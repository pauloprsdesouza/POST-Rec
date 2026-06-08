"""Rank correlation helpers for evaluation."""

from __future__ import annotations

from packages.postrec_core.evaluation.expert_labels import spearman_rho


def _rank(values: list[float]) -> list[float]:
    n = len(values)
    order = sorted(range(n), key=lambda i: values[i])
    ranks = [0.0] * n
    i = 0
    while i < n:
        j = i
        while j + 1 < n and values[order[j + 1]] == values[order[i]]:
            j += 1
        avg_rank = (i + j + 2) / 2.0
        for k in range(i, j + 1):
            ranks[order[k]] = avg_rank
        i = j + 1
    return ranks


def kendall_tau(x: list[float], y: list[float]) -> float | None:
    """Lightweight Kendall tau-b (no scipy dependency)."""
    if len(x) != len(y) or len(x) < 2:
        return None
    n = len(x)
    concordant = 0
    discordant = 0
    for i in range(n):
        for j in range(i + 1, n):
            sign_x = x[i] - x[j]
            sign_y = y[i] - y[j]
            product = sign_x * sign_y
            if product > 0:
                concordant += 1
            elif product < 0:
                discordant += 1
    denom = concordant + discordant
    if denom == 0:
        return None
    return round((concordant - discordant) / denom, 4)


def pearson_r(x: list[float], y: list[float]) -> float | None:
    if len(x) != len(y) or len(x) < 2:
        return None
    n = len(x)
    mean_x = sum(x) / n
    mean_y = sum(y) / n
    num = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n))
    den_x = sum((x[i] - mean_x) ** 2 for i in range(n)) ** 0.5
    den_y = sum((y[i] - mean_y) ** 2 for i in range(n)) ** 0.5
    if den_x == 0 or den_y == 0:
        return None
    return round(num / (den_x * den_y), 4)


def rank_correlation(system_ranks: list[float], user_ranks: list[float]) -> dict[str, float | None]:
    return {
        "spearman_rho": spearman_rho(system_ranks, user_ranks),
        "kendall_tau": kendall_tau(system_ranks, user_ranks),
        "pearson_r": pearson_r(system_ranks, user_ranks),
    }
