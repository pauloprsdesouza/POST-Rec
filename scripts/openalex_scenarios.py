"""Shared OpenAlex validation scenarios and helpers."""

from __future__ import annotations

from typing import Any

OPENALEX_VALIDATION_SCENARIOS: list[dict[str, Any]] = [
    {
        "name": "recsys_social_capital",
        "research_area": "Recommender Systems",
        "topics": ["social capital", "social networks", "profile modeling"],
        "query": "social capital Recommender Systems social networks",
    },
    {
        "name": "clinical_psychology",
        "research_area": "Clinical Psychology",
        "topics": ["adolescent depression", "social networks"],
        "query": "adolescent depression social networks",
    },
    {
        "name": "clinical_medicine_ml",
        "research_area": "Clinical Medicine",
        "topics": ["diabetes", "machine learning"],
        "query": "diabetes machine learning clinical",
    },
]


def reconstruct_openalex_abstract(inverted_index: dict[str, list[int]] | None) -> str | None:
    if not inverted_index:
        return None
    positions: list[tuple[int, str]] = []
    for token, indexes in inverted_index.items():
        for index in indexes:
            positions.append((index, token))
    if not positions:
        return None
    positions.sort(key=lambda item: item[0])
    return " ".join(token for _, token in positions)
