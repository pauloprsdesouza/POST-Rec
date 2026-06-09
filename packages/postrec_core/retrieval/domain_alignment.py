"""Backward-compatible wrappers for context alignment."""

from __future__ import annotations

from typing import Any

from packages.postrec_core.retrieval.context_alignment import (
    ContextAlignment,
    apply_context_alignment_to_score,
    compute_context_alignment,
)

DomainAlignment = ContextAlignment


def compute_domain_alignment(
    paper: dict[str, Any],
    research_area: str | None,
    *,
    topics: list[str] | None = None,
    learned_topics: list[str] | None = None,
    avoided_topics: list[str] | None = None,
) -> ContextAlignment:
    return compute_context_alignment(
        paper,
        research_area=research_area,
        topics=topics,
        learned_topics=learned_topics,
        avoided_topics=avoided_topics,
    )


def apply_domain_alignment_to_score(base_score: float, alignment: ContextAlignment) -> float:
    return apply_context_alignment_to_score(base_score, alignment)
