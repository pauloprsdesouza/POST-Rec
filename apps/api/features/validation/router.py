"""Validation dashboard routes."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from apps.api.shared.database import get_db
from apps.api.shared.schemas.common import ValidationDashboardResponse
from apps.api.features.validation.service import validation_metrics_service

router = APIRouter(prefix="/api/v1")


@router.get("/validation/dashboard", response_model=ValidationDashboardResponse)
def validation_dashboard(db: Session = Depends(get_db)):
    return validation_metrics_service.get_dashboard(db)
