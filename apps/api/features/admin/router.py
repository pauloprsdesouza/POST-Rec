"""Admin routes — operator dashboard, evaluation, configuration, user management."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from apps.api.features.admin.service import admin_service
from apps.api.shared.database import get_db
from apps.api.shared.dependencies import get_current_admin
from apps.api.shared.models import User
from apps.api.shared.schemas.common import (
    AdminModelEvaluationResponse,
    AdminOverviewResponse,
    AdminSystemConfigResponse,
    AdminUserListResponse,
    AdminUserResponse,
    AdminUserRoleUpdate,
    ResearchReportResponse,
    ValidationDashboardResponse,
)

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


@router.get("/overview", response_model=AdminOverviewResponse)
def admin_overview(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    return admin_service.get_overview(db)


@router.get("/system", response_model=AdminSystemConfigResponse)
def admin_system(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    _ = db  # readiness probe uses its own session operations
    return admin_service.get_system_config()


@router.get("/models", response_model=AdminModelEvaluationResponse)
def admin_models(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    return admin_service.get_model_evaluation(db)


@router.get("/evaluation/dashboard", response_model=ValidationDashboardResponse)
def admin_evaluation_dashboard(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    return admin_service.get_evaluation_dashboard(db)


@router.get("/evaluation/research-report", response_model=ResearchReportResponse)
def admin_research_report(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    return admin_service.get_research_report(db)


@router.get("/users", response_model=AdminUserListResponse)
def admin_list_users(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    return admin_service.list_users(db, limit=limit, offset=offset)


@router.patch("/users/{user_id}/role", response_model=AdminUserResponse)
def admin_update_user_role(
    user_id: uuid.UUID,
    payload: AdminUserRoleUpdate,
    db: Session = Depends(get_db),
    actor: User = Depends(get_current_admin),
):
    try:
        return admin_service.update_user_role(db, actor=actor, user_id=user_id, role=payload.role)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
