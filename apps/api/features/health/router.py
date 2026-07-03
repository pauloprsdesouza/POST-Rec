"""Health and readiness probes."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from apps.api.features.health.service import check_readiness, readiness_status
from apps.api.shared.database import get_db
from apps.api.shared.schemas.common import HealthResponse, ReadyResponse

router = APIRouter(prefix="/api/v1")


@router.get("/health", response_model=HealthResponse)
def health():
    return HealthResponse(status="ok")


@router.get("/ready", response_model=ReadyResponse)
def ready(db: Session = Depends(get_db)):
    checks = check_readiness(db)
    return ReadyResponse(status=readiness_status(checks), checks=checks)
