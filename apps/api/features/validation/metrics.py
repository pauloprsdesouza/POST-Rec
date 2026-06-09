"""SOTA quality metrics for validation dashboard."""

from __future__ import annotations

from sqlalchemy import Float, cast, func
from sqlalchemy.orm import Session

from apps.api.shared.models import RecommendationCandidate


def compute_sota_quality_metrics(db: Session) -> dict[str, float]:
    total = db.query(func.count(RecommendationCandidate.id)).scalar() or 0
    if not total:
        return {
            "sota_anchor_rate": 0.0,
            "refinement_rate": 0.0,
            "avg_novelty_verified": 0.0,
            "avg_sota_fit": 0.0,
        }

    needs_refinement = (
        db.query(func.count(RecommendationCandidate.id))
        .filter(RecommendationCandidate.status == "needs_refinement")
        .scalar()
        or 0
    )

    novelty_avg = (
        db.query(func.avg(cast(RecommendationCandidate.scores["novelty_verified"].astext, Float)))
        .filter(RecommendationCandidate.scores["novelty_verified"].astext.isnot(None))
        .scalar()
    )
    sota_fit_avg = (
        db.query(func.avg(cast(RecommendationCandidate.scores["sota_fit"].astext, Float)))
        .filter(RecommendationCandidate.scores["sota_fit"].astext.isnot(None))
        .scalar()
    )

    with_sota_anchor = 0
    for (scores,) in db.query(RecommendationCandidate.scores).filter(RecommendationCandidate.scores.isnot(None)):
        if not isinstance(scores, dict):
            continue
        sota = scores.get("_sota") if isinstance(scores.get("_sota"), dict) else {}
        anchors = sota.get("sota_anchors") or []
        if anchors:
            with_sota_anchor += 1

    return {
        "sota_anchor_rate": with_sota_anchor / total,
        "refinement_rate": needs_refinement / total,
        "avg_novelty_verified": float(novelty_avg or 0.0),
        "avg_sota_fit": float(sota_fit_avg or 0.0),
    }
