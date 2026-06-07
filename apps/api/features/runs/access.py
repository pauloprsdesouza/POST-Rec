"""Run access helpers shared by run and recommendation routes."""

import uuid

from fastapi import HTTPException
from sqlalchemy.orm import Session

from apps.api.shared.models import RecommendationRun, User


def user_id_optional(user: User | None) -> uuid.UUID | None:
    return user.id if user else None


def ensure_run_access(run: RecommendationRun, user: User | None) -> None:
    if user and run.user_id and run.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not allowed to access this run")


def get_run_or_404(db: Session, run_id: uuid.UUID) -> RecommendationRun:
    run = db.query(RecommendationRun).filter_by(id=run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return run
