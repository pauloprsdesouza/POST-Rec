"""Quota selection balancing recent SOTA and seminal papers."""

from __future__ import annotations

from typing import Any

from packages.postrec_core.retrieval.paper_tier import (
    PAPER_TIER_SEMINAL,
    PAPER_TIER_SOTA_RECENT,
)


def apply_tier_quotas(
    papers: list[dict[str, Any]],
    max_papers: int,
    *,
    sota_quota: float = 0.6,
) -> list[dict[str, Any]]:
    """Select up to ``max_papers`` with a SOTA-recent quota."""
    if max_papers <= 0 or not papers:
        return []

    sota_target = max(1, int(round(max_papers * sota_quota)))
    seminal_target = max(0, max_papers - sota_target)

    sota_recent = [p for p in papers if p.get("tier") == PAPER_TIER_SOTA_RECENT]
    seminal = [p for p in papers if p.get("tier") == PAPER_TIER_SEMINAL]
    other = [p for p in papers if p.get("tier") not in (PAPER_TIER_SOTA_RECENT, PAPER_TIER_SEMINAL)]

    selected: list[dict[str, Any]] = []
    selected.extend(sota_recent[:sota_target])
    selected.extend(seminal[:seminal_target])

    remaining = max_papers - len(selected)
    if remaining > 0:
        pool = sota_recent[sota_target:] + seminal[seminal_target:] + other
        selected.extend(pool[:remaining])

    return selected[:max_papers]
