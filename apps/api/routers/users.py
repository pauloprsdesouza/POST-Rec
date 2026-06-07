"""User profile and run history routes."""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from apps.api.database import get_db
from apps.api.dependencies import get_current_user_required
from apps.api.models import ParticipantConsent, RecommendationCandidate, RecommendationRun, User
from apps.api.schemas.common import (
    RecommendationDefaults,
    RunSummaryResponse,
    UserAccountResponse,
    UserAccountUpdate,
    UserConsentStatusResponse,
    UserProfileResponse,
    UserProfileUpdate,
)
from apps.api.services.auth_service import AuthError, auth_service
from apps.api.services.cache_service import CacheKeys, CacheTTL, cache_service
from apps.api.services.profile_service import profile_service
from packages.postrec_core.domain.enums import RunStatus

router = APIRouter(prefix="/api/v1/users/me", tags=["users"])

CURRENT_CONSENT_VERSION = "v1.0"


def _profile_response(profile) -> UserProfileResponse:
    defaults = profile.recommendation_defaults or {}
    return UserProfileResponse(
        research_area=profile.research_area,
        academic_level=profile.academic_level,
        professional_role=profile.professional_role,
        experience_with_ai=profile.experience_with_ai,
        experience_with_recommender_systems=profile.experience_with_recommender_systems,
        experience_with_scientific_writing=profile.experience_with_scientific_writing,
        goal_with_postrec=profile.goal_with_postrec,
        learned_topics=list(profile.learned_topics or []),
        avoided_topics=list(profile.avoided_topics or []),
        preferred_techniques=list(profile.preferred_techniques or []),
        recommendation_defaults=RecommendationDefaults(**defaults) if defaults else None,
        updated_at=profile.updated_at,
    )


def _load_consent(db: Session, user_id: uuid.UUID) -> UserConsentStatusResponse:
    consent = (
        db.query(ParticipantConsent)
        .filter_by(user_id=str(user_id), accepted=True)
        .order_by(ParticipantConsent.accepted_at.desc())
        .first()
    )
    if not consent:
        return UserConsentStatusResponse(accepted=False)
    return UserConsentStatusResponse(
        accepted=True,
        consent_version=consent.consent_version,
        accepted_at=consent.accepted_at,
    )


def _load_runs(db: Session, user_id: uuid.UUID, limit: int) -> list[RunSummaryResponse]:
    runs = (
        db.query(RecommendationRun)
        .filter_by(user_id=str(user_id))
        .order_by(RecommendationRun.created_at.desc())
        .limit(min(limit, 100))
        .all()
    )

    summaries: list[RunSummaryResponse] = []
    for run in runs:
        rec_count = db.query(RecommendationCandidate).filter_by(run_id=run.id, status="published").count()
        summaries.append(
            RunSummaryResponse(
                id=run.id,
                status=run.status,
                progress=run.progress,
                mode=run.mode,
                created_at=run.created_at,
                finished_at=run.finished_at,
                topics=list((run.input or {}).get("topics") or []),
                recommendation_count=rec_count if run.status == RunStatus.COMPLETED else 0,
            )
        )
    return summaries


@router.get("/consent", response_model=UserConsentStatusResponse)
def get_my_consent(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_required),
):
    user_id = str(current_user.id)
    key = CacheKeys.user_consent(user_id)

    def load() -> dict:
        return _load_consent(db, current_user.id).model_dump(mode="json")

    data = cache_service.get_or_load(key, CacheTTL.CONSENT, load)
    return UserConsentStatusResponse.model_validate(data)


@router.get("/account", response_model=UserAccountResponse)
def get_my_account(current_user: User = Depends(get_current_user_required)):
    user_id = str(current_user.id)
    key = CacheKeys.user_account(user_id)

    def load() -> dict:
        return UserAccountResponse(
            full_name=current_user.full_name,
            email=current_user.email,
            phone_number=current_user.phone_number,
            whatsapp_opt_in=current_user.whatsapp_opt_in,
        ).model_dump(mode="json")

    data = cache_service.get_or_load(key, CacheTTL.ACCOUNT, load)
    return UserAccountResponse.model_validate(data)


@router.put("/account", response_model=UserAccountResponse)
def update_my_account(
    payload: UserAccountUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_required),
):
    try:
        user = auth_service.update_account(
            db,
            current_user,
            full_name=payload.full_name,
            email=payload.email,
            phone_number=payload.phone_number,
            whatsapp_opt_in=payload.whatsapp_opt_in,
        )
    except AuthError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    cache_service.invalidate_user_account(str(user.id))
    return UserAccountResponse(
        full_name=user.full_name,
        email=user.email,
        phone_number=user.phone_number,
        whatsapp_opt_in=user.whatsapp_opt_in,
    )


@router.get("/profile", response_model=UserProfileResponse)
def get_my_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_required),
):
    user_id = str(current_user.id)
    key = CacheKeys.user_profile(user_id)

    def load() -> dict:
        profile = profile_service.get_or_create(db, current_user.id)
        return _profile_response(profile).model_dump(mode="json")

    data = cache_service.get_or_load(key, CacheTTL.PROFILE, load)
    return UserProfileResponse.model_validate(data)


@router.put("/profile", response_model=UserProfileResponse)
def update_my_profile(
    payload: UserProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_required),
):
    data = payload.model_dump(exclude_unset=True)
    if payload.recommendation_defaults is not None:
        data["recommendation_defaults"] = payload.recommendation_defaults.model_dump()
    profile = profile_service.update_profile(db, current_user.id, data)
    cache_service.invalidate_user_profile(str(current_user.id))
    return _profile_response(profile)


@router.get("/recommendation-runs", response_model=list[RunSummaryResponse])
def list_my_runs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_required),
    limit: int = 50,
):
    user_id = str(current_user.id)
    capped = min(limit, 100)
    key = CacheKeys.user_runs(user_id, capped)

    def load() -> list[dict]:
        return [item.model_dump(mode="json") for item in _load_runs(db, current_user.id, capped)]

    data = cache_service.get_or_load(key, CacheTTL.RUNS_LIST, load)
    return [RunSummaryResponse.model_validate(item) for item in data]
