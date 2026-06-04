"""Verified ranking score computation."""

import json
from pathlib import Path
from typing import Any

from packages.postrec_core.domain.run_mode import RunMode
from packages.postrec_core.scoring.ranking_weights import RankingWeights, weights_for_mode

CALIBRATION_PATH = Path(__file__).resolve().parents[3] / "data" / "ranking_weights_calibrated.json"


def _load_calibrated_weights(mode: RunMode) -> RankingWeights | None:
    if not CALIBRATION_PATH.exists():
        return None
    try:
        payload = json.loads(CALIBRATION_PATH.read_text(encoding="utf-8"))
        mode_weights = payload.get("modes", {}).get(mode.value)
        if not isinstance(mode_weights, dict):
            return None
        return RankingWeights(**mode_weights)
    except (OSError, json.JSONDecodeError, TypeError):
        return None


def _normalize_dimension_scores(scores: dict[str, Any]) -> dict[str, float]:
    normalized: dict[str, float] = {}
    for key in (
        "relevance",
        "novelty",
        "evidence",
        "feasibility",
        "trend",
        "publication_potential",
        "strategic_fit",
    ):
        raw = scores.get(key)
        if isinstance(raw, (int, float)):
            value = float(raw)
            normalized[key] = value / 100.0 if value > 1.0 else value
    return normalized


def compute_verified_final_score(
    scores: dict[str, Any],
    *,
    sota_fit: float,
    novelty_verified: float,
    mode: RunMode | str = RunMode.QUICK,
) -> float:
    """Compute a 0–100 ranking score blending LLM dimensions and verified signals."""
    parsed_mode = mode if isinstance(mode, RunMode) else RunMode.parse(str(mode))
    weights: RankingWeights = _load_calibrated_weights(parsed_mode) or weights_for_mode(parsed_mode)
    dims = _normalize_dimension_scores(scores)

    weighted = (
        weights.relevance * dims.get("relevance", 0.0)
        + weights.novelty * dims.get("novelty", 0.0)
        + weights.evidence * dims.get("evidence", 0.0)
        + weights.feasibility * dims.get("feasibility", 0.0)
        + weights.trend * dims.get("trend", 0.0)
        + weights.publication_potential * dims.get("publication_potential", 0.0)
        + weights.strategic_fit * dims.get("strategic_fit", 0.0)
        + weights.sota_fit * max(0.0, min(1.0, sota_fit))
        + weights.novelty_verified * max(0.0, min(1.0, novelty_verified))
    )
    return round(max(0.0, min(100.0, weighted * 100.0)), 2)
