"""Validation metrics aggregation."""

from sqlalchemy import case, func
from sqlalchemy.orm import Session

from apps.api.features.experiments.service import experiment_service
from apps.api.features.validation.analysis_service import analysis_data_service
from apps.api.features.validation.metrics import compute_sota_quality_metrics
from apps.api.shared.infra.cache import CacheKeys, CacheTTL, cache_service
from apps.api.shared.models import RecommendationFeedback, RecommendationRun, SessionFinalSurvey
from packages.postrec_core.domain.enums import RunStatus
from packages.postrec_core.evaluation.human_metrics import all_dimension_statistics, mean_field, rate


class ValidationMetricsService:
    def get_dashboard(self, db: Session) -> dict:
        key = CacheKeys.validation_dashboard()

        def load() -> dict:
            return self._compute_dashboard(db)

        return cache_service.get_or_load(key, CacheTTL.VALIDATION_DASHBOARD, load)

    def get_research_report(self, db: Session) -> dict:
        key = CacheKeys.research_report()

        def load() -> dict:
            return analysis_data_service.build_report(db)

        return cache_service.get_or_load(key, CacheTTL.RESEARCH_REPORT, load)

    def _compute_dashboard(self, db: Session) -> dict:
        run_stats = db.query(
            func.count(RecommendationRun.id).label("total"),
            func.sum(case((RecommendationRun.status == RunStatus.COMPLETED, 1), else_=0)).label("completed"),
            func.sum(
                case(
                    (
                        RecommendationRun.status.in_((RunStatus.FAILED, RunStatus.FAILED_SCHEMA_VALIDATION)),
                        1,
                    ),
                    else_=0,
                )
            ).label("failed"),
        ).one()

        total_runs = int(run_stats.total or 0)
        completed = int(run_stats.completed or 0)
        failed = int(run_stats.failed or 0)

        feedback_stats = db.query(
            func.count(RecommendationFeedback.id).label("total"),
            func.avg(RecommendationFeedback.expectation_alignment_score).label("avg_eas"),
            func.avg(RecommendationFeedback.trust_score).label("avg_trust"),
            func.avg(RecommendationFeedback.feasibility_score).label("avg_feasibility"),
            func.avg(RecommendationFeedback.usefulness_score).label("avg_usefulness"),
            func.sum(case((RecommendationFeedback.decision == "approved", 1), else_=0)).label("approved"),
            func.sum(case((RecommendationFeedback.would_use_in_real_paper == "yes", 1), else_=0)).label("would_use"),
        ).one()

        total_feedback = int(feedback_stats.total or 0)
        sota_metrics = compute_sota_quality_metrics(db)
        experiment_metrics = experiment_service.experiment_metrics(db)

        base = {
            "run_completion_rate": completed / total_runs if total_runs else 0.0,
            "run_failure_rate": failed / total_runs if total_runs else 0.0,
            "total_runs": total_runs,
            "total_feedback": total_feedback,
            **sota_metrics,
            "experiment": experiment_metrics,
        }

        surveys = db.query(SessionFinalSurvey).all()
        survey_metrics = {
            "count": len(surveys),
            "expectation_met_mean": mean_field(
                [{"expectation_met_score": s.expectation_met_score} for s in surveys],
                "expectation_met_score",
            ),
            "would_use_again_rate": rate(surveys, lambda s: bool(s.would_use_again)),
            "would_recommend_rate": rate(surveys, lambda s: bool(s.would_recommend)),
        }

        if not total_feedback:
            return {
                **base,
                "average_eas": 0.0,
                "approval_rate": 0.0,
                "would_use_rate": 0.0,
                "average_trust_score": 0.0,
                "average_feasibility_score": 0.0,
                "average_usefulness_score": 0.0,
                "rejection_reasons": [],
                "survey_metrics": survey_metrics,
                "rating_distributions": [],
                "weekly_trends": [],
                "ranking_summary": {},
            }

        rejection_reasons = [
            comment
            for (comment,) in db.query(RecommendationFeedback.comment)
            .filter(
                RecommendationFeedback.decision == "rejected",
                RecommendationFeedback.comment.isnot(None),
            )
            .all()
            if comment
        ]

        feedback_rows = [
            {
                "relevance_score": f.relevance_score,
                "originality_score": f.originality_score,
                "clarity_score": f.clarity_score,
                "feasibility_score": f.feasibility_score,
                "trust_score": f.trust_score,
                "usefulness_score": f.usefulness_score,
                "expectation_alignment_score": float(f.expectation_alignment_score or 0),
                "decision": f.decision,
                "would_use_in_real_paper": f.would_use_in_real_paper,
                "created_at": f.created_at.isoformat() if f.created_at else None,
                "run_id": str(f.run_id),
            }
            for f in db.query(RecommendationFeedback).all()
        ]

        report = analysis_data_service.build_report(db)

        return {
            **base,
            "average_eas": float(feedback_stats.avg_eas or 0.0),
            "approval_rate": int(feedback_stats.approved or 0) / total_feedback,
            "would_use_rate": int(feedback_stats.would_use or 0) / total_feedback,
            "average_trust_score": float(feedback_stats.avg_trust or 0.0),
            "average_feasibility_score": float(feedback_stats.avg_feasibility or 0.0),
            "average_usefulness_score": float(feedback_stats.avg_usefulness or 0.0),
            "rejection_reasons": rejection_reasons,
            "survey_metrics": survey_metrics,
            "rating_distributions": all_dimension_statistics(feedback_rows),
            "weekly_trends": report.get("weekly_trends") or [],
            "ranking_summary": report.get("ranking_metrics", {}).get("overall") or {},
        }


validation_metrics_service = ValidationMetricsService()
