"""Recommendation feedback routes."""

import uuid

from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.orm import Session

from apps.api.features.feedback.service import feedback_service
from apps.api.features.runs.access import user_id_optional
from apps.api.shared.database import get_db
from apps.api.shared.dependencies import get_current_user_optional
from apps.api.shared.models import User
from apps.api.shared.schemas.common import FeedbackCreate, FeedbackResponse

router = APIRouter(prefix="/api/v1")


@router.post("/recommendations/{recommendation_id}/feedback", response_model=FeedbackResponse)
def submit_feedback(
    recommendation_id: uuid.UUID,
    payload: FeedbackCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    feedback, calibration_task = feedback_service.create_feedback(
        db,
        recommendation_id,
        payload.session_id,
        payload.run_id,
        payload.model_dump(),
        user_id=user_id_optional(current_user),
    )
    if calibration_task is not None:
        background_tasks.add_task(calibration_task)
    return FeedbackResponse(id=feedback.id, expectation_alignment_score=float(feedback.expectation_alignment_score))
