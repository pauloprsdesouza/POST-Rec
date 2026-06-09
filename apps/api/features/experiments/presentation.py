"""Blind presentation helpers — hide algorithm variant from API consumers."""

from __future__ import annotations

import copy
import re
from typing import Any

from apps.api.features.experiments.assignment import PRESENTATION_BLIND, PRESENTATION_STANDARD

_BLIND_EVENT_REPLACEMENTS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"\bfacet(?:s|-grounded|-level)?\b", re.I), "verification"),
    (re.compile(r"\bFGGV\b", re.I), "verification"),
    (re.compile(r"\bgap matrix\b", re.I), "literature analysis"),
    (re.compile(r"\blandscape\b", re.I), "literature review"),
    (re.compile(r"\bfacet critic\b", re.I), "quality review"),
    (re.compile(r"\bFNI\b", re.I), "novelty score"),
    (re.compile(r"\bGFA\b", re.I), "alignment score"),
    (re.compile(r"\bFDS\b", re.I), "diversity selection"),
)

_FGGV_ONLY_RECOMMENDATION_FIELDS = frozenset(
    {
        "facet_novelty_index",
        "gap_alignment_score",
        "fggv_score",
        "facet_deltas",
        "aligned_gaps",
    }
)

_SCORE_KEYS_TO_STRIP = frozenset(
    {
        "_fggv",
        "false_novel_facet_count",
        "facet_novelty_index",
        "gap_alignment_score",
        "fggv_score",
    }
)


def is_blind_run(run: Any) -> bool:
    profile = getattr(run, "presentation_profile", PRESENTATION_STANDARD)
    return profile == PRESENTATION_BLIND and bool(getattr(run, "experiment_id", None))


def sanitize_event_message(message: str) -> str:
    text = message or ""
    for pattern, replacement in _BLIND_EVENT_REPLACEMENTS:
        text = pattern.sub(replacement, text)
    return text


def blind_event_payload(event: dict[str, Any]) -> dict[str, Any]:
    payload = dict(event)
    payload["message"] = sanitize_event_message(str(payload.get("message") or ""))
    return payload


def blind_recommendation_payload(payload: dict[str, Any]) -> dict[str, Any]:
    sanitized = copy.deepcopy(payload)
    for field in _FGGV_ONLY_RECOMMENDATION_FIELDS:
        sanitized.pop(field, None)

    scores = sanitized.get("scores")
    if isinstance(scores, dict):
        sanitized["scores"] = {key: value for key, value in scores.items() if key not in _SCORE_KEYS_TO_STRIP}
        if not sanitized["scores"]:
            sanitized["scores"] = None

    return sanitized


def blind_run_detail_payload(payload: dict[str, Any]) -> dict[str, Any]:
    sanitized = dict(payload)
    sanitized.pop("mode", None)
    sanitized["presentation_profile"] = PRESENTATION_BLIND
    sanitized["usage"] = None
    sanitized["estimated_cost_usd"] = 0.0
    return sanitized


def blind_run_summary_payload(payload: dict[str, Any]) -> dict[str, Any]:
    sanitized = dict(payload)
    sanitized.pop("mode", None)
    sanitized["presentation_profile"] = PRESENTATION_BLIND
    return sanitized
