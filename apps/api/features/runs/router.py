"""Recommendation run routes."""

import uuid

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from apps.api.features.experiments.service import experiment_service
from apps.api.features.recommendations.sources import get_run_source_documents, serialize_source_documents
from apps.api.features.runs.access import ensure_run_access, get_run_or_404, user_id_optional
from apps.api.features.runs.query import (
    feedback_counts_by_run,
    run_detail_payload,
    run_events_payload,
    run_sources_payload,
)
from apps.api.features.runs.service import run_service
from apps.api.features.runs.stream import stream_run_updates
from apps.api.shared.database import get_db
from apps.api.shared.dependencies import (
    get_current_user_optional,
    get_current_user_required,
    get_run_stream_access,
)
from apps.api.shared.infra.cache import (
    CacheKeys,
    CacheTTL,
    cache_service,
    is_terminal_run,
    run_detail_ttl,
    run_events_ttl,
)
from apps.api.shared.infra.cache_helpers import load_cached_json
from apps.api.shared.models import RecommendationRun, User
from apps.api.shared.schemas.common import (
    RecommendationRunCreate,
    RecommendationRunResponse,
    RunDetailResponse,
    RunEventResponse,
    SourceDocumentResponse,
)

router = APIRouter(prefix="/api/v1")


@router.post("/recommendation-runs", response_model=RecommendationRunResponse)
def create_recommendation_run(
    payload: RecommendationRunCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_required),
):
    constraints = payload.constraints.model_dump()
    assignment = experiment_service.resolve_run_assignment(
        user_id=current_user.id,
        requested_mode=payload.mode,
        avoid_real_user_experiments=bool(constraints.get("avoid_real_user_experiments", True)),
    )
    run = run_service.create_run(
        db=db,
        session_id=payload.session_id,
        expectation_id=payload.expectation_id,
        request_id=payload.request_id,
        topics=payload.topics,
        mode=assignment.mode,
        max_papers=payload.max_papers,
        max_recommendations=payload.max_recommendations,
        constraints=constraints,
        user_id=current_user.id,
        experiment_id=assignment.experiment_id,
        experiment_variant=assignment.experiment_variant,
        assigned_mode=assignment.assigned_mode,
        presentation_profile=assignment.presentation_profile,
    )
    from apps.api.workers.tasks import process_recommendation_run

    process_recommendation_run.delay(str(run.id))
    cache_service.invalidate_user_runs(str(current_user.id))
    return RecommendationRunResponse(
        run_id=run.id,
        status=run.status,
        progress=run.progress,
        message="Recommendation run created successfully.",
    )


@router.get("/recommendation-runs/{run_id}", response_model=RunDetailResponse)
def get_run(
    run_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    run = get_run_or_404(db, run_id)
    ensure_run_access(run, current_user)
    run_key = str(run_id)
    user_id = user_id_optional(current_user)
    data = load_cached_json(
        CacheKeys.run_detail(run_key),
        run_detail_ttl(run.status),
        lambda: run_detail_payload(db, run),
        terminal=is_terminal_run(run.status),
    )
    if user_id:
        rec_count = int(data.get("recommendation_count") or 0)
        feedback_count = feedback_counts_by_run(db, user_id, [run_id]).get(run_id, 0) if rec_count > 0 else 0
        data = {
            **data,
            "feedback_count": feedback_count,
            "feedback_complete": rec_count > 0 and feedback_count >= rec_count,
        }
    return RunDetailResponse.model_validate(data)


@router.get("/recommendation-runs/{run_id}/events", response_model=list[RunEventResponse])
def get_run_events_endpoint(run_id: uuid.UUID, db: Session = Depends(get_db)):
    run = get_run_or_404(db, run_id)
    run_key = str(run_id)
    data = load_cached_json(
        CacheKeys.run_events(run_key),
        run_events_ttl(run.status),
        lambda: run_events_payload(db, run_id, run.status, run),
        terminal=is_terminal_run(run.status),
    )
    return [RunEventResponse.model_validate(item) for item in data]


@router.get("/recommendation-runs/{run_id}/stream")
async def stream_run(
    run: RecommendationRun = Depends(get_run_stream_access),
    db: Session = Depends(get_db),
):
    return StreamingResponse(
        stream_run_updates(db, run),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get(
    "/recommendation-runs/{run_id}/source-documents",
    response_model=list[SourceDocumentResponse],
)
def get_run_source_documents_endpoint(run_id: uuid.UUID, db: Session = Depends(get_db)):
    run = get_run_or_404(db, run_id)
    run_key = str(run_id)
    if not is_terminal_run(run.status):
        return serialize_source_documents(get_run_source_documents(db, run_id))

    data = load_cached_json(
        CacheKeys.run_sources(run_key),
        CacheTTL.SOURCE_DOCUMENTS,
        lambda: run_sources_payload(db, run_id),
        terminal=True,
    )
    return [SourceDocumentResponse.model_validate(item) for item in data]


@router.post("/recommendation-runs/{run_id}/cancel")
def cancel_run(run_id: uuid.UUID, db: Session = Depends(get_db)):
    run = get_run_or_404(db, run_id)
    run_service.cancel_run(db, run)
    return {"status": "cancelled"}
