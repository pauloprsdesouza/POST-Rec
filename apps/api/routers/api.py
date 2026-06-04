"""FastAPI route handlers."""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from apps.api.database import get_db
from apps.api.dependencies import (
    get_current_user_optional,
    get_current_user_required,
    get_run_stream_access,
)
from apps.api.models import (
    ParticipantConsent,
    ParticipantProfile,
    RecommendationCandidate,
    RecommendationRun,
    SessionFinalSurvey,
    User,
    UserExpectation,
    UserInteractionEvent,
    VolunteerSession,
)
from apps.api.schemas.common import (
    ConsentCreate,
    ConsentResponse,
    ExpectationCreate,
    ExpectationResponse,
    FeedbackCreate,
    FeedbackResponse,
    FinalSurveyCreate,
    HealthResponse,
    InteractionEventCreate,
    ProfileCreate,
    ProfileResponse,
    ReadyResponse,
    RecommendationResponse,
    RecommendationRunCreate,
    RecommendationRunResponse,
    RunDetailResponse,
    RunEventResponse,
    SessionCreate,
    SessionResponse,
    SourceDocumentResponse,
    ValidationDashboardResponse,
)
from apps.api.services.source_service import (
    enrich_evidence_papers,
    get_run_source_documents,
)
from apps.api.services.cache_service import (
    CacheKeys,
    CacheTTL,
    cache_service,
    is_terminal_run,
    run_detail_ttl,
    run_events_ttl,
)
from apps.api.services.feedback_service import feedback_service
from apps.api.services.profile_service import profile_service
from apps.api.services.run_query import run_detail_payload, run_events_payload
from apps.api.services.run_service import run_service
from apps.api.services.run_stream import stream_run_updates
from apps.api.services.validation_metrics_service import validation_metrics_service
from apps.api.settings import get_settings
from apps.api.workers.tasks import process_recommendation_run

router = APIRouter(prefix="/api/v1")


def _user_id_str(user: User | None) -> str | None:
    return str(user.id) if user else None


def _ensure_run_access(run: RecommendationRun, user: User | None) -> None:
    if user and run.user_id and run.user_id != str(user.id):
        raise HTTPException(status_code=403, detail="Not allowed to access this run")


def _run_detail_payload(db: Session, run: RecommendationRun) -> dict:
    return run_detail_payload(db, run)


def _run_events_payload(db: Session, run_id: uuid.UUID, run_status: str) -> list[dict]:
    return run_events_payload(db, run_id, run_status)


def _run_sources_payload(db: Session, run_id: uuid.UUID) -> list[dict]:
    documents = get_run_source_documents(db, run_id)
    return [
        SourceDocumentResponse(
            id=d.id,
            source=d.source,
            title=d.title,
            abstract=d.abstract,
            authors=d.authors,
            year=d.year,
            venue=d.venue,
            doi=d.doi,
            url=d.url,
            citation_count=d.citation_count or 0,
        ).model_dump(mode="json")
        for d in documents
    ]


def _run_recommendations_payload(
    db: Session,
    run_id: uuid.UUID,
    *,
    include_refinement: bool = False,
) -> list[dict]:
    candidates = db.query(RecommendationCandidate).filter_by(run_id=run_id).all()
    if not include_refinement:
        candidates = [c for c in candidates if c.status == "published"]
    candidates.sort(
        key=lambda c: float(c.final_score) if c.final_score is not None else float("-inf"),
        reverse=True,
    )
    source_docs = get_run_source_documents(db, run_id)
    payload: list[dict] = []
    for candidate in candidates:
        scores = candidate.scores or {}
        sota = scores.get("_sota") if isinstance(scores.get("_sota"), dict) else {}
        validation_issues = scores.get("_validation_issues")
        if not isinstance(validation_issues, list):
            validation_issues = scores.get("_critic_issues") if isinstance(scores.get("_critic_issues"), list) else None
        payload.append(
            RecommendationResponse(
                id=candidate.id,
                title=candidate.title,
                technique_name=candidate.technique_name,
                research_gap=candidate.research_gap,
                research_question=candidate.research_question,
                hypothesis=candidate.hypothesis,
                proposed_method=candidate.proposed_method,
                related_work_summary=candidate.related_work_summary,
                expected_contribution=candidate.expected_contribution,
                sota_summary=sota.get("sota_summary"),
                novelty_delta=sota.get("novelty_delta"),
                closest_prior_work=sota.get("closest_prior_work"),
                differentiation_score_rationale=sota.get("differentiation_score_rationale"),
                sota_anchors=sota.get("sota_anchors"),
                sota_fit=scores.get("sota_fit"),
                novelty_verified=scores.get("novelty_verified"),
                facet_novelty_index=scores.get("facet_novelty_index"),
                gap_alignment_score=scores.get("gap_alignment_score"),
                fggv_score=scores.get("fggv_score"),
                facet_deltas=sota.get("facet_deltas"),
                aligned_gaps=sota.get("aligned_gaps"),
                recency_gap=scores.get("recency_gap"),
                embedding_distance=scores.get("embedding_distance"),
                critic_accepted=scores.get("critic_accepted"),
                validation_issues=validation_issues,
                status=candidate.status,
                evidence_papers=enrich_evidence_papers(candidate.evidence_papers, source_docs),
                datasets=candidate.datasets,
                evaluation_metrics=candidate.evaluation_metrics,
                experimental_plan=candidate.experimental_plan,
                risks=candidate.risks,
                confidence_level=candidate.confidence_level,
                scores=candidate.scores,
                final_score=float(candidate.final_score) if candidate.final_score else None,
            ).model_dump(mode="json")
        )
    return payload


@router.post("/sessions", response_model=SessionResponse)
def create_session(
    payload: SessionCreate,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    user_id = _user_id_str(current_user) or payload.user_id
    session = VolunteerSession(user_id=user_id, user_agent=payload.user_agent)
    db.add(session)
    db.commit()
    db.refresh(session)
    return SessionResponse(session_id=session.id, status=session.status)


@router.post("/consents", response_model=ConsentResponse)
def create_consent(payload: ConsentCreate, db: Session = Depends(get_db)):
    consent = ParticipantConsent(
        user_id=payload.user_id,
        session_id=payload.session_id,
        consent_version=payload.consent_version,
        accepted=payload.accepted,
    )
    db.add(consent)
    db.commit()
    db.refresh(consent)
    if payload.accepted:
        cache_service.invalidate_user_consent(payload.user_id)
    return ConsentResponse(id=consent.id, accepted=consent.accepted)


@router.post("/profiles", response_model=ProfileResponse)
def create_profile(
    payload: ProfileCreate,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    data = payload.model_dump()
    if current_user:
        data["user_id"] = str(current_user.id)
    profile = ParticipantProfile(**data)
    db.add(profile)
    db.commit()
    db.refresh(profile)
    if current_user:
        profile_service.upsert_from_participant(db, current_user.id, profile)
        cache_service.invalidate_user_profile(str(current_user.id))
    return ProfileResponse(id=profile.id)


@router.post("/expectations", response_model=ExpectationResponse)
def create_expectation(
    payload: ExpectationCreate,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    data = payload.model_dump()
    if current_user:
        data["user_id"] = str(current_user.id)
    expectation = UserExpectation(**data)
    db.add(expectation)
    db.commit()
    db.refresh(expectation)
    return ExpectationResponse(id=expectation.id)


@router.post("/recommendation-runs", response_model=RecommendationRunResponse)
def create_recommendation_run(
    payload: RecommendationRunCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_required),
):
    run = run_service.create_run(
        db=db,
        session_id=payload.session_id,
        expectation_id=payload.expectation_id,
        request_id=payload.request_id,
        topics=payload.topics,
        mode=payload.mode,
        max_papers=payload.max_papers,
        max_recommendations=payload.max_recommendations,
        constraints=payload.constraints.model_dump(),
        user_id=str(current_user.id),
    )
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
    run = db.query(RecommendationRun).filter_by(id=run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    _ensure_run_access(run, current_user)
    run_key = str(run_id)
    ttl = run_detail_ttl(run.status)

    def load() -> dict:
        fresh = db.query(RecommendationRun).filter_by(id=run_id).first()
        if not fresh:
            raise HTTPException(status_code=404, detail="Run not found")
        return _run_detail_payload(db, fresh)

    if is_terminal_run(run.status):
        data = cache_service.get_or_load(CacheKeys.run_detail(run_key), ttl, load)
    else:
        cached = cache_service.get_json(CacheKeys.run_detail(run_key))
        if cached is not None:
            return RunDetailResponse.model_validate(cached)
        data = load()
        cache_service.set_json(CacheKeys.run_detail(run_key), data, ttl)

    return RunDetailResponse.model_validate(data)


@router.get("/recommendation-runs/{run_id}/events", response_model=list[RunEventResponse])
def get_run_events(run_id: uuid.UUID, db: Session = Depends(get_db)):
    run = db.query(RecommendationRun).filter_by(id=run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    run_key = str(run_id)
    ttl = run_events_ttl(run.status)

    def load() -> list[dict]:
        fresh = db.query(RecommendationRun).filter_by(id=run_id).first()
        if not fresh:
            raise HTTPException(status_code=404, detail="Run not found")
        return _run_events_payload(db, run_id, fresh.status)

    if is_terminal_run(run.status):
        data = cache_service.get_or_load(CacheKeys.run_events(run_key), ttl, load)
    else:
        data = load()
        cache_service.set_json(CacheKeys.run_events(run_key), data, ttl)

    return [RunEventResponse.model_validate(item) for item in data]


@router.get("/recommendation-runs/{run_id}/stream")
async def stream_run(
    run: RecommendationRun = Depends(get_run_stream_access),
    db: Session = Depends(get_db),
):
    """Server-Sent Events stream for live run status and activity log updates."""
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
    run = db.query(RecommendationRun).filter_by(id=run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    run_key = str(run_id)
    if not is_terminal_run(run.status):
        documents = get_run_source_documents(db, run_id)
        return [
            SourceDocumentResponse(
                id=d.id,
                source=d.source,
                title=d.title,
                abstract=d.abstract,
                authors=d.authors,
                year=d.year,
                venue=d.venue,
                doi=d.doi,
                url=d.url,
                citation_count=d.citation_count or 0,
            )
            for d in documents
        ]

    data = cache_service.get_or_load(
        CacheKeys.run_sources(run_key),
        CacheTTL.SOURCE_DOCUMENTS,
        lambda: _run_sources_payload(db, run_id),
    )
    return [SourceDocumentResponse.model_validate(item) for item in data]


@router.get(
    "/recommendation-runs/{run_id}/recommendations", response_model=list[RecommendationResponse]
)
def get_recommendations(
    run_id: uuid.UUID,
    include_refinement: bool = False,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    run = db.query(RecommendationRun).filter_by(id=run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    _ensure_run_access(run, current_user)

    run_key = str(run_id)
    cache_suffix = ":all" if include_refinement else ":published"
    if not is_terminal_run(run.status):
        return [
            RecommendationResponse.model_validate(item)
            for item in _run_recommendations_payload(
                db, run_id, include_refinement=include_refinement
            )
        ]

    data = cache_service.get_or_load(
        CacheKeys.run_recommendations(run_key) + cache_suffix,
        CacheTTL.RECOMMENDATIONS,
        lambda: _run_recommendations_payload(
            db, run_id, include_refinement=include_refinement
        ),
    )
    return [RecommendationResponse.model_validate(item) for item in data]


@router.post("/recommendation-runs/{run_id}/cancel")
def cancel_run(run_id: uuid.UUID, db: Session = Depends(get_db)):
    run = db.query(RecommendationRun).filter_by(id=run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    run_service.cancel_run(db, run)
    return {"status": "cancelled"}


@router.post("/recommendations/{recommendation_id}/feedback", response_model=FeedbackResponse)
def submit_feedback(
    recommendation_id: uuid.UUID,
    payload: FeedbackCreate,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    feedback = feedback_service.create_feedback(
        db,
        recommendation_id,
        payload.session_id,
        payload.run_id,
        payload.model_dump(),
        user_id=_user_id_str(current_user),
    )
    return FeedbackResponse(id=feedback.id, expectation_alignment_score=float(feedback.expectation_alignment_score))


@router.post("/interaction-events")
def create_interaction_event(payload: InteractionEventCreate, db: Session = Depends(get_db)):
    event = UserInteractionEvent(
        session_id=payload.session_id,
        run_id=payload.run_id,
        recommendation_id=payload.recommendation_id,
        event_type=payload.event_type,
        event_value=payload.event_value,
        metadata_=payload.metadata,
    )
    db.add(event)
    db.commit()
    return {"status": "recorded"}


@router.post("/session-final-surveys")
def create_final_survey(payload: FinalSurveyCreate, db: Session = Depends(get_db)):
    survey = SessionFinalSurvey(**payload.model_dump())
    db.add(survey)
    session = db.query(VolunteerSession).filter_by(id=payload.session_id).first()
    if session:
        session.status = "completed"
    db.commit()
    return {"status": "recorded"}


@router.get("/validation/dashboard", response_model=ValidationDashboardResponse)
def validation_dashboard(db: Session = Depends(get_db)):
    return validation_metrics_service.get_dashboard(db)


@router.get("/health", response_model=HealthResponse)
def health():
    return HealthResponse(status="ok")


@router.get("/ready", response_model=ReadyResponse)
def ready(db: Session = Depends(get_db)):
    checks: dict[str, str] = {}
    settings = get_settings()

    try:
        db.execute(__import__("sqlalchemy").text("SELECT 1"))
        ext = db.execute(__import__("sqlalchemy").text(
            "SELECT extversion FROM pg_extension WHERE extname = 'vector'"
        )).scalar()
        checks["postgres"] = "ok" if ext else "fail: pgvector extension missing"
        if ext:
            checks["pgvector"] = f"ok ({ext})"
    except Exception as exc:
        checks["postgres"] = f"fail: {exc}"

    try:
        import redis

        client = redis.from_url(settings.redis_url, socket_connect_timeout=3)
        client.ping()
        checks["redis"] = "ok"
    except Exception as exc:
        checks["redis"] = f"fail: {exc}"

    if settings.cache_enabled and settings.redis_url:
        try:
            import redis

            from apps.api.services.cache_service import _cache_redis_url

            cache_client = redis.from_url(
                _cache_redis_url(settings.redis_url, settings.cache_redis_db),
                socket_connect_timeout=3,
            )
            cache_client.ping()
            checks["redis_cache"] = f"ok (db {settings.cache_redis_db})"
        except Exception as exc:
            checks["redis_cache"] = f"fail: {exc}"
    else:
        checks["redis_cache"] = "disabled"

    try:
        import amqp

        conn = amqp.Connection(
            host=f"{settings.rabbitmq_host}:{settings.rabbitmq_port}",
            userid=settings.rabbitmq_user,
            password=settings.rabbitmq_password,
            connect_timeout=3,
        )
        conn.connect()
        conn.close()
        checks["rabbitmq"] = "ok"
    except Exception as exc:
        checks["rabbitmq"] = f"fail: {exc}"

    checks["gemini_configured"] = "ok" if settings.gemini_api_key else "warning: no API key"
    checks["migrations"] = "ok"

    all_ok = all(v == "ok" or v.startswith("warning") or v.startswith("ok (") for v in checks.values())
    return ReadyResponse(status="ready" if all_ok else "not_ready", checks=checks)
