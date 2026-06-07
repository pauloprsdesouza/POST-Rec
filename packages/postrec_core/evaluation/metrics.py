"""Evaluation metrics for baseline vs FGGV comparison."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class DiscriminabilityResult:
    good_mean: float
    weak_mean: float
    delta: float
    separation_ratio: float


def mean_score(scores: list[float]) -> float:
    if not scores:
        return 0.0
    return sum(scores) / len(scores)


def discriminability(good_scores: list[float], weak_scores: list[float]) -> DiscriminabilityResult:
    good_mean = mean_score(good_scores)
    weak_mean = mean_score(weak_scores)
    delta = good_mean - weak_mean
    separation = delta / max(weak_mean, 1e-6) if weak_mean > 0 else delta
    return DiscriminabilityResult(
        good_mean=round(good_mean, 4),
        weak_mean=round(weak_mean, 4),
        delta=round(delta, 4),
        separation_ratio=round(separation, 4),
    )


def anchor_hit_rate(recommendations: list[dict[str, Any]], valid_titles: set[str]) -> float:
    if not recommendations:
        return 0.0
    hits = 0
    for rec in recommendations:
        anchors = rec.get("sota_anchors") or []
        for anchor in anchors:
            if isinstance(anchor, dict) and str(anchor.get("title", "")).lower() in valid_titles:
                hits += 1
                break
    return round(hits / len(recommendations), 4)


def refinement_rate(recommendations: list[dict[str, Any]]) -> float:
    if not recommendations:
        return 0.0
    refined = sum(1 for rec in recommendations if rec.get("_publication_status") == "needs_refinement")
    return round(refined / len(recommendations), 4)
