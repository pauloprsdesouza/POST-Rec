"""Consolidated OpenAlex retrieval plan — fewer API calls, same coverage intent."""

from __future__ import annotations

from dataclasses import dataclass, field

SOTA_QUERY_SUFFIX = "state of the art survey"


@dataclass(frozen=True)
class PlannedSearch:
    query: str
    pass_kinds: tuple[str, ...] = ("foundation", "sota")


@dataclass
class RetrievalPlan:
    searches: list[PlannedSearch] = field(default_factory=list)
    learned_queries: list[str] = field(default_factory=list)


def _clean(text: str | None) -> str:
    return " ".join((text or "").split())


def _primary_topic(topics: list[str]) -> str | None:
    for topic in topics:
        cleaned = _clean(topic)
        if cleaned:
            return cleaned
    return None


def build_retrieval_plan(
    topics: list[str],
    *,
    research_area: str | None = None,
    learned_topics: list[str] | None = None,
    include_sota_terms: bool = True,
    learned_topic_cap: int = 2,
    dual_pass: bool = True,
) -> RetrievalPlan:
    """Build a small set of high-signal OpenAlex searches."""
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

    def add_search(query: str, *, pass_kinds: tuple[str, ...]) -> None:
        normalized = _clean(query)
        if not normalized:
            return
        key = (normalized.lower(), pass_kinds)
        if key in seen:
            return
        seen.add(key)
        searches.append(PlannedSearch(query=normalized, pass_kinds=pass_kinds))

    add_search(intent_query, pass_kinds=passes)
    if primary.lower() != intent_query.lower():
        add_search(primary, pass_kinds=passes)
    if include_sota_terms and dual_pass:
        add_search(f"{primary} {SOTA_QUERY_SUFFIX}", pass_kinds=("sota",))

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

    return RetrievalPlan(searches=searches, learned_queries=learned)
