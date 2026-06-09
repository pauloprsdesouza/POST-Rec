"""Qualis estrato → normalized score mapping."""

from __future__ import annotations

from apps.api.features.qualis.periods import DEFAULT_PERIOD_LABEL, period_rank_from_label

# Higher estratos receive higher scores in [0, 1]. A1 is top-tier CAPES classification.
DEFAULT_ESTRATO_SCORES: dict[str, float] = {
    "A1": 1.0,
    "A2": 0.89,
    "A3": 0.78,
    "A4": 0.67,
    "B1": 0.56,
    "B2": 0.44,
    "B3": 0.33,
    "B4": 0.22,
    "C": 0.11,
}

ESTRATO_RANK: dict[str, int] = {
    "A1": 9,
    "A2": 8,
    "A3": 7,
    "A4": 6,
    "B1": 5,
    "B2": 4,
    "B3": 3,
    "B4": 2,
    "C": 1,
}


def normalize_estrato(estrato: str | None) -> str | None:
    if not estrato:
        return None
    cleaned = estrato.strip().upper()
    return cleaned if cleaned in DEFAULT_ESTRATO_SCORES else None


def estrato_score(estrato: str | None, *, weights: dict[str, float] | None = None) -> float:
    """Return a normalized Qualis score in [0, 1] for the given estrato."""
    normalized = normalize_estrato(estrato)
    if not normalized:
        return 0.0
    table = weights or DEFAULT_ESTRATO_SCORES
    return table.get(normalized, 0.0)


def best_estrato(estratos: set[str]) -> str | None:
    """Pick the highest estrato when multiple classifications exist."""
    valid = [e for e in estratos if normalize_estrato(e)]
    if not valid:
        return None
    return max(valid, key=lambda e: ESTRATO_RANK[normalize_estrato(e) or "C"])


DEFAULT_QUALIS_PERIOD = DEFAULT_PERIOD_LABEL


def period_rank(period: str | None) -> int:
    """Higher rank means more recent; prefers parsed start_year over legacy map."""
    rank = period_rank_from_label(period)
    if rank > 0:
        return rank
    # Legacy fallback for unknown label formats.
    legacy = {"2021-2024": 2021, "2017-2020": 2017}
    if not period:
        return 0
    return legacy.get(period.strip(), 0)


def resolve_qualis_classification(
    classifications: list[tuple[str, str]],
) -> tuple[str | None, str | None]:
    """Pick estrato using period recency, then best estrato within the winning period."""
    valid = [
        (estrato, period)
        for estrato, period in classifications
        if normalize_estrato(estrato) and period_rank(period) > 0
    ]
    if not valid:
        return None, None

    by_period: dict[str, set[str]] = {}
    for estrato, period in valid:
        by_period.setdefault(period, set()).add(estrato)

    winning_period = max(by_period.keys(), key=period_rank)
    estrato = best_estrato(by_period[winning_period])
    return estrato, winning_period
