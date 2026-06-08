"""Session final survey routes."""

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from apps.api.shared.database import get_db
from apps.api.shared.models import SessionFinalSurvey, StudySession
from apps.api.shared.schemas.common import FinalSurveyCreate
from packages.postrec_core.domain.enums import SessionStatus

router = APIRouter(prefix="/api/v1")


@router.post("/session-final-surveys")
def create_final_survey(payload: FinalSurveyCreate, db: Session = Depends(get_db)):
    existing = db.query(SessionFinalSurvey).filter_by(session_id=payload.session_id).first()
    if existing:
        raise HTTPException(status_code=409, detail="Final survey already submitted for this session")

    survey = SessionFinalSurvey(**payload.model_dump())
    db.add(survey)
    session = db.query(StudySession).filter_by(id=payload.session_id).first()
    if session:
        session.status = SessionStatus.COMPLETED
        session.finished_at = datetime.now(UTC)
    db.commit()
    return {"status": "recorded"}
