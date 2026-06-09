"""Experiment enrollment routes."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from apps.api.features.experiments.service import experiment_service
from apps.api.features.profile.service import profile_service
from apps.api.shared.database import get_db
from apps.api.shared.dependencies import get_current_user_required
from apps.api.shared.models import User
from apps.api.shared.schemas.common import ExperimentEnrollmentResponse

router = APIRouter(prefix="/api/v1")


@router.get("/experiments/enrollment", response_model=ExperimentEnrollmentResponse)
def get_experiment_enrollment(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_required),
):
    profile = profile_service.get_or_create(db, current_user.id)
    defaults = profile.recommendation_defaults or {}
    avoid = bool(defaults.get("avoid_real_user_experiments", True))
    return ExperimentEnrollmentResponse.model_validate(
        experiment_service.enrollment_status(
            user_id=str(current_user.id),
            avoid_real_user_experiments=avoid,
        )
    )
