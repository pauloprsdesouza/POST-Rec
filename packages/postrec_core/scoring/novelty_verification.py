"""Deterministic novelty verification helpers."""

from __future__ import annotations

import re
from typing import Any

from packages.postrec_core.retrieval.hybrid_ranking import cosine_similarity

TOKEN_PATTERN = re.compile(r"[a-z0-9]+")


def proposal_text(recommendation: dict[str, Any]) -> str:
    parts = [
        recommendation.get("title"),
        recommendation.get("research_gap"),
        recommendation.get("research_question"),
        recommendation.get("hypothesis"),
        recommendation.get("proposed_method"),
        recommendation.get("novelty_delta"),
        recommendation.get("expected_contribution"),
    ]
    return " ".join(str(part) for part in parts if part)


def token_set(text: str) -> set[str]:
    return set(TOKEN_PATTERN.findall(text.lower()))


def claim_overlap_novelty(proposal: str, corpus_texts: list[str]) -> float:
    """Higher means more novel (less token overlap with corpus)."""
    proposal_tokens = token_set(proposal)
    if not proposal_tokens:
        return 0.5
    max_overlap = 0.0
    for text in corpus_texts:
        other = token_set(text)
        if not other:
            continue
        overlap = len(proposal_tokens & other) / len(proposal_tokens)
        max_overlap = max(max_overlap, overlap)
    return max(0.0, min(1.0, 1.0 - max_overlap))


def embedding_novelty(proposal_embedding: list[float], paper_embeddings: list[list[float]]) -> float:
    """Higher means more novel (lower max cosine similarity to evidence)."""
    if not proposal_embedding or not paper_embeddings:
        return 0.5
    max_sim = max(cosine_similarity(proposal_embedding, emb) for emb in paper_embeddings)
    return max(0.0, min(1.0, 1.0 - max_sim))


def blend_novelty_verified(
    embedding_novelty_score: float,
    claim_novelty_score: float,
    llm_novelty_0_100: float | None,
    *,
    llm_blend: float = 0.35,
) -> float:
    deterministic = 0.6 * embedding_novelty_score + 0.4 * claim_novelty_score
    if llm_novelty_0_100 is None:
        return deterministic
    llm_norm = max(0.0, min(1.0, llm_novelty_0_100 / 100.0))
    return max(0.0, min(1.0, (1.0 - llm_blend) * deterministic + llm_blend * llm_norm))


def compute_sota_fit(
    recommendation: dict[str, Any],
    papers: list[dict[str, Any]],
) -> float:
    """Estimate how well a proposal engages recent SOTA anchors."""
    anchors = recommendation.get("sota_anchors") or []
    if not anchors:
        evidence = recommendation.get("evidence_papers") or []
        anchors = [e for e in evidence if isinstance(e, dict)]

    if not anchors:
        return 0.0

    paper_by_title = {str(p.get("title", "")).lower(): p for p in papers if p.get("title")}
    recent_hits = 0
    for anchor in anchors:
        if not isinstance(anchor, dict):
            continue
        title = str(anchor.get("title") or "").lower()
        paper = paper_by_title.get(title)
        if paper and paper.get("tier") == "sota_recent":
            recent_hits += 1

    anchor_score = min(1.0, len(anchors) / 2.0)
    recent_score = recent_hits / max(len(anchors), 1)
    summary = recommendation.get("sota_summary") or recommendation.get("related_work_summary") or ""
    summary_bonus = 0.15 if len(summary.strip()) > 40 else 0.0
    return max(0.0, min(1.0, 0.45 * anchor_score + 0.45 * recent_score + summary_bonus))
