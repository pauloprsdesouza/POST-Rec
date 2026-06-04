"""Paper tier classification for SOTA-aware retrieval."""

from datetime import UTC, datetime
from typing import Any

PAPER_TIER_SOTA_RECENT = "sota_recent"
PAPER_TIER_SEMINAL = "seminal"
PAPER_TIER_PERIPHERAL = "peripheral"


def current_year() -> int:
    return datetime.now(UTC).year


def classify_paper_tier(
    paper: dict[str, Any],
    *,
    recent_years: int = 3,
    seminal_citation_threshold: int = 50,
) -> str:
    """Classify a paper as recent SOTA, seminal, or peripheral."""
    year = paper.get("year")
    citations = int(paper.get("citation_count") or 0)
    cutoff = current_year() - recent_years

    if isinstance(year, int) and year >= cutoff:
        return PAPER_TIER_SOTA_RECENT
    if citations >= seminal_citation_threshold:
        return PAPER_TIER_SEMINAL
    return PAPER_TIER_PERIPHERAL


def tag_paper_tiers(
    papers: list[dict[str, Any]],
    *,
    recent_years: int = 3,
    seminal_citation_threshold: int = 50,
) -> list[dict[str, Any]]:
    """Return papers with a ``tier`` field attached."""
    tagged: list[dict[str, Any]] = []
    for paper in papers:
        tier = classify_paper_tier(
            paper,
            recent_years=recent_years,
            seminal_citation_threshold=seminal_citation_threshold,
        )
        tagged.append({**paper, "tier": tier})
    return tagged
