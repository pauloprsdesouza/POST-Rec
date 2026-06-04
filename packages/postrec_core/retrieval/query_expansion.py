"""Query expansion for literature retrieval."""

from __future__ import annotations

SOTA_EXPANSION_TERMS = (
    "state of the art",
    "recent benchmark",
    "latest methods",
    "survey",
)


def expand_retrieval_queries(
    topics: list[str],
    *,
    research_area: str | None = None,
    learned_topics: list[str] | None = None,
    include_sota_terms: bool = True,
) -> list[str]:
    """Build deduplicated search queries from seed topics and profile context."""
    queries: list[str] = []
    seen: set[str] = set()

    def add(query: str) -> None:
        normalized = " ".join(query.lower().split())
        if normalized and normalized not in seen:
            seen.add(normalized)
            queries.append(query.strip())

    for topic in topics:
        if topic and topic.strip():
            add(topic.strip())

    if research_area and research_area.strip():
        add(research_area.strip())
        for topic in topics[:3]:
            if topic and topic.strip():
                add(f"{topic.strip()} {research_area.strip()}")

    for learned in learned_topics or []:
        if learned and learned.strip():
            add(learned.strip())

    if include_sota_terms:
        for topic in topics[:2]:
            if not topic or not topic.strip():
                continue
            for term in SOTA_EXPANSION_TERMS[:2]:
                add(f"{topic.strip()} {term}")

    return queries
