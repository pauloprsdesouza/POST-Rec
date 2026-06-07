"""Deterministic validation for generated recommendations."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from packages.postrec_core.domain.run_mode import RunMode
from packages.postrec_core.retrieval.paper_tier import PAPER_TIER_SOTA_RECENT


@dataclass
class ValidationResult:
    valid: bool
    issues: list[str] = field(default_factory=list)
    publication_status: str = "published"


def _normalize_title(value: str | None) -> str:
    return " ".join(str(value or "").lower().split())


def _paper_index(papers: list[dict[str, Any]]) -> tuple[set[str], set[str]]:
    titles = {_normalize_title(p.get("title")) for p in papers if p.get("title")}
    dois = {str(p.get("doi")).lower() for p in papers if p.get("doi")}
    return titles, dois


def _has_sota_recent_anchor(recommendation: dict[str, Any], papers: list[dict[str, Any]]) -> bool:
    paper_by_title = {_normalize_title(p.get("title")): p for p in papers if p.get("title")}
    anchors = recommendation.get("sota_anchors") or []
    for anchor in anchors:
        if not isinstance(anchor, dict):
            continue
        paper = paper_by_title.get(_normalize_title(anchor.get("title")))
        if paper and paper.get("tier") == PAPER_TIER_SOTA_RECENT:
            return True
        if isinstance(anchor.get("year"), int) and anchor["year"] >= _recent_cutoff():
            return True
    return False


def _recent_cutoff() -> int:
    from packages.postrec_core.retrieval.paper_tier import current_year

    return current_year() - 3


def verify_citations(
    recommendation: dict[str, Any],
    papers: list[dict[str, Any]],
) -> list[str]:
    """Return issues for citations not present in retrieved papers."""
    titles, dois = _paper_index(papers)
    issues: list[str] = []

    def check_entry(entry: dict[str, Any], label: str) -> None:
        title = _normalize_title(entry.get("title"))
        doi = str(entry.get("doi") or "").lower()
        if title and title not in titles:
            issues.append(f"{label} title not in retrieved set: {entry.get('title')}")
        if doi and doi not in dois:
            issues.append(f"{label} DOI not in retrieved set: {entry.get('doi')}")

    for entry in recommendation.get("evidence_papers") or []:
        if isinstance(entry, dict):
            check_entry(entry, "Evidence")
    for entry in recommendation.get("sota_anchors") or []:
        if isinstance(entry, dict):
            check_entry(entry, "SOTA anchor")

    return issues


def validate_recommendation(
    recommendation: dict[str, Any],
    papers: list[dict[str, Any]],
    *,
    mode: RunMode,
    require_sota_fields: bool = True,
) -> ValidationResult:
    issues: list[str] = []

    if not recommendation.get("title"):
        issues.append("Missing title.")

    if require_sota_fields:
        for field in ("sota_summary", "novelty_delta", "closest_prior_work"):
            if not str(recommendation.get(field) or "").strip():
                issues.append(f"Missing required field: {field}.")

        anchors = recommendation.get("sota_anchors") or []
        if not anchors:
            issues.append("Missing sota_anchors.")

    citation_issues = verify_citations(recommendation, papers)
    issues.extend(citation_issues)

    if mode in (RunMode.SOTA, RunMode.EXPLORATORY, RunMode.FGGV) and not _has_sota_recent_anchor(
        recommendation, papers
    ):
        issues.append("No recent SOTA anchor linked to retrieved papers.")

    if mode == RunMode.FGGV:
        facet_deltas = recommendation.get("facet_deltas")
        if not isinstance(facet_deltas, dict) or not any(
            str(facet_deltas.get(k) or "").strip() for k in ("problem", "method", "data", "evaluation")
        ):
            issues.append("Missing facet_deltas (problem/method/data/evaluation).")
        aligned = recommendation.get("aligned_gaps") or []
        if not aligned:
            issues.append("Missing aligned_gaps referencing gap matrix.")

    publication_status = "published"
    if issues:
        if mode.strict_critic:
            publication_status = "needs_refinement"
        elif len(citation_issues) > 0:
            publication_status = "needs_refinement"

    return ValidationResult(
        valid=len(issues) == 0,
        issues=issues,
        publication_status=publication_status if issues else "published",
    )
