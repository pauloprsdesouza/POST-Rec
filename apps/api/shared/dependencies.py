"""FastAPI dependencies."""

import uuid

from fastapi import Depends, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from apps.api.shared.database import get_db
from apps.api.shared.models import RecommendationRun, User
from apps.api.features.auth.service import AuthError, auth_service
from apps.api.shared.settings import get_settings

bearer_scheme = HTTPBearer(auto_error=False)


def _resolve_user_from_token(db: Session, access_token: str | None) -> User | None:
    if not access_token:
        return None
    try:
        user_id = auth_service.decode_token(access_token)
    except AuthError:
        return None
    return auth_service.get_user(db, user_id)


def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User | None:
    if not credentials:
        return None
    return _resolve_user_from_token(db, credentials.credentials)


def get_current_user_required(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    settings = get_settings()
    if not credentials:
        if settings.auth_enabled:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Login required")

    try:
        user_id = auth_service.decode_token(credentials.credentials)
    except AuthError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    user = auth_service.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


def get_run_stream_access(
    run_id: uuid.UUID,
    token: str | None = Query(None, description="Bearer token for EventSource clients"),
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> RecommendationRun:
    access_token = token or (credentials.credentials if credentials else None)
    if not access_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    user = _resolve_user_from_token(db, access_token)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    run = db.query(RecommendationRun).filter_by(id=run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    if run.user_id and run.user_id != str(user.id):
        raise HTTPException(status_code=403, detail="Not allowed to access this run")

    return run
