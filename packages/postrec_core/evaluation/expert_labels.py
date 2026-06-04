"""Expert label schema and correlation helpers for human studies."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def spearman_rho(x: list[float], y: list[float]) -> float | None:
    """Lightweight Spearman correlation (no scipy dependency)."""
    if len(x) != len(y) or len(x) < 3:
        return None
    n = len(x)

    def rank(values: list[float]) -> list[float]:
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

    rx = rank(x)
    ry = rank(y)
    mean_x = sum(rx) / n
    mean_y = sum(ry) / n
    num = sum((rx[i] - mean_x) * (ry[i] - mean_y) for i in range(n))
    den_x = sum((rx[i] - mean_x) ** 2 for i in range(n)) ** 0.5
    den_y = sum((ry[i] - mean_y) ** 2 for i in range(n)) ** 0.5
    if den_x == 0 or den_y == 0:
        return None
    return round(num / (den_x * den_y), 4)


def load_expert_labels(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload.get("ratings") or []


def correlate_fni_with_expert_originality(labels: list[dict[str, Any]]) -> dict[str, Any]:
    """RQ4: correlate system FNI with blind expert originality (1–7)."""
    fni_values: list[float] = []
    expert_values: list[float] = []
    for row in labels:
        fni = row.get("facet_novelty_index")
        originality = row.get("expert_originality")
        if isinstance(fni, (int, float)) and isinstance(originality, (int, float)):
            fni_values.append(float(fni))
            expert_values.append(float(originality))
    rho = spearman_rho(fni_values, expert_values)
    return {
        "n": len(fni_values),
        "spearman_rho": rho,
        "target_rho": 0.4,
        "meets_target": rho is not None and rho >= 0.4,
    }
