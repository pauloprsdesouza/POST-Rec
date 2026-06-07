"""Consolidated retrieval plan — fewer API calls, same coverage intent."""

from __future__ import annotations

from dataclasses import dataclass, field

SOTA_QUERY_SUFFIX = "state of the art survey"

CS_ML_SIGNALS = (
    "machine learning",
    "deep learning",
    "neural network",
    "recommender",
    "reinforcement learning",
    "natural language",
    "computer vision",
    "artificial intelligence",
    "graph neural",
    "large language model",
    "transformer",
    "classification",
    "regression",
    "data mining",
    "information retrieval",
)


@dataclass(frozen=True)
class PlannedSearch:
    """One search string applied to selected sources and passes."""

    query: str
    pass_kinds: tuple[str, ...] = ("foundation", "sota")
    use_crossref: bool = False


@dataclass
class RetrievalPlan:
    """Structured plan replacing per-keyword fan-out across all sources."""

    searches: list[PlannedSearch] = field(default_factory=list)
    learned_queries: list[str] = field(default_factory=list)
    arxiv_query: str | None = None


def _clean(text: str | None) -> str:
    return " ".join((text or "").split())


def _primary_topic(topics: list[str]) -> str | None:
    for topic in topics:
        cleaned = _clean(topic)
        if cleaned:
            return cleaned
    return None


def should_include_arxiv(
    topics: list[str],
    *,
    research_area: str | None = None,
    learned_topics: list[str] | None = None,
) -> bool:
    """Include arXiv only for CS/ML-heavy research (preprint source)."""
    blob = " ".join(
        part.lower() for part in [*topics, research_area or "", *(learned_topics or [])] if part and str(part).strip()
    )
    return any(signal in blob for signal in CS_ML_SIGNALS)


def build_arxiv_search_query(query: str) -> str:
    """Field-targeted arXiv query (title + abstract)."""
    cleaned = _clean(query)
    if not cleaned:
        return ""
    if len(cleaned) > 120:
        cleaned = cleaned[:120].rsplit(" ", 1)[0]
    safe = cleaned.replace('"', "")
    return f"(ti:{safe} OR abs:{safe})"


def build_retrieval_plan(
    topics: list[str],
    *,
    research_area: str | None = None,
    learned_topics: list[str] | None = None,
    include_sota_terms: bool = True,
    learned_topic_cap: int = 2,
    dual_pass: bool = True,
) -> RetrievalPlan:
    """
    Build a small set of high-signal searches instead of cartesian query expansion.

    Typical output: 2–4 core searches + up to 2 learned-topic searches + optional arXiv.
    """
    primary = _primary_topic(topics)
    if not primary:
        return RetrievalPlan()

    area = _clean(research_area) if research_area else ""
    secondary = _clean(topics[1]) if len(topics) > 1 else ""

    intent_parts = [primary]
    if area and area.lower() not in primary.lower():
        intent_parts.append(area)
    if secondary and secondary.lower() not in primary.lower():
        intent_parts.append(secondary)
    intent_query = _clean(" ".join(intent_parts))

    passes: tuple[str, ...] = ("foundation", "sota") if dual_pass else ("foundation",)
    searches: list[PlannedSearch] = []
    seen: set[tuple[str, tuple[str, ...]]] = set()

    def add_search(query: str, *, pass_kinds: tuple[str, ...], use_crossref: bool = False) -> None:
        normalized = _clean(query)
        if not normalized:
            return
        key = (normalized.lower(), pass_kinds)
        if key in seen:
            return
        seen.add(key)
        searches.append(PlannedSearch(query=normalized, pass_kinds=pass_kinds, use_crossref=use_crossref))

    add_search(intent_query, pass_kinds=passes, use_crossref=True)

    if primary.lower() != intent_query.lower():
        add_search(primary, pass_kinds=passes, use_crossref=True)

    if include_sota_terms and dual_pass:
        sota_query = _clean(f"{primary} {SOTA_QUERY_SUFFIX}")
        add_search(sota_query, pass_kinds=("sota",), use_crossref=False)

    learned: list[str] = []
    seen_learned: set[str] = set()
    for item in learned_topics or []:
        cleaned = _clean(item)
        key = cleaned.lower()
        if not cleaned or key in seen_learned:
            continue
        seen_learned.add(key)
        learned.append(cleaned)
        if len(learned) >= max(learned_topic_cap, 0):
            break

    arxiv_query: str | None = None
    if should_include_arxiv(topics, research_area=research_area, learned_topics=learned_topics):
        arxiv_query = build_arxiv_search_query(intent_query or primary)

    return RetrievalPlan(searches=searches, learned_queries=learned, arxiv_query=arxiv_query)
