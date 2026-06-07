"""Novelty verification and critic orchestration."""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from apps.api.services.facet_verification_service import facet_verification_service
from apps.api.services.llm_service import gemini_service
from apps.api.settings import get_settings
from packages.postrec_core.domain.run_mode import RunMode
from packages.postrec_core.scoring.novelty_verification import (
    blend_novelty_verified,
    claim_overlap_novelty,
    compute_sota_fit,
    embedding_novelty,
    proposal_text,
)
from packages.postrec_core.scoring.recency_gap import compute_recency_gap
from packages.postrec_core.scoring.verified_ranking import compute_verified_final_score
from packages.postrec_core.validation.recommendation_validator import validate_recommendation


class NoveltyVerificationService:
    """Apply deterministic novelty checks and optional LLM critic."""

    def __init__(self) -> None:
        self._settings = get_settings()

    def verify_recommendation(
        self,
        db: Session,
        run_id: str,
        recommendation: dict[str, Any],
        papers: list[dict[str, Any]],
        paper_embeddings: list[list[float]],
        *,
        mode: RunMode,
        sota_landscape: dict[str, Any] | None = None,
        gap_matrix: dict[str, Any] | None = None,
        facet_map=None,
    ) -> dict[str, Any]:
        text = proposal_text(recommendation)
        corpus = [f"{p.get('title', '')}. {p.get('abstract', '')}" for p in papers]

        proposal_embedding = gemini_service.generate_embeddings(db, run_id, [text])[0]
        embed_novelty = embedding_novelty(proposal_embedding, paper_embeddings)
        max_sim = max(0.0, 1.0 - embed_novelty)
        claim_novelty = claim_overlap_novelty(text, corpus)
        recency_gap = compute_recency_gap(recommendation, papers)
        llm_novelty = (recommendation.get("scores") or {}).get("novelty")
        llm_novelty_val = float(llm_novelty) if isinstance(llm_novelty, (int, float)) else None

        novelty_verified = blend_novelty_verified(
            embed_novelty,
            claim_novelty,
            llm_novelty_val,
            llm_blend=self._settings.novelty_llm_blend,
        )
        novelty_verified = max(0.0, min(1.0, 0.85 * novelty_verified + 0.15 * recency_gap))
        sota_fit = compute_sota_fit(recommendation, papers)

        scores = dict(recommendation.get("scores") or {})
        scores["sota_fit"] = round(sota_fit * 100, 2)
        scores["novelty_verified"] = round(novelty_verified * 100, 2)
        scores["recency_gap"] = round(recency_gap * 100, 2)
        scores["embedding_distance"] = round(max_sim * 100, 2)
        scores["llm_novelty"] = llm_novelty_val

        validation = validate_recommendation(
            recommendation,
            papers,
            mode=mode,
            require_sota_fields=mode != RunMode.QUICK or self._settings.require_sota_fields_quick,
        )
        if validation.issues:
            scores["_validation_issues"] = validation.issues
        recommendation["_publication_status"] = validation.publication_status

        critic = {"accept": True, "issues": []}
        if self._settings.critic_enabled and (mode.uses_full_sota_pipeline or mode == RunMode.QUICK):
            critic = gemini_service.critic_recommendation(
                db=db,
                run_id=run_id,
                proposal=recommendation,
                papers=papers,
                sota_landscape=sota_landscape or {},
            )
            scores["critic_accepted"] = bool(critic.get("accept", False))
            if critic.get("issues"):
                scores["_critic_issues"] = critic.get("issues")

            revised = critic.get("revised_scores") or {}
            for key, value in revised.items():
                if isinstance(value, (int, float)):
                    scores[key] = value

        verified_final = compute_verified_final_score(
            scores,
            sota_fit=sota_fit,
            novelty_verified=novelty_verified,
            mode=mode,
        )
        scores["verified_final_score"] = verified_final
        scores["final_score"] = verified_final

        recommendation["scores"] = scores
        recommendation["final_score"] = verified_final

        if mode.strict_critic and not critic.get("accept", True):
            recommendation["_rejected_by_critic"] = True
            recommendation["_publication_status"] = "needs_refinement"

        if embed_novelty < self._settings.novelty_min_embedding_distance and mode == RunMode.SOTA:
            recommendation["_rejected_by_critic"] = True
            recommendation["_publication_status"] = "needs_refinement"
            issues = scores.get("_critic_issues")
            if not isinstance(issues, list):
                issues = []
            issues.append("Too similar to a single source paper.")
            scores["_critic_issues"] = issues

        if self._settings.critic_reject_on_failure and not critic.get("accept", True):
            recommendation["_publication_status"] = "needs_refinement"

        if validation.publication_status == "needs_refinement":
            recommendation["_publication_status"] = "needs_refinement"

        if mode.uses_fggv_verification:
            recommendation = facet_verification_service.verify_fggv(
                db,
                run_id,
                recommendation,
                papers,
                facet_map=facet_map,
                gap_matrix=gap_matrix,
                verified_final_score=verified_final,
                document_novelty_verified=novelty_verified,
            )

        return recommendation

    def filter_publishable(
        self,
        recommendations: list[dict[str, Any]],
        *,
        mode: RunMode,
    ) -> list[dict[str, Any]]:
        """Return all recommendations with publication status set (no silent drop)."""
        return recommendations


novelty_verification_service = NoveltyVerificationService()
