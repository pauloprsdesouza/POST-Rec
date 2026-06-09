"""Recommendation run business logic."""

import uuid
from datetime import UTC, datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session

from apps.api.features.profile.service import profile_service
from apps.api.features.runs.cleanup import is_run_cancellable, is_run_retryable
from apps.api.features.runs.query import published_recommendation_counts
from apps.api.features.runs.stream_service import run_stream_service
from apps.api.shared.infra.cache import cache_service
from apps.api.shared.models import (
    LLMUsage,
    RecommendationCandidate,
    RecommendationFeedback,
    RecommendationRun,
    RecommendationRunEvent,
)
from apps.api.shared.observability.logging import get_logger
from packages.postrec_core.domain.enums import RunStatus
from packages.postrec_core.scoring.expectation_alignment import compute_final_ranking_score

logger = get_logger("postrec-run")

_SOTA_REC_FIELDS = (
    "sota_summary",
    "novelty_delta",
    "closest_prior_work",
    "sota_anchors",
    "differentiation_score_rationale",
    "facet_deltas",
    "aligned_gaps",
)


def _build_scores(rec: dict) -> tuple[dict, float]:
    scores = dict(rec.get("scores") or {})
    sota_blob = {key: rec[key] for key in _SOTA_REC_FIELDS if rec.get(key)}
    if sota_blob:
        scores["_sota"] = sota_blob

    final = rec.get("final_score")
    if final is None:
        final = scores.get("verified_final_score") or scores.get("final_score")
    if final is None:
        final = (
            compute_final_ranking_score({k: v / 100 for k, v in scores.items() if isinstance(v, (int, float))}) * 100
        )

    return scores, float(final)


class RunService:
    def create_run(
        self,
        db: Session,
        session_id: uuid.UUID,
        expectation_id: uuid.UUID | None,
        request_id: str | None,
        topics: list[str],
        mode: str,
        max_papers: int,
        max_recommendations: int,
        constraints: dict,
        user_id: uuid.UUID | None = None,
        *,
        experiment_id: str | None = None,
        experiment_variant: str | None = None,
        assigned_mode: str | None = None,
        presentation_profile: str = "standard",
    ) -> RecommendationRun:
        run = RecommendationRun(
            request_id=request_id or str(uuid.uuid4()),
            session_id=session_id,
            expectation_id=expectation_id,
            user_id=user_id,
            input={"topics": topics, "constraints": constraints},
            mode=mode,
            status=RunStatus.QUEUED,
            progress=2,
            max_papers=max_papers,
            max_recommendations=max_recommendations,
            experiment_id=experiment_id,
            experiment_variant=experiment_variant,
            assigned_mode=assigned_mode or mode,
            presentation_profile=presentation_profile,
        )
        db.add(run)
        db.flush()
        event_message = "Recommendation run created"
        if experiment_id:
            event_message = "Recommendation run created for blind evaluation"
        self._add_event(db, run, "run_created", event_message)
        db.commit()
        db.refresh(run)
        if user_id:
            cache_service.invalidate_user_runs(str(user_id))
        run_stream_service.publish(db, run)
        logger.info("run_created", run_id=str(run.id), session_id=str(session_id))
        return run

    def update_status(
        self,
        db: Session,
        run: RecommendationRun,
        status: RunStatus,
        progress: int,
        message: str,
    ) -> None:
        run.status = status
        run.progress = progress
        run.current_step = status
        if status in (RunStatus.COMPLETED, RunStatus.CANCELLED):
            run.error_message = None
        if status == RunStatus.STARTED and not run.started_at:
            run.started_at = datetime.now(UTC)
        if status in (RunStatus.COMPLETED, RunStatus.FAILED, RunStatus.CANCELLED):
            run.finished_at = datetime.now(UTC)
        self._add_event(db, run, status, message)
        db.commit()

        cache_service.invalidate_run(str(run.id))

        if run.user_id:
            cache_service.invalidate_user_runs(str(run.user_id))

        run_stream_service.publish(db, run)

        if status in (
            RunStatus.COMPLETED,
            RunStatus.FAILED,
            RunStatus.CANCELLED,
            RunStatus.COST_LIMIT_EXCEEDED,
            RunStatus.FAILED_SCHEMA_VALIDATION,
        ):
            cache_service.invalidate_validation_dashboard()

    def bump_progress(self, db: Session, run: RecommendationRun, progress: int) -> None:
        """Raise progress without changing status (e.g. long-running substeps)."""
        if progress <= run.progress:
            return
        run.progress = progress
        db.commit()

        cache_service.invalidate_run(str(run.id))

        if run.user_id:
            cache_service.invalidate_user_runs(str(run.user_id))

        run_stream_service.publish(db, run)

    def cancel_run(self, db: Session, run: RecommendationRun) -> None:
        if not is_run_cancellable(run.status):
            raise HTTPException(status_code=409, detail="Run cannot be cancelled in its current state")
        self.update_status(db, run, RunStatus.CANCELLED, run.progress, "Run cancelled by user")

    def retry_run(self, db: Session, run: RecommendationRun) -> None:
        if run.archived_at is not None:
            raise HTTPException(status_code=409, detail="Archived runs cannot be retried")
        published_count = published_recommendation_counts(db, [run.id]).get(run.id, 0)
        if not is_run_retryable(run.status, published_count):
            raise HTTPException(status_code=409, detail="Run cannot be retried in its current state")

        self._clear_run_artifacts(db, run.id)
        run.status = RunStatus.QUEUED
        run.progress = 2
        run.current_step = None
        run.error_message = None
        run.started_at = None
        run.finished_at = None
        self._add_event(db, run, "run_retried", "Recommendation run queued for retry")
        db.commit()
        db.refresh(run)
        self._invalidate_user_run_caches(run)
        run_stream_service.publish(db, run)

        from apps.api.workers.tasks import process_recommendation_run

        process_recommendation_run.delay(str(run.id))
        logger.info("run_retried", run_id=str(run.id))

    def archive_run(
        self,
        db: Session,
        run: RecommendationRun,
        *,
        user_id: uuid.UUID,
        remove_learned_topics: list[str] | None = None,
    ) -> None:
        if run.archived_at is not None:
            return
        if is_run_cancellable(run.status):
            raise HTTPException(status_code=409, detail="Cancel the run before archiving it")

        if remove_learned_topics:
            profile_service.remove_learned_topics(db, user_id, remove_learned_topics)
            cache_service.invalidate_user_profile(str(user_id))

        run.archived_at = datetime.now(UTC)
        self._add_event(db, run, "run_archived", "Run archived by user")
        db.commit()
        db.refresh(run)
        self._invalidate_user_run_caches(run)
        run_stream_service.publish(db, run)
        logger.info("run_archived", run_id=str(run.id))

    def remove_run(
        self,
        db: Session,
        run: RecommendationRun,
        *,
        user_id: uuid.UUID,
        remove_learned_topics: list[str] | None = None,
    ) -> None:
        if is_run_cancellable(run.status):
            raise HTTPException(status_code=409, detail="Cancel the run before removing it")

        if remove_learned_topics:
            profile_service.remove_learned_topics(db, user_id, remove_learned_topics)
            cache_service.invalidate_user_profile(str(user_id))

        run_id = str(run.id)
        owner_id = str(run.user_id) if run.user_id else None
        self._clear_run_artifacts(db, run.id)
        db.delete(run)
        db.commit()
        cache_service.invalidate_run(run_id)
        if owner_id:
            cache_service.invalidate_user_runs(owner_id)
        logger.info("run_removed", run_id=run_id)

    def _clear_run_artifacts(self, db: Session, run_id: uuid.UUID) -> None:
        db.query(RecommendationFeedback).filter_by(run_id=run_id).delete(synchronize_session=False)
        db.query(RecommendationCandidate).filter_by(run_id=run_id).delete(synchronize_session=False)
        db.query(RecommendationRunEvent).filter_by(run_id=run_id).delete(synchronize_session=False)
        db.query(LLMUsage).filter_by(run_id=run_id).delete(synchronize_session=False)
        db.flush()

    def _invalidate_user_run_caches(self, run: RecommendationRun) -> None:
        cache_service.invalidate_run(str(run.id))
        if run.user_id:
            cache_service.invalidate_user_runs(str(run.user_id))

    def save_recommendations(
        self, db: Session, run: RecommendationRun, recommendations: list[dict]
    ) -> list[RecommendationCandidate]:
        candidates = []
        for rec in recommendations:
            scores, final = _build_scores(rec)
            status = rec.get("_publication_status") or rec.get("status") or "published"
            if rec.get("_rejected_by_critic"):
                status = "needs_refinement"

            candidate = RecommendationCandidate(
                run_id=run.id,
                title=rec["title"],
                technique_name=rec.get("technique_name"),
                research_gap=rec.get("research_gap"),
                research_question=rec.get("research_question"),
                hypothesis=rec.get("hypothesis"),
                proposed_method=rec.get("proposed_method"),
                related_work_summary=rec.get("related_work_summary"),
                evidence_papers=rec.get("evidence_papers"),
                datasets=rec.get("datasets"),
                evaluation_metrics=rec.get("evaluation_metrics"),
                experimental_plan=rec.get("experimental_plan"),
                risks=rec.get("risks"),
                expected_contribution=rec.get("expected_contribution"),
                confidence_level=rec.get("confidence_level"),
                scores=scores,
                final_score=final,
                status=status,
            )
            db.add(candidate)
            candidates.append(candidate)
        db.commit()
        return candidates

    def _add_event(
        self,
        db: Session,
        run: RecommendationRun,
        event_type: str,
        message: str,
        payload: dict | None = None,
    ) -> None:
        event = RecommendationRunEvent(
            run_id=run.id,
            event_type=event_type,
            message=message,
            payload=payload,
        )
        db.add(event)


run_service = RunService()
