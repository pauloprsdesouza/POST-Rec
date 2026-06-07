"""Recommendation feedback routes."""

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from apps.api.shared.database import get_db
from apps.api.shared.dependencies import get_current_user_optional
from apps.api.shared.models import User
from apps.api.shared.schemas.common import FeedbackCreate, FeedbackResponse
from apps.api.features.feedback.service import feedback_service
from apps.api.features.runs.access import user_id_str

router = APIRouter(prefix="/api/v1")


@router.post("/recommendations/{recommendation_id}/feedback", response_model=FeedbackResponse)
def submit_feedback(
    recommendation_id: uuid.UUID,
    payload: FeedbackCreate,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    feedback = feedback_service.create_feedback(
        db,
        recommendation_id,
        payload.session_id,
        payload.run_id,
        payload.model_dump(),
        user_id=user_id_str(current_user),
    )
    return FeedbackResponse(id=feedback.id, expectation_alignment_score=float(feedback.expectation_alignment_score))
