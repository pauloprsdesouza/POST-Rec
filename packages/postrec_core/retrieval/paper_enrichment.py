"""Extract lightweight labels from paper abstracts."""

from __future__ import annotations

import re
from typing import Any

LIMITATION_PATTERNS = (
    re.compile(r"(?i)(however,? .{10,120})"),
    re.compile(r"(?i)(future work.{0,100})"),
    re.compile(r"(?i)(remains? unclear.{0,100})"),
    re.compile(r"(?i)(limitation[s]?:?.{10,120})"),
    re.compile(r"(?i)(open problem[s]?:?.{10,120})"),
)

METHOD_HINTS = (
    "transformer",
    "graph neural",
    "reinforcement learning",
    "large language model",
    "diffusion",
    "contrastive learning",
    "meta-learning",
    "federated learning",
    "retrieval-augmented",
    "benchmark",
    "dataset",
)


def extract_limitations(abstract: str | None, *, max_items: int = 3) -> list[str]:
    if not abstract:
        return []
    found: list[str] = []
    for pattern in LIMITATION_PATTERNS:
        for match in pattern.findall(abstract):
            snippet = " ".join(str(match).split())
            if snippet and snippet not in found:
                found.append(snippet[:180])
            if len(found) >= max_items:
                return found
    return found


def extract_method_hints(title: str | None, abstract: str | None, *, max_items: int = 5) -> list[str]:
    text = f"{title or ''} {abstract or ''}".lower()
    hints = [hint for hint in METHOD_HINTS if hint in text]
    return hints[:max_items]


def enrich_paper_metadata(paper: dict[str, Any]) -> dict[str, Any]:
    """Attach methods and limitations labels to paper metadata."""
    title = paper.get("title")
    abstract = paper.get("abstract")
    limitations = extract_limitations(abstract if isinstance(abstract, str) else None)
    methods = extract_method_hints(
        title if isinstance(title, str) else None,
        abstract if isinstance(abstract, str) else None,
    )
    enriched = dict(paper)
    meta = dict(enriched.get("metadata") or enriched.get("metadata_") or {})
    if limitations:
        meta["limitations"] = limitations
    if methods:
        meta["methods"] = methods
    enriched["metadata"] = meta
    return enriched
