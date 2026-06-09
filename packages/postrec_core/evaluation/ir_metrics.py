"""Information retrieval metrics for ranked recommendation lists."""

from __future__ import annotations

import math
from collections.abc import Sequence


def dcg_at_k(relevances: Sequence[float], k: int | None = None) -> float:
    if not relevances:
        return 0.0
    items = list(relevances[:k] if k is not None else relevances)
    return sum(rel / math.log2(i + 2) for i, rel in enumerate(items))


def ndcg_at_k(relevances: Sequence[float], k: int | None = None) -> float:
    if not relevances:
        return 0.0
    k = k or len(relevances)
    ideal = sorted(relevances, reverse=True)
    idcg = dcg_at_k(ideal, k)
    if idcg <= 0:
        return 0.0
    return round(dcg_at_k(relevances, k) / idcg, 4)


def average_precision(relevances: Sequence[float], threshold: float = 0.5) -> float:
    if not relevances:
        return 0.0
    hits = 0
    precision_sum = 0.0
    for index, rel in enumerate(relevances, start=1):
        if rel >= threshold:
            hits += 1
            precision_sum += hits / index
    if hits == 0:
        return 0.0
    return round(precision_sum / hits, 4)


def map_at_k(lists: Sequence[Sequence[float]], k: int | None = None, threshold: float = 0.5) -> float:
    if not lists:
        return 0.0
    scores = []
    for relevances in lists:
        truncated = list(relevances[:k] if k is not None else relevances)
        scores.append(average_precision(truncated, threshold=threshold))
    return round(sum(scores) / len(scores), 4)


def mrr(lists: Sequence[Sequence[float]], threshold: float = 0.5) -> float:
    if not lists:
        return 0.0
    reciprocals: list[float] = []
    for relevances in lists:
        rank = next((i + 1 for i, rel in enumerate(relevances) if rel >= threshold), None)
        reciprocals.append(1.0 / rank if rank else 0.0)
    return round(sum(reciprocals) / len(reciprocals), 4)


def precision_at_k(relevances: Sequence[float], k: int, threshold: float = 0.5) -> float:
    if not relevances or k <= 0:
        return 0.0
    top = list(relevances[:k])
    hits = sum(1 for rel in top if rel >= threshold)
    return round(hits / k, 4)


def recall_at_k(relevances: Sequence[float], k: int, threshold: float = 0.5) -> float:
    if not relevances:
        return 0.0
    total_relevant = sum(1 for rel in relevances if rel >= threshold)
    if total_relevant == 0:
        return 0.0
    top = list(relevances[:k])
    hits = sum(1 for rel in top if rel >= threshold)
    return round(hits / total_relevant, 4)


def hit_at_k(relevances: Sequence[float], k: int, threshold: float = 0.5) -> float:
    if not relevances or k <= 0:
        return 0.0
    return 1.0 if any(rel >= threshold for rel in relevances[:k]) else 0.0


def mean_metric(values: Sequence[float]) -> float:
    if not values:
        return 0.0
    return round(sum(values) / len(values), 4)


def err_at_k(relevances: Sequence[float], k: int | None = None) -> float:
    """Expected Reciprocal Rank with graded relevance (Chapelle et al., WSDM 2009)."""
    if not relevances:
        return 0.0
    items = list(relevances[:k] if k is not None else relevances)
    err = 0.0
    survival = 1.0
    for index, rel in enumerate(items, start=1):
        grade = max(0.0, min(1.0, float(rel)))
        err += survival * grade / index
        survival *= 1.0 - grade
    return round(err, 4)


def success_at_k(relevances: Sequence[float], k: int, threshold: float = 0.5) -> float:
    """Fraction of lists with at least one relevant item in top-k (alias for hit rate)."""
    return hit_at_k(relevances, k, threshold=threshold)
