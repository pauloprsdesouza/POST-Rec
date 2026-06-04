"""SOTA quality metrics for validation dashboard."""

from __future__ import annotations

from sqlalchemy.orm import Session

from apps.api.models import RecommendationCandidate


def compute_sota_quality_metrics(db: Session) -> dict[str, float]:
    candidates = db.query(RecommendationCandidate).all()
    if not candidates:
        return {
            "sota_anchor_rate": 0.0,
            "refinement_rate": 0.0,
            "avg_novelty_verified": 0.0,
            "avg_sota_fit": 0.0,
        }

    with_sota_anchor = 0
    needs_refinement = 0
    novelty_values: list[float] = []
    sota_fit_values: list[float] = []

    for candidate in candidates:
        if candidate.status == "needs_refinement":
            needs_refinement += 1

        scores = candidate.scores or {}
        sota = scores.get("_sota") if isinstance(scores.get("_sota"), dict) else {}
        anchors = sota.get("sota_anchors") or []
        if anchors:
            with_sota_anchor += 1

        if scores.get("novelty_verified") is not None:
            novelty_values.append(float(scores["novelty_verified"]))
        if scores.get("sota_fit") is not None:
            sota_fit_values.append(float(scores["sota_fit"]))

    total = len(candidates)
    return {
        "sota_anchor_rate": with_sota_anchor / total,
        "refinement_rate": needs_refinement / total,
        "avg_novelty_verified": sum(novelty_values) / len(novelty_values) if novelty_values else 0.0,
        "avg_sota_fit": sum(sota_fit_values) / len(sota_fit_values) if sota_fit_values else 0.0,
    }
