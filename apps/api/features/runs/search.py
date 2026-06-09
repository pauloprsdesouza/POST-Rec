"""Full-text search across runs and published recommendation ideas."""

from __future__ import annotations

import re
import uuid

from sqlalchemy import Text, and_, cast, desc, func, or_
from sqlalchemy.orm import Session

from apps.api.features.experiments.presentation import blind_run_summary_payload, is_blind_run
from apps.api.features.runs.query import (
    feedback_counts_by_run,
    published_recommendation_counts,
)
from apps.api.shared.models import RecommendationCandidate, RecommendationRun
from apps.api.shared.schemas.common import RunSummaryResponse
from packages.postrec_core.domain.enums import RunStatus

_TOKEN_RE = re.compile(r"[\w\u00c0-\u024f]+", re.UNICODE)
_MIN_TOKEN_LEN = 2
_MAX_TOKENS = 8


def normalize_search_query(query: str) -> list[str]:
    tokens = [token.lower() for token in _TOKEN_RE.findall(query.strip()) if len(token) >= _MIN_TOKEN_LEN]
    return tokens[:_MAX_TOKENS]


def _candidate_search_blob():
    text_fields = (
        RecommendationCandidate.title,
        RecommendationCandidate.technique_name,
        RecommendationCandidate.research_gap,
        RecommendationCandidate.research_question,
        RecommendationCandidate.hypothesis,
        RecommendationCandidate.proposed_method,
        RecommendationCandidate.related_work_summary,
        RecommendationCandidate.expected_contribution,
        RecommendationCandidate.experimental_plan,
        RecommendationCandidate.confidence_level,
    )
    json_fields = (
        RecommendationCandidate.datasets,
        RecommendationCandidate.evaluation_metrics,
        RecommendationCandidate.risks,
        RecommendationCandidate.evidence_papers,
        RecommendationCandidate.scores,
    )
    parts = [func.coalesce(field, "") for field in text_fields]
    parts.extend(cast(field, Text) for field in json_fields)
    return func.lower(func.concat_ws(" ", *parts))


def _run_search_blob():
    return func.lower(
        func.concat_ws(
            " ",
            cast(RecommendationRun.input, Text),
            cast(RecommendationRun.mode, Text),
            cast(RecommendationRun.status, Text),
            func.coalesce(cast(RecommendationRun.current_step, Text), ""),
            func.coalesce(RecommendationRun.error_message, ""),
        )
    )


def _token_filters(blob, tokens: list[str]):
    return [blob.like(f"%{token}%") for token in tokens]


def _best_snippet(*values: str | None, max_len: int = 140) -> str | None:
    for value in values:
        if not value:
            continue
        cleaned = " ".join(value.split())
        if len(cleaned) <= max_len:
            return cleaned
        return f"{cleaned[: max_len - 1]}…"
    return None


def search_run_summaries_payload(
    db: Session,
    user_id: uuid.UUID,
    query: str,
    limit: int,
) -> list[dict]:
    tokens = normalize_search_query(query)
    if not tokens:
        return []

    capped = min(limit, 100)
    candidate_blob = _candidate_search_blob()
    run_blob = _run_search_blob()
    token_match = or_(
        and_(*_token_filters(run_blob, tokens)),
        and_(*_token_filters(candidate_blob, tokens)),
    )

    matching_run_ids = [
        row[0]
        for row in (
            db.query(RecommendationRun.id)
            .outerjoin(
                RecommendationCandidate,
                (RecommendationCandidate.run_id == RecommendationRun.id)
                & (RecommendationCandidate.status == "published"),
            )
            .filter(RecommendationRun.user_id == user_id)
            .filter(token_match)
            .group_by(RecommendationRun.id)
            .order_by(desc(func.max(RecommendationRun.created_at)))
            .limit(capped)
            .all()
        )
    ]
    if not matching_run_ids:
        return []

    runs_by_id = {
        run.id: run for run in db.query(RecommendationRun).filter(RecommendationRun.id.in_(matching_run_ids)).all()
    }
    runs = [runs_by_id[run_id] for run_id in matching_run_ids if run_id in runs_by_id]
    run_ids = matching_run_ids
    completed_ids = [run.id for run in runs if run.status == RunStatus.COMPLETED]
    rec_counts = published_recommendation_counts(db, completed_ids)
    feedback_counts = feedback_counts_by_run(db, user_id, completed_ids)

    candidates = (
        db.query(RecommendationCandidate)
        .filter(
            RecommendationCandidate.run_id.in_(run_ids),
            RecommendationCandidate.status == "published",
        )
        .all()
    )
    candidates_by_run: dict[uuid.UUID, list[RecommendationCandidate]] = {}
    for candidate in candidates:
        candidates_by_run.setdefault(candidate.run_id, []).append(candidate)

    summaries: list[dict] = []
    for run in runs:
        rec_count = rec_counts.get(run.id, 0) if run.status == RunStatus.COMPLETED else 0
        feedback_count = feedback_counts.get(run.id, 0) if rec_count > 0 else 0
        run_candidates = candidates_by_run.get(run.id, [])

        match_count = 0
        snippet: str | None = None
        for candidate in run_candidates:
            haystack = " ".join(
                filter(
                    None,
                    [
                        candidate.title,
                        candidate.technique_name,
                        candidate.research_gap,
                        candidate.research_question,
                        candidate.hypothesis,
                        candidate.proposed_method,
                        candidate.related_work_summary,
                        candidate.expected_contribution,
                        candidate.experimental_plan,
                        str(candidate.datasets or ""),
                        str(candidate.risks or ""),
                        str(candidate.evidence_papers or ""),
                    ],
                )
            ).lower()
            if all(token in haystack for token in tokens):
                match_count += 1
                if snippet is None:
                    snippet = _best_snippet(
                        candidate.title,
                        candidate.research_question,
                        candidate.research_gap,
                        candidate.technique_name,
                    )

        if match_count == 0:
            topics = " ".join((run.input or {}).get("topics") or [])
            run_haystack = " ".join(
                filter(
                    None,
                    [
                        topics,
                        run.mode,
                        run.status,
                        str(run.current_step or ""),
                        run.error_message,
                    ],
                )
            ).lower()
            if all(token in run_haystack for token in tokens):
                match_count = 1
                snippet = _best_snippet(topics, run.error_message)

        summary = RunSummaryResponse(
            id=run.id,
            status=run.status,
            progress=run.progress,
            mode=run.mode,
            presentation_profile=run.presentation_profile or "standard",
            created_at=run.created_at,
            finished_at=run.finished_at,
            topics=list((run.input or {}).get("topics") or []),
            recommendation_count=rec_count,
            feedback_count=feedback_count,
            feedback_complete=rec_count > 0 and feedback_count >= rec_count,
            search_match_count=match_count or None,
            search_snippet=snippet,
        )
        payload = summary.model_dump(mode="json")
        if is_blind_run(run):
            payload = blind_run_summary_payload(payload)
        summaries.append(payload)

    summaries.sort(
        key=lambda item: (
            -(item.get("search_match_count") or 0),
            item.get("created_at") or "",
        ),
    )
    return summaries
