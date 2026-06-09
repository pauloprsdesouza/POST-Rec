"""Helpers for run dismissal and learned-topic cleanup."""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from apps.api.shared.models import RecommendationCandidate, RecommendationRun, UserResearchProfile

RETRYABLE_STATUSES = frozenset(
    {
        "failed",
        "cancelled",
        "cost_limit_exceeded",
        "failed_schema_validation",
    }
)

ACTIVE_RUN_STATUSES = frozenset(
    {
        "queued",
        "started",
        "searching_papers",
        "normalizing_documents",
        "deduplicating_documents",
        "generating_embeddings",
        "ranking_candidates",
        "generating_recommendations",
        "validating_output",
    }
)


def is_run_retryable(status: str, published_recommendation_count: int) -> bool:
    if status in RETRYABLE_STATUSES:
        return True
    return status == "completed" and published_recommendation_count == 0


def is_run_cancellable(status: str) -> bool:
    return status in ACTIVE_RUN_STATUSES


def _normalize_topic(value: str) -> str:
    return value.strip().lower()


def run_cleanup_signals(run: RecommendationRun, candidates: list[RecommendationCandidate]) -> set[str]:
    signals: set[str] = set()
    for topic in (run.input or {}).get("topics") or []:
        if isinstance(topic, str) and topic.strip():
            signals.add(topic.strip())
    for candidate in candidates:
        if candidate.technique_name and candidate.technique_name.strip():
            signals.add(candidate.technique_name.strip())
        if candidate.title and candidate.title.strip():
            signals.add(candidate.title.strip()[:120])
    return signals


def learned_topics_matching_run(
    profile: UserResearchProfile | None,
    run: RecommendationRun,
    candidates: list[RecommendationCandidate],
) -> list[str]:
    if not profile:
        return []
    learned = [topic.strip() for topic in (profile.learned_topics or []) if topic and topic.strip()]
    if not learned:
        return []

    signals = {_normalize_topic(value) for value in run_cleanup_signals(run, candidates)}
    if not signals:
        return []

    matched: list[str] = []
    seen: set[str] = set()
    for topic in learned:
        key = _normalize_topic(topic)
        if key in signals and key not in seen:
            seen.add(key)
            matched.append(topic)
    return sorted(matched, key=str.lower)


def learned_topics_for_run_cleanup(
    db: Session,
    user_id: uuid.UUID,
    run: RecommendationRun,
) -> list[str]:
    profile = db.query(UserResearchProfile).filter_by(user_id=user_id).first()
    candidates = db.query(RecommendationCandidate).filter_by(run_id=run.id).all()
    return learned_topics_matching_run(profile, run, candidates)
