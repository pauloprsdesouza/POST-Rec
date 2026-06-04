"""Facet Diversity Selection (FDS) via token-level MMR."""

from __future__ import annotations

from typing import Any

from packages.postrec_core.scoring.facet_grounded_ranking import facet_token_diversity


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def average_pairwise_facet_diversity(recommendations: list[dict[str, Any]]) -> float:
    """Mean pairwise Jaccard distance on facet tokens (RQ3 metric)."""
    if len(recommendations) < 2:
        return 0.0

    def _jaccard(a: set[str], b: set[str]) -> float:
        if not a or not b:
            return 0.0
        return len(a & b) / len(a | b)

    tokens = [facet_token_diversity(rec) for rec in recommendations]
    distances: list[float] = []
    for i in range(len(tokens)):
        for j in range(i + 1, len(tokens)):
            distances.append(1.0 - _jaccard(tokens[i], tokens[j]))
    return round(sum(distances) / len(distances), 4) if distances else 0.0


def select_facet_diverse(
    recommendations: list[dict[str, Any]],
    *,
    max_items: int,
    lambda_param: float = 0.7,
) -> list[dict[str, Any]]:
    """Maximal Marginal Relevance on facet token sets."""
    if max_items <= 0 or not recommendations:
        return []

    remaining = list(recommendations)
    selected: list[dict[str, Any]] = []

    def score(rec: dict[str, Any]) -> float:
        return float(rec.get("final_score") or (rec.get("scores") or {}).get("fggv_score") or 0.0)

    while remaining and len(selected) < max_items:
        best_idx = 0
        best_mmr = float("-inf")
        for idx, candidate in enumerate(remaining):
            relevance = score(candidate) / 100.0
            cand_tokens = facet_token_diversity(candidate)
            max_sim = 0.0
            for chosen in selected:
                max_sim = max(max_sim, _jaccard(cand_tokens, facet_token_diversity(chosen)))
            mmr = lambda_param * relevance - (1.0 - lambda_param) * max_sim
            if mmr > best_mmr:
                best_mmr = mmr
                best_idx = idx
        selected.append(remaining.pop(best_idx))

    return selected
