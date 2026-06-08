"""Human validation metrics and rating aggregates."""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

LIKERT_DIMENSIONS = (
    "relevance_score",
    "originality_score",
    "clarity_score",
    "feasibility_score",
    "trust_score",
    "usefulness_score",
)


@dataclass(frozen=True)
class DimensionStats:
    dimension: str
    mean: float
    std: float
    min: float
    max: float
    count: int
    distribution: dict[str, int]


def _std(values: Sequence[float]) -> float:
    if len(values) < 2:
        return 0.0
    mean = sum(values) / len(values)
    variance = sum((v - mean) ** 2 for v in values) / (len(values) - 1)
    return math.sqrt(variance)


def dimension_statistics(rows: Sequence[dict[str, Any]], dimension: str) -> DimensionStats | None:
    values = [float(row[dimension]) for row in rows if row.get(dimension) is not None]
    if not values:
        return None
    distribution = {str(score): 0 for score in range(1, 6)}
    for value in values:
        key = str(int(round(value)))
        if key in distribution:
            distribution[key] += 1
    return DimensionStats(
        dimension=dimension,
        mean=round(sum(values) / len(values), 4),
        std=round(_std(values), 4),
        min=round(min(values), 4),
        max=round(max(values), 4),
        count=len(values),
        distribution=distribution,
    )


def all_dimension_statistics(rows: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for dimension in LIKERT_DIMENSIONS:
        stats = dimension_statistics(rows, dimension)
        if stats:
            results.append(
                {
                    "dimension": dimension.replace("_score", ""),
                    "mean": stats.mean,
                    "std": stats.std,
                    "min": stats.min,
                    "max": stats.max,
                    "count": stats.count,
                    "distribution": stats.distribution,
                }
            )
    return results


def cronbach_alpha(rows: Sequence[dict[str, Any]], dimensions: Sequence[str] = LIKERT_DIMENSIONS) -> float | None:
    """Cronbach's alpha for internal consistency across Likert dimensions."""
    matrix: list[list[float]] = []
    for row in rows:
        values = [row.get(dim) for dim in dimensions]
        if any(v is None for v in values):
            continue
        matrix.append([float(v) for v in values])
    k = len(dimensions)
    n = len(matrix)
    if n < 2 or k < 2:
        return None

    col_vars = []
    for col in range(k):
        column = [row[col] for row in matrix]
        mean = sum(column) / n
        col_vars.append(sum((v - mean) ** 2 for v in column) / (n - 1))

    row_totals = [sum(row) for row in matrix]
    total_mean = sum(row_totals) / n
    total_var = sum((t - total_mean) ** 2 for t in row_totals) / (n - 1)
    if total_var <= 0:
        return None

    alpha = (k / (k - 1)) * (1 - sum(col_vars) / total_var)
    return round(max(0.0, min(1.0, alpha)), 4)


def rate(rows: Sequence[dict[str, Any]], predicate) -> float:
    if not rows:
        return 0.0
    return round(sum(1 for row in rows if predicate(row)) / len(rows), 4)


def mean_field(rows: Sequence[dict[str, Any]], field: str) -> float:
    values = [float(row[field]) for row in rows if row.get(field) is not None]
    if not values:
        return 0.0
    return round(sum(values) / len(values), 4)
