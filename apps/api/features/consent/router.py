"""Participant consent routes."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from apps.api.shared.database import get_db
from apps.api.shared.models import ParticipantConsent
from apps.api.shared.schemas.common import ConsentCreate, ConsentResponse
from apps.api.shared.infra.cache import cache_service

router = APIRouter(prefix="/api/v1")


@router.post("/consents", response_model=ConsentResponse)
def create_consent(payload: ConsentCreate, db: Session = Depends(get_db)):
    consent = ParticipantConsent(
        user_id=payload.user_id,
        session_id=payload.session_id,
        consent_version=payload.consent_version,
        accepted=payload.accepted,
    )
    db.add(consent)
    db.commit()
    db.refresh(consent)
    if payload.accepted:
        cache_service.invalidate_user_consent(payload.user_id)
    return ConsentResponse(id=consent.id, accepted=consent.accepted)
