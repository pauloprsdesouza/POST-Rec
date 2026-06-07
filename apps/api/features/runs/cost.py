"""Aggregate LLM usage cost onto recommendation runs."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from apps.api.shared.models import LLMUsage, RecommendationRun


def get_run_estimated_cost(db: Session, run: RecommendationRun) -> float:
    total = db.query(func.coalesce(func.sum(LLMUsage.estimated_cost_usd), 0)).filter(LLMUsage.run_id == run.id).scalar()
    aggregate = float(total or 0)
    stored = float(run.estimated_cost_usd or 0)
    return max(aggregate, stored)


def get_run_usage_summary(
    db: Session,
    run: RecommendationRun,
    *,
    recommendation_count: int = 0,
) -> dict[str, Any]:
    rows = db.query(LLMUsage).filter(LLMUsage.run_id == run.id).order_by(LLMUsage.created_at).all()

    merged: dict[str, dict[str, Any]] = {}
    for row in rows:
        key = f"{row.operation}:{row.model}"
        input_tokens = int(row.input_tokens or 0)
        output_tokens = int(row.output_tokens or 0)
        cost = float(row.estimated_cost_usd or 0)
        if key not in merged:
            merged[key] = {
                "operation": row.operation,
                "model": row.model,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": input_tokens + output_tokens,
                "estimated_cost_usd": cost,
            }
            continue

        bucket = merged[key]
        bucket["input_tokens"] += input_tokens
        bucket["output_tokens"] += output_tokens
        bucket["total_tokens"] += input_tokens + output_tokens
        bucket["estimated_cost_usd"] += cost

    lines = sorted(
        merged.values(),
        key=lambda item: float(item["estimated_cost_usd"]),
        reverse=True,
    )
    input_tokens = sum(line["input_tokens"] for line in lines)
    output_tokens = sum(line["output_tokens"] for line in lines)
    aggregate = sum(float(row.estimated_cost_usd or 0) for row in rows)
    total_cost = max(aggregate, float(run.estimated_cost_usd or 0))

    avg_per_recommendation = total_cost / recommendation_count if recommendation_count > 0 else None

    return {
        "estimated_cost_usd": total_cost,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": input_tokens + output_tokens,
        "estimated_cost_per_recommendation_usd": avg_per_recommendation,
        "lines": lines,
    }


def add_usage_cost(db: Session, run_id: str | uuid.UUID, cost: float) -> None:
    if cost <= 0:
        return

    run_uuid = run_id if isinstance(run_id, uuid.UUID) else uuid.UUID(str(run_id))
    run = db.query(RecommendationRun).filter_by(id=run_uuid).first()
    if run is None:
        return

    run.estimated_cost_usd = float(run.estimated_cost_usd or 0) + cost
