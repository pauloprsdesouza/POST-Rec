"""Heuristic facet extraction from papers and proposals."""

from __future__ import annotations

import re
from typing import Any

from packages.postrec_core.facets.taxonomy import FacetType
from packages.postrec_core.retrieval.paper_enrichment import extract_limitations, extract_method_hints

DATA_PATTERNS = (
    re.compile(r"(?i)\b(dataset|benchmark|corpus|dblp|imagenet|mnist|cifar|movielens)\b[^.]{0,80}"),
    re.compile(r"(?i)\bon (the )?[A-Z][A-Za-z0-9-]+ (dataset|benchmark)\b"),
)

EVAL_PATTERNS = (
    re.compile(r"(?i)\b(accuracy|f1|auc|ndcg|map|rmse|mae|bleu|rouge|hit@|mrr)\b[^.]{0,60}"),
    re.compile(r"(?i)\b(evaluation metric|experimental setup|ablation)\b[^.]{0,80}"),
)


def _first_sentence(text: str | None, *, max_len: int = 200) -> str:
    if not text:
        return ""
    cleaned = " ".join(text.split())
    for sep in (". ", "; ", " — ", " - "):
        if sep in cleaned:
            return cleaned.split(sep, 1)[0][:max_len]
    return cleaned[:max_len]


def _match_patterns(text: str, patterns: tuple[re.Pattern[str], ...], *, max_items: int = 2) -> str:
    found: list[str] = []
    for pattern in patterns:
        for match in pattern.findall(text):
            snippet = " ".join(str(match).split())
            if snippet and snippet not in found:
                found.append(snippet[:160])
            if len(found) >= max_items:
                break
        if len(found) >= max_items:
            break
    return "; ".join(found)


def extract_paper_facets(paper: dict[str, Any]) -> dict[str, str]:
    """Build facet statements from a retrieved paper."""
    title = str(paper.get("title") or "")
    abstract = str(paper.get("abstract") or "")
    methods = paper.get("methods") or extract_method_hints(title or None, abstract or None)
    limitations = paper.get("limitations") or extract_limitations(abstract or None)

    problem_parts = [_first_sentence(abstract)] if abstract else []
    if limitations:
        problem_parts.append(limitations[0])
    problem = " ".join(part for part in problem_parts if part).strip() or title

    method = ", ".join(str(m) for m in methods) if methods else _first_sentence(title)
    data = _match_patterns(f"{title} {abstract}", DATA_PATTERNS)
    evaluation = _match_patterns(f"{title} {abstract}", EVAL_PATTERNS)

    return {
        FacetType.PROBLEM.value: problem or title,
        FacetType.METHOD.value: method or title,
        FacetType.DATA.value: data or "standard benchmarks in domain",
        FacetType.EVALUATION.value: evaluation or "standard domain metrics",
    }


def extract_proposal_facets(recommendation: dict[str, Any]) -> dict[str, str]:
    """Resolve facet deltas from explicit fields or fall back to proposal structure."""
    explicit = recommendation.get("facet_deltas")
    if isinstance(explicit, dict) and any(explicit.values()):
        return {
            facet.value: str(explicit.get(facet.value) or "").strip()
            for facet in FacetType.all_ordered()
        }

    datasets = recommendation.get("datasets") or []
    metrics = recommendation.get("evaluation_metrics") or []
    return {
        FacetType.PROBLEM.value: " ".join(
            str(part)
            for part in (
                recommendation.get("research_gap"),
                recommendation.get("research_question"),
            )
            if part
        ).strip(),
        FacetType.METHOD.value: str(recommendation.get("proposed_method") or recommendation.get("technique_name") or ""),
        FacetType.DATA.value: ", ".join(str(d) for d in datasets) if datasets else "",
        FacetType.EVALUATION.value: ", ".join(str(m) for m in metrics) if metrics else str(
            recommendation.get("experimental_plan") or ""
        )[:180],
    }
