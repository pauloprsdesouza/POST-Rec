"""Research project API routes."""

import uuid

from fastapi import APIRouter, Depends, Query
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from apps.api.features.projects.service import project_service
from apps.api.shared.database import get_db
from apps.api.shared.dependencies import get_current_user_required
from apps.api.shared.models import User
from apps.api.shared.schemas.common import (
    ProjectCreate,
    ProjectExportResponse,
    ProjectListItem,
    ProjectResponse,
    ProjectTaskUpdate,
    ProjectTaskResponse,
)

router = APIRouter(prefix="/api/v1")


@router.post("/projects", response_model=ProjectResponse)
def create_project(
    payload: ProjectCreate,
    locale: str = Query("en-US"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_required),
):
    project = project_service.create_project(
        db,
        user=current_user,
        recommendation_id=payload.recommendation_id,
        locale=locale,
    )
    return ProjectResponse.model_validate(project_service.project_to_dict(project))


@router.get("/projects", response_model=list[ProjectListItem])
def list_projects(
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_required),
):
    projects = project_service.list_projects(db, current_user.id, limit=limit)
    items: list[ProjectListItem] = []
    for project in projects:
        current_phase_title = None
        if project.current_phase_id:
            phase = next((p for p in project.phases if p.id == project.current_phase_id), None)
            current_phase_title = phase.title if phase else None
        items.append(
            ProjectListItem(
                id=project.id,
                run_id=project.run_id,
                recommendation_id=project.recommendation_id,
                title=project.title,
                status=project.status,
                progress_pct=project.progress_pct,
                current_phase_title=current_phase_title,
                created_at=project.created_at,
                updated_at=project.updated_at,
            )
        )
    return items


@router.get("/projects/by-recommendation/{recommendation_id}", response_model=ProjectResponse | None)
def get_project_by_recommendation(
    recommendation_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_required),
):
    project = project_service.get_project_by_recommendation(db, current_user.id, recommendation_id)
    if not project:
        return None
    return ProjectResponse.model_validate(project_service.project_to_dict(project))


@router.get("/projects/{project_id}", response_model=ProjectResponse)
def get_project(
    project_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_required),
):
    project = project_service.get_project(db, project_id, current_user.id)
    return ProjectResponse.model_validate(project_service.project_to_dict(project))


@router.patch("/projects/{project_id}/tasks/{task_id}", response_model=ProjectTaskResponse)
def update_project_task(
    project_id: uuid.UUID,
    task_id: uuid.UUID,
    payload: ProjectTaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_required),
):
    task = project_service.update_task(
        db,
        user=current_user,
        project_id=project_id,
        task_id=task_id,
        status=payload.status,
        user_notes=payload.user_notes,
    )
    return ProjectTaskResponse(
        id=task.id,
        status=task.status,
        user_notes=task.user_notes,
        completed_at=task.completed_at,
    )


@router.get("/projects/{project_id}/export")
def export_project(
    project_id: uuid.UUID,
    format: str = Query("markdown"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_required),
):
    project = project_service.get_project(db, project_id, current_user.id)
    if format != "markdown":
        return ProjectExportResponse(content=project_service.export_markdown(project), format="markdown")
    content = project_service.export_markdown(project)
    return PlainTextResponse(content, media_type="text/markdown; charset=utf-8")
