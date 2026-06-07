"""Volunteer session routes."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from apps.api.shared.database import get_db
from apps.api.shared.dependencies import get_current_user_optional
from apps.api.shared.models import User, VolunteerSession
from apps.api.shared.schemas.common import SessionCreate, SessionResponse
from apps.api.features.runs.access import user_id_str

router = APIRouter(prefix="/api/v1")


@router.post("/sessions", response_model=SessionResponse)
def create_session(
    payload: SessionCreate,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    user_id = user_id_str(current_user) or payload.user_id
    session = VolunteerSession(user_id=user_id, user_agent=payload.user_agent)
    db.add(session)
    db.commit()
    db.refresh(session)
    return SessionResponse(session_id=session.id, status=session.status)
