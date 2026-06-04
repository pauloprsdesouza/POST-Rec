"""Topic and context relevance scoring for retrieved papers."""

import math
import re
from typing import Any

STOPWORDS = frozenset({
    "a", "an", "the", "and", "or", "of", "in", "on", "for", "to", "with", "by",
    "from", "at", "is", "are", "was", "were", "be", "been", "being", "have", "has",
    "had", "do", "does", "did", "will", "would", "could", "should", "may", "might",
    "this", "that", "these", "those", "it", "its", "as", "we", "our", "their", "they",
    "using", "based", "study", "analysis", "approach", "model", "models", "method",
    "methods", "paper", "review", "survey", "research", "new", "towards", "via",
})

TOKEN_PATTERN = re.compile(r"[a-z0-9]+")


def tokenize(text: str | None) -> set[str]:
    if not text:
        return set()
    return {
        token
        for token in TOKEN_PATTERN.findall(text.lower())
        if len(token) > 2 and token not in STOPWORDS
    }


def _overlap_score(text_tokens: set[str], query_tokens: set[str]) -> float:
    if not query_tokens or not text_tokens:
        return 0.0
    return len(text_tokens & query_tokens) / len(query_tokens)


def compute_relevance_score(
    paper: dict[str, Any],
    *,
    topics: list[str],
    research_area: str | None = None,
    learned_topics: list[str] | None = None,
    avoided_topics: list[str] | None = None,
) -> float:
    title_tokens = tokenize(paper.get("title"))
    body_tokens = tokenize(
        " ".join(
            part
            for part in (
                paper.get("title"),
                paper.get("abstract"),
                paper.get("venue"),
            )
            if part
        )
    )

    query_tokens: set[str] = set()
    for phrase in topics:
        query_tokens.update(tokenize(phrase))
    if research_area:
        query_tokens.update(tokenize(research_area))
    for phrase in learned_topics or []:
        query_tokens.update(tokenize(phrase))

    if not query_tokens:
        return 0.5

    title_overlap = _overlap_score(title_tokens, query_tokens)
    body_overlap = _overlap_score(body_tokens, query_tokens)

    avoided_tokens: set[str] = set()
    for phrase in avoided_topics or []:
        avoided_tokens.update(tokenize(phrase))
    avoid_penalty = 0.35 if avoided_tokens and body_tokens & avoided_tokens else 0.0

    citations = paper.get("citation_count") or 0
    citation_boost = min(math.log1p(citations) / 12.0, 0.15)

    score = (0.55 * title_overlap) + (0.30 * body_overlap) + citation_boost - avoid_penalty

    if title_overlap < 0.08 and body_overlap < 0.12:
        score = min(score, 0.18)

    return max(0.0, min(score, 1.0))


def filter_and_rank_papers(
    papers: list[dict[str, Any]],
    *,
    topics: list[str],
    research_area: str | None = None,
    learned_topics: list[str] | None = None,
    avoided_topics: list[str] | None = None,
    min_score: float = 0.22,
    max_papers: int | None = None,
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    scored: list[tuple[float, dict[str, Any]]] = []
    stats = {"input": len(papers), "filtered_out": 0, "kept": 0}

    for paper in papers:
        if not isinstance(paper, dict):
            stats["filtered_out"] += 1
            continue
        score = compute_relevance_score(
            paper,
            topics=topics,
            research_area=research_area,
            learned_topics=learned_topics,
            avoided_topics=avoided_topics,
        )
        paper = {**paper, "relevance_score": round(score, 4)}
        if score >= min_score:
            scored.append((score, paper))
        else:
            stats["filtered_out"] += 1

    scored.sort(key=lambda item: (item[0], item[1].get("citation_count") or 0), reverse=True)
    ranked = [paper for _, paper in scored]
    if max_papers:
        ranked = ranked[:max_papers]
    stats["kept"] = len(ranked)
    return ranked, stats
