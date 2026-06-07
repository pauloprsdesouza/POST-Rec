"""Session final survey routes."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from apps.api.shared.database import get_db
from apps.api.shared.models import SessionFinalSurvey, VolunteerSession
from apps.api.shared.schemas.common import FinalSurveyCreate

router = APIRouter(prefix="/api/v1")


@router.post("/session-final-surveys")
def create_final_survey(payload: FinalSurveyCreate, db: Session = Depends(get_db)):
    survey = SessionFinalSurvey(**payload.model_dump())
    db.add(survey)
    session = db.query(VolunteerSession).filter_by(id=payload.session_id).first()
    if session:
        session.status = "completed"
    db.commit()
    return {"status": "recorded"}
