"""Experiment enrollment and metrics."""

from __future__ import annotations

from sqlalchemy.orm import Session

from apps.api.features.experiments.assignment import PRESENTATION_BLIND, resolve_experiment_assignment
from apps.api.shared.models import RecommendationFeedback, RecommendationRun
from apps.api.shared.settings import get_settings
from packages.postrec_core.domain.enums import RunStatus


class ExperimentService:
    def enrollment_status(
        self,
        *,
        user_id: str | None,
    ) -> dict:
        settings = get_settings()

        assignment_preview = None
        if user_id:
            assignment_preview = resolve_experiment_assignment(
                user_id=user_id,
                requested_mode="auto",
                experiment_id=settings.experiment_fggv_vs_sota_id,
                treatment_fraction=settings.experiment_treatment_fraction,
            )

        return {
            "experiment_active": True,
            "experiment_id": settings.experiment_fggv_vs_sota_id,
            "enrolled": True,
            "presentation_profile": assignment_preview.presentation_profile if assignment_preview else "standard",
            "control_mode": "sota",
            "treatment_mode": "fggv",
        }

    def resolve_run_assignment(
        self,
        *,
        user_id: str | None,
        requested_mode: str,
    ):
        settings = get_settings()
        return resolve_experiment_assignment(
            user_id=user_id,
            requested_mode=requested_mode,
            experiment_id=settings.experiment_fggv_vs_sota_id,
            treatment_fraction=settings.experiment_treatment_fraction,
        )

    def experiment_metrics(self, db: Session) -> dict | None:
        settings = get_settings()
        experiment_id = settings.experiment_fggv_vs_sota_id
        if not experiment_id:
            return None

        runs = db.query(RecommendationRun).filter(RecommendationRun.experiment_id == experiment_id).all()
        if not runs:
            return None

        run_ids = [run.id for run in runs]
        feedback_rows = db.query(RecommendationFeedback).filter(RecommendationFeedback.run_id.in_(run_ids)).all()
        feedback_by_run = {}
        for row in feedback_rows:
            feedback_by_run.setdefault(row.run_id, []).append(row)

        variants: list[dict] = []
        for variant in ("control", "treatment"):
            variant_runs = [run for run in runs if run.experiment_variant == variant]
            if not variant_runs:
                continue

            variant_run_ids = {run.id for run in variant_runs}
            variant_feedback = [row for row in feedback_rows if row.run_id in variant_run_ids]
            completed = sum(1 for run in variant_runs if run.status == RunStatus.COMPLETED)

            avg_eas = _average([float(row.expectation_alignment_score or 0) for row in variant_feedback])
            avg_originality = _average([row.originality_score for row in variant_feedback])
            approval_rate = _rate(variant_feedback, lambda row: row.decision == "approved")
            would_use_rate = _rate(variant_feedback, lambda row: row.would_use_in_real_paper == "yes")

            variants.append(
                {
                    "variant": variant,
                    "run_count": len(variant_runs),
                    "completed_count": completed,
                    "feedback_count": len(variant_feedback),
                    "average_eas": avg_eas,
                    "average_originality": avg_originality,
                    "approval_rate": approval_rate,
                    "would_use_rate": would_use_rate,
                }
            )

        return {
            "experiment_id": experiment_id,
            "active": True,
            "presentation_profile": PRESENTATION_BLIND,
            "variants": variants,
        }


def _average(values: list[float]) -> float:
    if not values:
        return 0.0
    return round(sum(values) / len(values), 4)


def _rate(rows: list[RecommendationFeedback], predicate) -> float:
    if not rows:
        return 0.0
    return round(sum(1 for row in rows if predicate(row)) / len(rows), 4)


experiment_service = ExperimentService()
