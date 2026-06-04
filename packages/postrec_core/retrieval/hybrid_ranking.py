"""Hybrid sparse + dense ranking utilities."""

from __future__ import annotations

import math
from typing import Any


def cosine_similarity(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b, strict=False))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)


def fuse_relevance_scores(
    sparse_score: float,
    dense_score: float,
    *,
    sparse_weight: float = 0.4,
) -> float:
    """Fuse lexical and embedding similarity into a single score in [0, 1]."""
    sparse_weight = max(0.0, min(1.0, sparse_weight))
    dense_weight = 1.0 - sparse_weight
    dense_normalized = max(0.0, min(1.0, (dense_score + 1.0) / 2.0))
    fused = sparse_weight * sparse_score + dense_weight * dense_normalized
    return max(0.0, min(1.0, fused))


def rank_papers_by_hybrid_score(
    papers: list[dict[str, Any]],
    paper_embeddings: list[list[float]],
    query_embedding: list[float],
    *,
    sparse_weight: float = 0.4,
) -> list[dict[str, Any]]:
    """Attach dense/hybrid scores and return papers sorted by hybrid score."""
    if len(papers) != len(paper_embeddings):
        raise ValueError("papers and paper_embeddings length mismatch")

    scored: list[tuple[float, dict[str, Any]]] = []
    for paper, embedding in zip(papers, paper_embeddings, strict=False):
        sparse = float(paper.get("relevance_score") or 0.0)
        dense = cosine_similarity(query_embedding, embedding)
        hybrid = fuse_relevance_scores(sparse, dense, sparse_weight=sparse_weight)
        enriched = {
            **paper,
            "dense_score": round(dense, 4),
            "hybrid_score": round(hybrid, 4),
        }
        scored.append((hybrid, enriched))

    scored.sort(
        key=lambda item: (
            item[0],
            item[1].get("citation_count") or 0,
        ),
        reverse=True,
    )
    return [paper for _, paper in scored]
