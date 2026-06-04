"""Merge SOTA-recent and foundation retrieval passes."""

from __future__ import annotations

from typing import Any

from packages.postrec_core.retrieval.paper_tier import classify_paper_tier


def merge_dual_pass_results(
    sota_papers: list[dict[str, Any]],
    foundation_papers: list[dict[str, Any]],
    *,
    max_papers: int,
    sota_quota: float = 0.6,
    recent_years: int = 3,
    seminal_citation_threshold: int = 50,
) -> list[dict[str, Any]]:
    """Merge two retrieval passes with a SOTA-recent quota."""
    seen: set[str] = set()
    merged: list[dict[str, Any]] = []

    def key(paper: dict[str, Any]) -> str:
        doi = str(paper.get("doi") or "").lower()
        if doi:
            return f"doi:{doi}"
        return f"title:{str(paper.get('title') or '').lower()}"

    def add(paper: dict[str, Any], retrieval_pass: str) -> None:
        paper_key = key(paper)
        if paper_key in seen:
            return
        seen.add(paper_key)
        tagged = {
            **paper,
            "retrieval_pass": retrieval_pass,
            "tier": classify_paper_tier(
                paper,
                recent_years=recent_years,
                seminal_citation_threshold=seminal_citation_threshold,
            ),
        }
        merged.append(tagged)

    sota_target = max(1, int(round(max_papers * sota_quota)))
    for paper in sota_papers:
        if len([p for p in merged if p.get("retrieval_pass") == "sota"]) >= sota_target:
            break
        add(paper, "sota")

    foundation_target = max(0, max_papers - sota_target)
    for paper in foundation_papers:
        if len([p for p in merged if p.get("retrieval_pass") == "foundation"]) >= foundation_target:
            break
        add(paper, "foundation")

    for paper in sota_papers:
        if len(merged) >= max_papers:
            break
        add(paper, "sota")

    for paper in foundation_papers:
        if len(merged) >= max_papers:
            break
        add(paper, "foundation")

    return merged[:max_papers]
