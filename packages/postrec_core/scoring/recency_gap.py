"""Recency gap signal for novelty verification."""

from __future__ import annotations

from typing import Any

from packages.postrec_core.retrieval.paper_tier import current_year


def min_year_distance(proposal_methods: list[str], anchor_years: list[int]) -> float:
    """Higher is better: proposal methods farther from anchor years (normalized)."""
    if not anchor_years:
        return 0.5
    avg_anchor_year = sum(anchor_years) / len(anchor_years)
    year_gap = max(0.0, current_year() - avg_anchor_year)
    method_bonus = min(1.0, len(proposal_methods) / 3.0)
    return max(0.0, min(1.0, (year_gap / 5.0) * 0.6 + method_bonus * 0.4))


def compute_recency_gap(
    recommendation: dict[str, Any],
    papers: list[dict[str, Any]],
) -> float:
    """Estimate whether a proposal extends recent work vs stale baselines."""
    anchors = recommendation.get("sota_anchors") or recommendation.get("evidence_papers") or []
    paper_by_title = {str(p.get("title", "")).lower(): p for p in papers if p.get("title")}

    anchor_years: list[int] = []
    for anchor in anchors:
        if not isinstance(anchor, dict):
            continue
        title = str(anchor.get("title") or "").lower()
        paper = paper_by_title.get(title)
        year = anchor.get("year") or (paper.get("year") if paper else None)
        if isinstance(year, int):
            anchor_years.append(year)

    methods_text = " ".join(
        str(part)
        for part in (
            recommendation.get("proposed_method"),
            recommendation.get("technique_name"),
            recommendation.get("novelty_delta"),
        )
        if part
    ).lower()

    method_hints = [token for token in methods_text.split() if len(token) > 4][:8]
    return min_year_distance(method_hints, anchor_years)
