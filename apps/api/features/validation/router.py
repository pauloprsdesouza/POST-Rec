"""Validation dashboard routes (admin-only; prefer /api/v1/admin/evaluation/*)."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from apps.api.features.validation.service import validation_metrics_service
from apps.api.shared.database import get_db
from apps.api.shared.dependencies import get_current_admin
from apps.api.shared.models import User
from apps.api.shared.schemas.common import ResearchReportResponse, ValidationDashboardResponse

router = APIRouter(prefix="/api/v1")


@router.get("/validation/dashboard", response_model=ValidationDashboardResponse)
def validation_dashboard(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    return validation_metrics_service.get_dashboard(db)


@router.get("/validation/research-report", response_model=ResearchReportResponse)
def research_report(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    return validation_metrics_service.get_research_report(db)
