"""FGGV facet verification orchestration."""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from apps.api.services.llm_service import gemini_service
from apps.api.settings import get_settings
from packages.postrec_core.facets.facet_map import LiteratureFacetMap, build_literature_facet_map
from packages.postrec_core.facets.gap_facet_alignment import compute_gap_facet_alignment
from packages.postrec_core.facets.taxonomy import FacetType
from packages.postrec_core.scoring.facet_grounded_ranking import (
    FggvAblation,
    compute_facet_novelty_index,
    compute_fggv_score,
    count_false_novel_facets,
)


class FacetVerificationService:
    """Apply Facet-Grounded Gap Verification (FGGV v2) to a recommendation."""

    def __init__(self) -> None:
        self._settings = get_settings()

    def build_facet_map(self, papers: list[dict[str, Any]]) -> LiteratureFacetMap:
        return build_literature_facet_map(papers)

    def _embed_facets(
        self,
        db: Session,
        run_id: str,
        recommendation: dict[str, Any],
        lfm: LiteratureFacetMap,
    ) -> tuple[dict[str, list[float]], dict[str, list[list[float]]]]:
        from packages.postrec_core.facets.extraction import extract_proposal_facets

        facet_embeddings: dict[str, list[float]] = {}
        corpus_facet_embeddings: dict[str, list[list[float]]] = {}
        proposal_facets = extract_proposal_facets(recommendation)
        texts_to_embed: list[str] = []
        text_keys: list[tuple[str, str]] = []

        for facet in FacetType.all_ordered():
            prop_text = proposal_facets.get(facet.value, "").strip()
            if prop_text:
                texts_to_embed.append(prop_text)
                text_keys.append(("proposal", facet.value))
            for idx, corpus_text in enumerate(lfm.corpus_texts_for(facet)):
                if corpus_text.strip():
                    texts_to_embed.append(corpus_text)
                    text_keys.append(("corpus", f"{facet.value}:{idx}"))

        if not texts_to_embed:
            return facet_embeddings, corpus_facet_embeddings

        embeddings = gemini_service.generate_embeddings(db, run_id, texts_to_embed)
        for (kind, key), emb in zip(text_keys, embeddings, strict=False):
            if kind == "proposal":
                facet_embeddings[key] = emb
            else:
                facet_key = key.split(":", 1)[0]
                corpus_facet_embeddings.setdefault(facet_key, []).append(emb)
        return facet_embeddings, corpus_facet_embeddings

    def _llm_per_facet_scores(self, critic: dict[str, Any]) -> dict[str, float]:
        per_facet = critic.get("per_facet") or {}
        scores: dict[str, float] = {}
        if not isinstance(per_facet, dict):
            return scores
        for facet in FacetType.all_ordered():
            entry = per_facet.get(facet.value)
            if isinstance(entry, dict) and isinstance(entry.get("novelty_0_100"), (int, float)):
                scores[facet.value] = float(entry["novelty_0_100"])
        return scores

    def verify_fggv(
        self,
        db: Session,
        run_id: str,
        recommendation: dict[str, Any],
        papers: list[dict[str, Any]],
        *,
        facet_map: LiteratureFacetMap | None = None,
        gap_matrix: dict[str, Any] | None = None,
        verified_final_score: float,
        document_novelty_verified: float,
    ) -> dict[str, Any]:
        lfm = facet_map or build_literature_facet_map(papers)
        facet_embeddings: dict[str, list[float]] = {}
        corpus_facet_embeddings: dict[str, list[list[float]]] = {}

        try:
            facet_embeddings, corpus_facet_embeddings = self._embed_facets(db, run_id, recommendation, lfm)
        except Exception:
            pass

        fni, per_facet, diagnostics = compute_facet_novelty_index(
            recommendation,
            lfm,
            facet_embeddings=facet_embeddings or None,
            corpus_facet_embeddings=corpus_facet_embeddings or None,
            use_saturation_weights=self._settings.fggv_saturation_aware,
        )

        critic_payload: dict[str, Any] = {}
        if self._settings.fggv_facet_critic_enabled:
            critic_payload = gemini_service.facet_critic(
                db=db,
                run_id=run_id,
                proposal=recommendation,
                papers=papers,
                closest_matches=diagnostics.get("closest_facet_matches") or {},
            )
            llm_scores = self._llm_per_facet_scores(critic_payload)
            if llm_scores:
                fni, per_facet, diagnostics = compute_facet_novelty_index(
                    recommendation,
                    lfm,
                    facet_embeddings=facet_embeddings or None,
                    corpus_facet_embeddings=corpus_facet_embeddings or None,
                    llm_per_facet_scores=llm_scores,
                    llm_blend=self._settings.fggv_llm_facet_blend,
                    use_saturation_weights=self._settings.fggv_saturation_aware,
                )

        gas = compute_gap_facet_alignment(recommendation, gap_matrix)
        fggv_score = compute_fggv_score(
            verified_final_score=verified_final_score,
            facet_novelty_index=fni,
            gap_alignment_score=gas,
            document_novelty_verified=document_novelty_verified,
            ablation=FggvAblation.FULL,
        )

        false_novel_count = count_false_novel_facets(
            per_facet,
            min_novelty=self._settings.fggv_min_per_facet_novelty,
        )

        scores = dict(recommendation.get("scores") or {})
        scores["facet_novelty_index"] = round(fni * 100, 2)
        scores["gap_alignment_score"] = round(gas * 100, 2)
        scores["fggv_score"] = fggv_score
        scores["verified_final_score"] = fggv_score
        scores["final_score"] = fggv_score
        scores["false_novel_facet_count"] = false_novel_count
        scores["_fggv"] = {
            "method": "fggv_v2",
            "per_facet_novelty": {k: round(v * 100, 2) for k, v in per_facet.items()},
            "facet_saturation": lfm.saturation,
            "closest_facet_matches": diagnostics.get("closest_facet_matches"),
            "facet_weights": diagnostics.get("facet_weights"),
            "low_novelty_facets": diagnostics.get("low_novelty_facets"),
            "facet_critic": critic_payload if critic_payload else None,
            "false_novel_risk": critic_payload.get("false_novel_risk") if critic_payload else None,
        }

        recommendation["scores"] = scores
        recommendation["final_score"] = fggv_score

        if fni < self._settings.fggv_min_facet_novelty_index:
            recommendation["_publication_status"] = "needs_refinement"
            self._append_issue(scores, "Low facet-level novelty vs literature map.")

        if false_novel_count >= self._settings.fggv_false_novel_facet_threshold:
            recommendation["_publication_status"] = "needs_refinement"
            self._append_issue(
                scores,
                f"False-novel risk: {false_novel_count} facet(s) overlap heavily with corpus.",
            )

        if gas < 0.25:
            recommendation["_publication_status"] = "needs_refinement"
            self._append_issue(scores, "Weak alignment between facet deltas and gap matrix.")

        if critic_payload.get("false_novel_risk") == "high":
            recommendation["_publication_status"] = "needs_refinement"
            self._append_issue(scores, "Facet critic flagged high false-novel risk.")

        return recommendation

    @staticmethod
    def _append_issue(scores: dict[str, Any], message: str) -> None:
        issues = scores.get("_critic_issues")
        if not isinstance(issues, list):
            issues = []
        if message not in issues:
            issues.append(message)
        scores["_critic_issues"] = issues


facet_verification_service = FacetVerificationService()
