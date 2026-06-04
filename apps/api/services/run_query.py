"""Read models for recommendation runs (detail, events, stream payloads)."""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from apps.api.models import RecommendationCandidate, RecommendationRun, RecommendationRunEvent
from apps.api.schemas.common import RunDetailResponse
from apps.api.services.run_cost import get_run_estimated_cost, get_run_usage_summary
from apps.api.services.run_events import format_events_for_user, sanitize_run_error_message


def run_detail_payload(db: Session, run: RecommendationRun) -> dict:
    rec_count = (
        db.query(RecommendationCandidate)
        .filter_by(run_id=run.id, status="published")
        .count()
    )
    usage = get_run_usage_summary(db, run, recommendation_count=rec_count)
    return RunDetailResponse(
        id=run.id,
        status=run.status,
        progress=run.progress,
        current_step=run.current_step,
        mode=run.mode,
        error_message=sanitize_run_error_message(run.error_message),
        estimated_cost_usd=get_run_estimated_cost(db, run),
        created_at=run.created_at,
        started_at=run.started_at,
        finished_at=run.finished_at,
        recommendation_count=rec_count,
        topics=list((run.input or {}).get("topics") or []),
        usage=usage,
    ).model_dump(mode="json")


def run_events_payload(db: Session, run_id: uuid.UUID, run_status: str) -> list[dict]:
    events = (
        db.query(RecommendationRunEvent)
        .filter_by(run_id=run_id)
        .order_by(RecommendationRunEvent.created_at)
        .all()
    )
    return format_events_for_user(events, run_status)


def run_stream_payload(db: Session, run: RecommendationRun) -> dict:
    return {
        "run": run_detail_payload(db, run),
        "events": run_events_payload(db, run.id, run.status),
    }
