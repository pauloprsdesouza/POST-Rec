"""Gap-Facet Alignment (GFA) between proposals and gap matrix."""

from __future__ import annotations

import re
from typing import Any

from packages.postrec_core.facets.extraction import extract_proposal_facets
from packages.postrec_core.facets.taxonomy import FacetType

TOKEN_PATTERN = re.compile(r"[a-z0-9]+")
STOPWORDS = frozenset(
    {
        "the",
        "and",
        "for",
        "with",
        "that",
        "this",
        "from",
        "into",
        "using",
        "based",
        "study",
        "paper",
        "work",
        "approach",
        "method",
        "methods",
    }
)


def _content_tokens(text: str) -> set[str]:
    return {tok for tok in TOKEN_PATTERN.findall(text.lower()) if tok not in STOPWORDS and len(tok) > 2}


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def gap_statements(gap_matrix: dict[str, Any] | None) -> list[str]:
    if not gap_matrix:
        return []
    gaps = gap_matrix.get("gaps") or []
    statements: list[str] = []
    for item in gaps:
        if not isinstance(item, dict):
            continue
        parts = [
            item.get("gap"),
            item.get("suggested_direction"),
            *(item.get("supporting_limitations") or []),
        ]
        text = " ".join(str(p) for p in parts if p).strip()
        if text:
            statements.append(text)
    return statements


def compute_gap_facet_alignment(
    recommendation: dict[str, Any],
    gap_matrix: dict[str, Any] | None,
) -> float:
    """Score how well proposal facet deltas align with identified literature gaps."""
    gaps = gap_statements(gap_matrix)
    if not gaps:
        return 0.5

    proposal_facets = extract_proposal_facets(recommendation)
    aligned_gaps = recommendation.get("aligned_gaps") or []
    if isinstance(aligned_gaps, list):
        gaps = [str(g) for g in aligned_gaps if g] + gaps

    proposal_text = " ".join(
        proposal_facets.get(facet.value, "") for facet in FacetType.all_ordered()
    )
    proposal_tokens = _content_tokens(proposal_text)
    if not proposal_tokens:
        return 0.0

    gap_tokens = [_content_tokens(g) for g in gaps]
    max_overlap = max(_jaccard(proposal_tokens, gt) for gt in gap_tokens if gt)
    explicit = recommendation.get("novelty_delta") or ""
    explicit_bonus = 0.1 if _jaccard(proposal_tokens, _content_tokens(str(explicit))) > 0.15 else 0.0

    aligned_gaps = recommendation.get("aligned_gaps") or []
    alignment_multiplier = 1.0 if isinstance(aligned_gaps, list) and aligned_gaps else 0.45

    return max(0.0, min(1.0, (max_overlap + explicit_bonus) * alignment_multiplier))
