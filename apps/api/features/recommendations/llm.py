"""Google Gemini LLM and embedding service."""

import json
import re
import uuid
from typing import Any

from google import genai
from google.genai import types
from sqlalchemy.orm import Session

from apps.api.shared.models import LLMUsage
from apps.api.shared.observability.logging import get_logger
from apps.api.shared.infra.embedding_config import resolve_embedding_model
from apps.api.features.runs.cost import add_usage_cost
from apps.api.shared.settings import get_settings
from packages.postrec_core.domain.expectation_context import format_user_expectations
from packages.postrec_core.prompts.facet_critic import FACET_CRITIC_USER_TEMPLATE
from packages.postrec_core.prompts.facet_pipeline import FGGV_PROPOSAL_USER_TEMPLATE
from packages.postrec_core.prompts.recommendation_prompt import (
    RECOMMENDATION_SYSTEM_PROMPT,
    RECOMMENDATION_USER_TEMPLATE,
)
from packages.postrec_core.prompts.sota_pipeline import (
    SOTA_CRITIC_USER_TEMPLATE,
    SOTA_GAP_MATRIX_USER_TEMPLATE,
    SOTA_LANDSCAPE_USER_TEMPLATE,
    SOTA_PROPOSAL_USER_TEMPLATE,
    SOTA_SYSTEM_PROMPT,
)

logger = get_logger("postrec-llm")

# Approximate Gemini pricing (USD per 1M tokens) for cost tracking
GEMINI_PRICING = {
    "gemini-2.0-flash": {"input": 0.10, "output": 0.40},
    "gemini-2.5-flash-lite": {"input": 0.075, "output": 0.30},
}
DEFAULT_EMBEDDING_PRICING = {"input": 0.01, "output": 0.0}


def _constraint_prompt_fields(constraints: dict) -> dict[str, str]:
    return {
        "constraints": json.dumps(constraints),
        "user_expectations": format_user_expectations(constraints),
    }


class GeminiService:
    def __init__(self) -> None:
        self._client: genai.Client | None = None

    @property
    def settings(self):
        return get_settings()

    @property
    def client(self) -> genai.Client:
        if self._client is None:
            self._client = genai.Client(api_key=self.settings.gemini_api_key)
        return self._client

    def _embedding_model(self) -> str:
        return resolve_embedding_model(self.settings.gemini_embedding_model)

    def _estimate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        if model == self._embedding_model():
            pricing = DEFAULT_EMBEDDING_PRICING
        else:
            pricing = GEMINI_PRICING.get(model, {"input": 0.10, "output": 0.40})
        return (input_tokens * pricing["input"] + output_tokens * pricing["output"]) / 1_000_000

    def _record_usage(
        self,
        db: Session,
        run_id: str,
        operation: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
    ) -> float:
        cost = self._estimate_cost(model, input_tokens, output_tokens)
        run_uuid = uuid.UUID(str(run_id))
        usage = LLMUsage(
            run_id=run_uuid,
            provider="google_gemini",
            model=model,
            operation=operation,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
            estimated_cost_usd=cost,
        )
        db.add(usage)
        add_usage_cost(db, run_uuid, cost)
        return cost

    def generate_embeddings(self, db: Session, run_id: str, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        settings = self.settings
        if not settings.gemini_api_key:
            logger.warning("embedding_fallback", reason="gemini_api_key_missing")
            return [[0.0] * settings.gemini_embedding_dimensions for _ in texts]

        model = self._embedding_model()
        embeddings: list[list[float]] = []
        total_input = 0
        batch_size = 32

        for start in range(0, len(texts), batch_size):
            batch = texts[start : start + batch_size]
            result = self.client.models.embed_content(
                model=model,
                contents=batch,
                config=types.EmbedContentConfig(output_dimensionality=settings.gemini_embedding_dimensions),
            )
            for item in result.embeddings:
                embeddings.append(list(item.values))
            total_input += sum(max(1, len(text) // 4) for text in batch)

        self._record_usage(db, run_id, "embedding", model, total_input, 0)
        return embeddings

    @staticmethod
    def _papers_context(papers: list[dict], limit: int = 30) -> str:
        return "\n".join(
            f"- {p.get('title', 'Unknown')} ({p.get('year', 'N/A')}) "
            f"tier={p.get('tier', 'unknown')} DOI: {p.get('doi', 'N/A')}"
            for p in papers[:limit]
        )

    def _generate_json(
        self,
        db: Session,
        run_id: str,
        *,
        operation: str,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.5,
    ) -> dict[str, Any]:
        if not self.settings.gemini_api_key:
            logger.warning("generation_fallback", reason="gemini_api_key_missing", operation=operation)
            return {}

        model = self.settings.gemini_generation_model
        response = self.client.models.generate_content(
            model=model,
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                response_mime_type="application/json",
                temperature=temperature,
            ),
        )
        input_tokens = response.usage_metadata.prompt_token_count if response.usage_metadata else 0
        output_tokens = response.usage_metadata.candidates_token_count if response.usage_metadata else 0
        self._record_usage(db, run_id, operation, model, input_tokens, output_tokens)
        return self._parse_json(response.text or "{}")

    def generate_recommendations(
        self,
        db: Session,
        run_id: str,
        research_area: str,
        seed_topics: list[str],
        expected_output: str,
        desired_depth: str,
        constraints: dict,
        papers: list[dict],
        max_recommendations: int,
        enhanced_sota_fields: bool = True,
    ) -> dict[str, Any]:
        _ = enhanced_sota_fields  # call-site compatibility; SOTA fields always enabled
        papers_context = self._papers_context(papers)
        template = RECOMMENDATION_USER_TEMPLATE
        user_prompt = template.format(
            research_area=research_area or "General",
            seed_topics=", ".join(seed_topics),
            expected_output=expected_output or "Research ideas",
            desired_depth=desired_depth or "medium",
            **_constraint_prompt_fields(constraints),
            papers_context=papers_context or "No papers retrieved.",
            max_recommendations=max_recommendations,
        )

        if not self.settings.gemini_api_key:
            logger.warning("generation_fallback", reason="gemini_api_key_missing")
            return self._fallback_recommendations(seed_topics, papers, max_recommendations)

        return self._generate_json(
            db,
            run_id,
            operation="generation",
            system_prompt=RECOMMENDATION_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            temperature=0.7,
        )

    def generate_sota_landscape(
        self,
        db: Session,
        run_id: str,
        *,
        research_area: str,
        seed_topics: list[str],
        expected_output: str,
        papers: list[dict],
    ) -> dict[str, Any]:
        if not self.settings.gemini_api_key:
            return self._fallback_landscape(papers)
        prompt = SOTA_LANDSCAPE_USER_TEMPLATE.format(
            research_area=research_area or "General",
            seed_topics=", ".join(seed_topics),
            expected_output=expected_output or "Research ideas",
            papers_context=self._papers_context(papers),
        )
        return self._generate_json(
            db,
            run_id,
            operation="sota_landscape",
            system_prompt=SOTA_SYSTEM_PROMPT,
            user_prompt=prompt,
            temperature=0.3,
        )

    def generate_gap_matrix(
        self,
        db: Session,
        run_id: str,
        *,
        research_area: str,
        seed_topics: list[str],
        papers: list[dict],
        sota_landscape: dict[str, Any],
    ) -> dict[str, Any]:
        if not self.settings.gemini_api_key:
            return {
                "gaps": [
                    {
                        "gap": "Under-explored combinations of recent methods",
                        "supporting_limitations": [],
                        "suggested_direction": "Benchmark and extend recent approaches",
                    }
                ]
            }
        prompt = SOTA_GAP_MATRIX_USER_TEMPLATE.format(
            research_area=research_area or "General",
            seed_topics=", ".join(seed_topics),
            sota_landscape_json=json.dumps(sota_landscape, default=str),
            papers_context=self._papers_context(papers),
        )
        return self._generate_json(
            db,
            run_id,
            operation="gap_matrix",
            system_prompt=SOTA_SYSTEM_PROMPT,
            user_prompt=prompt,
            temperature=0.4,
        )

    def generate_sota_proposals(
        self,
        db: Session,
        run_id: str,
        *,
        research_area: str,
        seed_topics: list[str],
        expected_output: str,
        desired_depth: str,
        constraints: dict,
        papers: list[dict],
        sota_landscape: dict[str, Any],
        gap_matrix: dict[str, Any],
        max_recommendations: int,
    ) -> dict[str, Any]:
        if not self.settings.gemini_api_key:
            return self._fallback_recommendations(seed_topics, papers, max_recommendations)
        prompt = SOTA_PROPOSAL_USER_TEMPLATE.format(
            research_area=research_area or "General",
            seed_topics=", ".join(seed_topics),
            expected_output=expected_output or "Research ideas",
            desired_depth=desired_depth or "medium",
            **_constraint_prompt_fields(constraints),
            sota_landscape_json=json.dumps(sota_landscape, default=str),
            gap_matrix_json=json.dumps(gap_matrix, default=str),
            papers_context=self._papers_context(papers),
            max_recommendations=max_recommendations,
        )
        return self._generate_json(
            db,
            run_id,
            operation="sota_generation",
            system_prompt=SOTA_SYSTEM_PROMPT,
            user_prompt=prompt,
            temperature=0.65,
        )

    def generate_fggv_proposals(
        self,
        db: Session,
        run_id: str,
        *,
        research_area: str,
        seed_topics: list[str],
        expected_output: str,
        desired_depth: str,
        constraints: dict,
        papers: list[dict],
        sota_landscape: dict[str, Any],
        gap_matrix: dict[str, Any],
        facet_saturation: dict[str, float],
        underserved_facets: list[str],
        max_recommendations: int,
    ) -> dict[str, Any]:
        if not self.settings.gemini_api_key:
            return self._fallback_recommendations(seed_topics, papers, max_recommendations)
        prompt = FGGV_PROPOSAL_USER_TEMPLATE.format(
            research_area=research_area or "General",
            seed_topics=", ".join(seed_topics),
            expected_output=expected_output or "Research ideas",
            desired_depth=desired_depth or "medium",
            **_constraint_prompt_fields(constraints),
            sota_landscape_json=json.dumps(sota_landscape, default=str),
            gap_matrix_json=json.dumps(gap_matrix, default=str),
            facet_saturation_json=json.dumps(facet_saturation, default=str),
            underserved_facets_json=json.dumps(underserved_facets, default=str),
            papers_context=self._papers_context(papers),
            max_recommendations=max_recommendations,
        )
        return self._generate_json(
            db,
            run_id,
            operation="fggv_generation",
            system_prompt=SOTA_SYSTEM_PROMPT,
            user_prompt=prompt,
            temperature=0.65,
        )

    def facet_critic(
        self,
        db: Session,
        run_id: str,
        *,
        proposal: dict[str, Any],
        papers: list[dict],
        closest_matches: dict[str, Any],
    ) -> dict[str, Any]:
        if not self.settings.gemini_api_key:
            return {"per_facet": {}, "false_novel_risk": "low", "overall_novelty_0_100": 70}
        from packages.postrec_core.facets.extraction import extract_proposal_facets

        prompt = FACET_CRITIC_USER_TEMPLATE.format(
            papers_context=self._papers_context(papers),
            facet_deltas_json=json.dumps(extract_proposal_facets(proposal), default=str),
            closest_matches_json=json.dumps(closest_matches, default=str),
        )
        result = self._generate_json(
            db,
            run_id,
            operation="facet_critic",
            system_prompt=SOTA_SYSTEM_PROMPT,
            user_prompt=prompt,
            temperature=0.2,
        )
        if not isinstance(result, dict):
            return {"per_facet": {}, "false_novel_risk": "low", "overall_novelty_0_100": 70}
        result.setdefault("per_facet", {})
        result.setdefault("false_novel_risk", "low")
        result.setdefault("overall_novelty_0_100", 70)
        return result

    def critic_recommendation(
        self,
        db: Session,
        run_id: str,
        *,
        proposal: dict[str, Any],
        papers: list[dict],
        sota_landscape: dict[str, Any],
    ) -> dict[str, Any]:
        if not self.settings.gemini_api_key:
            return {"accept": True, "issues": [], "revised_scores": {}}
        prompt = SOTA_CRITIC_USER_TEMPLATE.format(
            sota_landscape_json=json.dumps(sota_landscape, default=str),
            papers_context=self._papers_context(papers),
            proposal_json=json.dumps(proposal, default=str),
        )
        result = self._generate_json(
            db,
            run_id,
            operation="critic",
            system_prompt=SOTA_SYSTEM_PROMPT,
            user_prompt=prompt,
            temperature=0.2,
        )
        if not isinstance(result, dict):
            return {"accept": True, "issues": [], "revised_scores": {}}
        result.setdefault("accept", True)
        result.setdefault("issues", [])
        result.setdefault("revised_scores", {})
        return result

    def _fallback_landscape(self, papers: list[dict]) -> dict[str, Any]:
        titles = [p.get("title") for p in papers[:5] if p.get("title")]
        return {
            "methods": ["Literature-driven analysis"],
            "datasets": ["Public benchmarks"],
            "metrics": ["Standard task metrics"],
            "open_problems": ["Limited unified evaluation across recent papers"],
            "recent_strategies": titles[:3],
        }

    def _parse_json(self, raw: str) -> dict[str, Any]:
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", raw, re.DOTALL)
            if match:
                return json.loads(match.group())
            raise

    def _fallback_recommendations(self, seed_topics: list[str], papers: list[dict], max_recs: int) -> dict[str, Any]:
        """Deterministic fallback when Gemini is unavailable (dev/demo)."""
        recs = []
        for i, topic in enumerate(seed_topics[:max_recs]):
            evidence = papers[i : i + 2] if papers else []
            recs.append(
                {
                    "title": f"Investigating {topic}: A Systematic Approach",
                    "technique_name": "Literature-driven gap analysis",
                    "research_gap": f"Limited systematic studies on {topic} with reproducible benchmarks.",
                    "research_question": f"How can {topic} be evaluated using public datasets?",
                    "hypothesis": f"Applying structured evaluation to {topic} will reveal actionable gaps.",
                    "proposed_method": "Systematic literature review + benchmark experiments on public datasets.",
                    "related_work_summary": f"Existing work on {topic} lacks unified evaluation frameworks.",
                    "evidence_papers": [
                        {
                            "title": p.get("title", "Unknown"),
                            "year": p.get("year"),
                            "doi": p.get("doi"),
                            "url": p.get("url"),
                            "why_relevant": "Retrieved as relevant evidence.",
                        }
                        for p in evidence
                    ],
                    "datasets": ["Public benchmark datasets"],
                    "evaluation_metrics": ["Precision@K", "NDCG", "Reproducibility score"],
                    "experimental_plan": "1. Collect papers 2. Define tasks 3. Run benchmarks 4. Analyze gaps",
                    "risks": ["Dataset bias", "Limited generalizability"],
                    "expected_contribution": f"Novel evaluation framework for {topic}",
                    "confidence_level": "medium",
                    "scores": {
                        "relevance": 75,
                        "novelty": 60,
                        "evidence": 70,
                        "feasibility": 80,
                        "trend": 85,
                        "publication_potential": 70,
                        "strategic_fit": 75,
                        "final_score": 73,
                    },
                }
            )
        return {"recommendations": recs}


gemini_service = GeminiService()
