"""Experiment enrollment routes."""

from fastapi import APIRouter, Depends

from apps.api.features.experiments.service import experiment_service
from apps.api.shared.dependencies import get_current_user_required
from apps.api.shared.models import User
from apps.api.shared.schemas.common import ExperimentEnrollmentResponse

router = APIRouter(prefix="/api/v1")


@router.get("/experiments/enrollment", response_model=ExperimentEnrollmentResponse)
def get_experiment_enrollment(
    current_user: User = Depends(get_current_user_required),
):
    return ExperimentEnrollmentResponse.model_validate(
        experiment_service.enrollment_status(user_id=str(current_user.id))
    )
