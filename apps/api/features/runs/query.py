"""Read models for recommendation runs (detail, events, summaries, API payloads)."""

from __future__ import annotations

import uuid

from sqlalchemy import func
from sqlalchemy.orm import Session

from apps.api.shared.models import (
    RecommendationCandidate,
    RecommendationRun,
    RecommendationRunEvent,
)
from apps.api.shared.schemas.common import (
    RecommendationResponse,
    RunDetailResponse,
    RunSummaryResponse,
)
from apps.api.features.runs.cost import get_run_usage_summary
from apps.api.features.runs.events import format_events_for_user, sanitize_run_error_message
from apps.api.features.recommendations.sources import (
    enrich_evidence_papers,
    get_run_source_documents,
    serialize_source_documents,
)
from packages.postrec_core.domain.enums import RunStatus


def published_recommendation_counts(db: Session, run_ids: list[uuid.UUID]) -> dict[uuid.UUID, int]:
    if not run_ids:
        return {}
    rows = (
        db.query(RecommendationCandidate.run_id, func.count())
        .filter(
            RecommendationCandidate.run_id.in_(run_ids),
            RecommendationCandidate.status == "published",
        )
        .group_by(RecommendationCandidate.run_id)
        .all()
    )
    return {run_id: int(count) for run_id, count in rows}


def _candidate_to_response(candidate: RecommendationCandidate, source_docs) -> dict:
    scores = candidate.scores or {}
    sota = scores.get("_sota") if isinstance(scores.get("_sota"), dict) else {}
    validation_issues = scores.get("_validation_issues")
    if not isinstance(validation_issues, list):
        validation_issues = scores.get("_critic_issues") if isinstance(scores.get("_critic_issues"), list) else None

    return RecommendationResponse(
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
        estimated_cost_usd=float(usage["estimated_cost_usd"]),
        created_at=run.created_at,
        started_at=run.started_at,
        finished_at=run.finished_at,
        recommendation_count=rec_count,
        topics=list((run.input or {}).get("topics") or []),
        usage=usage,
    ).model_dump(mode="json")


def run_events_payload(db: Session, run_id: uuid.UUID, run_status: str) -> list[dict]:
    events = db.query(RecommendationRunEvent).filter_by(run_id=run_id).order_by(RecommendationRunEvent.created_at).all()
    return format_events_for_user(events, run_status)


def run_stream_payload(db: Session, run: RecommendationRun) -> dict:
    return {
        "run": run_detail_payload(db, run),
        "events": run_events_payload(db, run.id, run.status),
    }


def run_sources_payload(db: Session, run_id: uuid.UUID) -> list[dict]:
    return serialize_source_documents(get_run_source_documents(db, run_id))


def run_recommendations_payload(
    db: Session,
    run_id: uuid.UUID,
    *,
    include_refinement: bool = False,
) -> list[dict]:
    query = db.query(RecommendationCandidate).filter_by(run_id=run_id)
    if not include_refinement:
        query = query.filter_by(status="published")
    candidates = query.all()
    candidates.sort(
        key=lambda c: float(c.final_score) if c.final_score is not None else float("-inf"),
        reverse=True,
    )
    source_docs = get_run_source_documents(db, run_id)
    return [_candidate_to_response(candidate, source_docs) for candidate in candidates]


def run_summaries_payload(db: Session, user_id: uuid.UUID, limit: int) -> list[dict]:
    runs = (
        db.query(RecommendationRun)
        .filter_by(user_id=str(user_id))
        .order_by(RecommendationRun.created_at.desc())
        .limit(min(limit, 100))
        .all()
    )
    completed_ids = [run.id for run in runs if run.status == RunStatus.COMPLETED]
    rec_counts = published_recommendation_counts(db, completed_ids)

    summaries: list[RunSummaryResponse] = []
    for run in runs:
        rec_count = rec_counts.get(run.id, 0) if run.status == RunStatus.COMPLETED else 0
        summaries.append(
            RunSummaryResponse(
                id=run.id,
                status=run.status,
                progress=run.progress,
                mode=run.mode,
                created_at=run.created_at,
                finished_at=run.finished_at,
                topics=list((run.input or {}).get("topics") or []),
                recommendation_count=rec_count,
            )
        )
    return [item.model_dump(mode="json") for item in summaries]
