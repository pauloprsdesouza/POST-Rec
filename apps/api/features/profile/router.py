"""Research profile and expectation routes."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from apps.api.features.profile.service import profile_service
from apps.api.features.runs.access import user_id_optional
from apps.api.shared.database import get_db
from apps.api.shared.dependencies import get_current_user_optional
from apps.api.shared.infra.cache import cache_service
from apps.api.shared.models import SessionExpectation, SessionProfile, User
from apps.api.shared.schemas.common import (
    ExpectationCreate,
    ExpectationResponse,
    ProfileCreate,
    ProfileResponse,
)

router = APIRouter(prefix="/api/v1")


@router.post("/profiles", response_model=ProfileResponse)
def create_profile(
    payload: ProfileCreate,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    data = payload.model_dump(exclude={"user_id"})
    data["user_id"] = user_id_optional(current_user)
    profile = SessionProfile(**data)
    db.add(profile)
    db.commit()
    db.refresh(profile)
    if current_user:
        profile_service.upsert_from_session_profile(db, current_user.id, profile)
        cache_service.invalidate_user_profile(str(current_user.id))
    return ProfileResponse(id=profile.id)


@router.post("/expectations", response_model=ExpectationResponse)
def create_expectation(
    payload: ExpectationCreate,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    data = payload.model_dump(exclude={"user_id"})
    data["user_id"] = user_id_optional(current_user)
    expectation = SessionExpectation(**data)
    db.add(expectation)
    db.commit()
    db.refresh(expectation)
    return ExpectationResponse(id=expectation.id)
