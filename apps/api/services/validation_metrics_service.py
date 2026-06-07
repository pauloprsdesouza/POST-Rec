"""Validation metrics aggregation."""

from sqlalchemy import func
from sqlalchemy.orm import Session

from apps.api.models import RecommendationFeedback, RecommendationRun
from apps.api.services.cache_service import CacheKeys, CacheTTL, cache_service
from apps.api.services.sota_metrics_service import compute_sota_quality_metrics
from packages.postrec_core.domain.enums import RunStatus


class ValidationMetricsService:
    def get_dashboard(self, db: Session) -> dict:
        key = CacheKeys.validation_dashboard()

        def load() -> dict:
            return self._compute_dashboard(db)

        return cache_service.get_or_load(key, CacheTTL.VALIDATION_DASHBOARD, load)

    def _compute_dashboard(self, db: Session) -> dict:
        feedbacks = db.query(RecommendationFeedback).all()
        runs = db.query(RecommendationRun).all()

        total_runs = len(runs)
        completed = sum(1 for r in runs if r.status == RunStatus.COMPLETED)
        failed = sum(1 for r in runs if r.status in (RunStatus.FAILED, RunStatus.FAILED_SCHEMA_VALIDATION))

        if not feedbacks:
            sota_metrics = compute_sota_quality_metrics(db)
            return {
                "average_eas": 0.0,
                "approval_rate": 0.0,
                "would_use_rate": 0.0,
                "average_trust_score": 0.0,
                "average_feasibility_score": 0.0,
                "average_usefulness_score": 0.0,
                "run_completion_rate": completed / total_runs if total_runs else 0.0,
                "run_failure_rate": failed / total_runs if total_runs else 0.0,
                "total_runs": total_runs,
                "total_feedback": 0,
                "rejection_reasons": [],
                **sota_metrics,
            }

        eas_values = [
            float(f.expectation_alignment_score) for f in feedbacks if f.expectation_alignment_score is not None
        ]
        approved = sum(1 for f in feedbacks if f.decision == "approved")
        would_use = sum(1 for f in feedbacks if f.would_use_in_real_paper == "yes")

        sota_metrics = compute_sota_quality_metrics(db)
        return {
            "average_eas": sum(eas_values) / len(eas_values) if eas_values else 0.0,
            "approval_rate": approved / len(feedbacks),
            "would_use_rate": would_use / len(feedbacks),
            "average_trust_score": db.query(func.avg(RecommendationFeedback.trust_score)).scalar() or 0.0,
            "average_feasibility_score": db.query(func.avg(RecommendationFeedback.feasibility_score)).scalar() or 0.0,
            "average_usefulness_score": db.query(func.avg(RecommendationFeedback.usefulness_score)).scalar() or 0.0,
            "run_completion_rate": completed / total_runs if total_runs else 0.0,
            "run_failure_rate": failed / total_runs if total_runs else 0.0,
            "total_runs": total_runs,
            "total_feedback": len(feedbacks),
            "rejection_reasons": [f.comment for f in feedbacks if f.decision == "rejected" and f.comment],
            **sota_metrics,
        }


validation_metrics_service = ValidationMetricsService()
