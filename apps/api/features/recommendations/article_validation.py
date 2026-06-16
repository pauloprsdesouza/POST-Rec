"""LLM-assisted validation that retrieved papers match research topics."""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from apps.api.features.recommendations.llm import assign_paper_ids, gemini_service
from apps.api.features.retrieval.persistence import persist_article_validation_scores
from apps.api.features.retrieval.relevance import compute_relevance_score
from apps.api.shared.observability.logging import get_logger
from apps.api.shared.settings import get_settings
from packages.postrec_core.retrieval.context_alignment import compute_context_alignment

logger = get_logger("postrec-article-validation")


class ArticleValidationService:
    """Filter papers by topic/research-area relevance before idea generation."""

    def validate_and_filter(
        self,
        db: Session,
        run_id: str,
        papers: list[dict[str, Any]],
        *,
        research_area: str,
        seed_topics: list[str],
        avoided_topics: list[str] | None = None,
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        settings = get_settings()
        papers = assign_paper_ids(papers)
        min_valid_papers = settings.article_min_valid_papers
        if len(papers) <= settings.article_sparse_corpus_threshold:
            min_valid_papers = min(min_valid_papers, max(1, min(2, len(papers))))

        stats: dict[str, Any] = {
            "input": len(papers),
            "method": "deterministic",
            "kept": len(papers),
            "filtered_out": 0,
            "sufficient_evidence": True,
        }

        if not papers:
            stats["sufficient_evidence"] = False
            stats["insufficient_evidence_reason"] = "No papers retrieved."
            return [], stats

        if not settings.article_llm_validation_enabled or not settings.gemini_api_key:
            filtered, stats, scored = self._deterministic_filter(
                papers,
                research_area=research_area,
                seed_topics=seed_topics,
                avoided_topics=avoided_topics,
                min_score=settings.retrieval_min_relevance_score,
                min_valid=min_valid_papers,
            )
            filtered, stats = self._apply_best_effort(papers, filtered, stats, settings, min_valid_papers)
            self._persist_scores(db, scored, run_id=run_id, method=stats["method"])
            return filtered, stats

        llm_result = gemini_service.validate_retrieved_papers(
            db=db,
            run_id=run_id,
            papers=papers,
            research_area=research_area,
            seed_topics=seed_topics,
            avoided_topics=avoided_topics or [],
            min_score=settings.article_llm_min_relevance_score,
            min_valid_papers=min_valid_papers,
        )

        validated_papers = llm_result.get("papers") or papers
        validations = llm_result.get("validations") or []
        filtered = self._papers_passing_validation(validated_papers, settings.article_llm_min_relevance_score)

        if len(filtered) < min_valid_papers:
            logger.warning(
                "article_llm_validation_insufficient",
                run_id=run_id,
                passed=len(filtered),
                required=min_valid_papers,
            )
            filtered, det_stats, scored = self._deterministic_filter(
                papers,
                research_area=research_area,
                seed_topics=seed_topics,
                avoided_topics=avoided_topics,
                min_score=settings.retrieval_min_relevance_score,
                min_valid=min_valid_papers,
            )
            stats.update(det_stats)
            stats["method"] = "llm_then_deterministic_fallback"
            stats["llm_validations"] = len(validations)
            stats["scope_summary"] = llm_result.get("scope_summary")
            filtered, stats = self._apply_best_effort(scored, filtered, stats, settings, min_valid_papers)
            if not stats["sufficient_evidence"]:
                stats["insufficient_evidence_reason"] = llm_result.get("insufficient_evidence_reason") or det_stats.get(
                    "insufficient_evidence_reason"
                )
            self._persist_scores(db, scored, run_id=run_id, method=stats["method"])
            return filtered, stats

        stats.update(
            {
                "method": "llm",
                "kept": len(filtered),
                "filtered_out": len(papers) - len(filtered),
                "llm_validations": len(validations),
                "sufficient_evidence": len(filtered) >= min_valid_papers,
                "scope_summary": llm_result.get("scope_summary"),
                "insufficient_evidence_reason": None
                if len(filtered) >= min_valid_papers
                else llm_result.get("insufficient_evidence_reason"),
            }
        )
        filtered, stats = self._apply_best_effort(validated_papers, filtered, stats, settings, min_valid_papers)
        self._persist_scores(db, validated_papers, run_id=run_id, method=stats["method"])
        return filtered, stats

    @staticmethod
    def _papers_passing_validation(papers: list[dict[str, Any]], min_score: float) -> list[dict[str, Any]]:
        return [
            paper
            for paper in papers
            if paper.get("llm_passes_validation", paper.get("llm_relevance_score", 0) >= min_score)
        ]

    @staticmethod
    def _paper_validation_score(paper: dict[str, Any]) -> float:
        llm_score = paper.get("llm_relevance_score")
        if isinstance(llm_score, (int, float)):
            return float(llm_score)
        relevance = paper.get("relevance_score")
        if isinstance(relevance, (int, float)):
            return float(relevance)
        return 0.0

    def _apply_best_effort(
        self,
        scored_pool: list[dict[str, Any]],
        filtered: list[dict[str, Any]],
        stats: dict[str, Any],
        settings,
        min_valid: int | None = None,
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        required = min_valid if min_valid is not None else settings.article_min_valid_papers
        if len(filtered) >= required:
            stats["sufficient_evidence"] = True
            stats["insufficient_evidence_reason"] = None
            return filtered, stats

        if not settings.article_grounding_best_effort_enabled or not scored_pool:
            stats["sufficient_evidence"] = False
            return filtered, stats

        ranked = sorted(scored_pool, key=self._paper_validation_score, reverse=True)
        best_effort = ranked[: max(required, min(len(ranked), 3))]
        if not best_effort:
            stats["sufficient_evidence"] = False
            return filtered, stats

        stats["method"] = f"{stats.get('method', 'deterministic')}_best_effort"
        stats["kept"] = len(best_effort)
        stats["filtered_out"] = len(scored_pool) - len(best_effort)
        stats["sufficient_evidence"] = True
        stats["insufficient_evidence_reason"] = None
        stats["best_effort_grounding"] = True
        logger.warning(
            "article_validation_best_effort",
            kept=len(best_effort),
            required=required,
            top_score=round(self._paper_validation_score(best_effort[0]), 3),
        )
        return best_effort, stats

    def _deterministic_filter(
        self,
        papers: list[dict[str, Any]],
        *,
        research_area: str,
        seed_topics: list[str],
        avoided_topics: list[str] | None,
        min_score: float,
        min_valid: int,
    ) -> tuple[list[dict[str, Any]], dict[str, Any], list[dict[str, Any]]]:
        settings = get_settings()
        scored_all: list[dict[str, Any]] = []
        kept: list[dict[str, Any]] = []
        for paper in papers:
            score = compute_relevance_score(
                paper,
                topics=seed_topics,
                research_area=research_area,
                avoided_topics=avoided_topics,
            )
            passes = score >= min_score
            alignment = compute_context_alignment(
                paper,
                research_area=research_area,
                topics=seed_topics,
                avoided_topics=avoided_topics,
                pass_threshold=float(getattr(settings, "retrieval_min_domain_alignment", 0.40) or 0.40),
            )
            if settings.retrieval_domain_filter_enabled and research_area and not alignment.passes:
                passes = False
            enriched = {
                **paper,
                "relevance_score": round(score, 4),
                "llm_relevance_score": round(score, 4),
                "llm_passes_validation": passes,
                "domain_alignment_score": alignment.score,
                "domain_alignment_passes": alignment.passes,
            }
            scored_all.append(enriched)
            if passes:
                kept.append(enriched)

        sufficient = len(kept) >= min_valid
        stats = {
            "method": "deterministic",
            "input": len(papers),
            "kept": len(kept),
            "filtered_out": len(papers) - len(kept),
            "sufficient_evidence": sufficient,
            "insufficient_evidence_reason": None
            if sufficient
            else f"Only {len(kept)} papers meet relevance threshold (need {min_valid}).",
        }
        return kept, stats, scored_all

    @staticmethod
    def _persist_scores(
        db: Session,
        papers: list[dict[str, Any]],
        *,
        run_id: str,
        method: str,
    ) -> None:
        updated = persist_article_validation_scores(db, papers, run_id=run_id, method=method)
        if updated:
            logger.info("article_validation_scores_persisted", run_id=run_id, updated=updated, method=method)


article_validation_service = ArticleValidationService()
