"""Topic and context relevance scoring for retrieved papers."""

import math
import re
from datetime import UTC, datetime
from typing import Any

from apps.api.features.qualis.service import qualis_service
from apps.api.shared.settings import get_settings
from packages.postrec_core.retrieval.context_alignment import (
    apply_context_alignment_to_score,
    compute_context_alignment,
)

STOPWORDS = frozenset(
    {
        "a",
        "an",
        "the",
        "and",
        "or",
        "of",
        "in",
        "on",
        "for",
        "to",
        "with",
        "by",
        "from",
        "at",
        "is",
        "are",
        "was",
        "were",
        "be",
        "been",
        "being",
        "have",
        "has",
        "had",
        "do",
        "does",
        "did",
        "will",
        "would",
        "could",
        "should",
        "may",
        "might",
        "this",
        "that",
        "these",
        "those",
        "it",
        "its",
        "as",
        "we",
        "our",
        "their",
        "they",
        "using",
        "based",
        "study",
        "analysis",
        "approach",
        "model",
        "models",
        "method",
        "methods",
        "paper",
        "review",
        "survey",
        "research",
        "new",
        "towards",
        "via",
    }
)

TOKEN_PATTERN = re.compile(r"[a-z0-9]+")


def tokenize(text: str | None) -> set[str]:
    if not text:
        return set()
    return {token for token in TOKEN_PATTERN.findall(text.lower()) if len(token) > 2 and token not in STOPWORDS}


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

    topic_tokens: set[str] = set()
    for phrase in topics:
        topic_tokens.update(tokenize(phrase))

    area_tokens = tokenize(research_area) if research_area else set()
    if not topic_tokens and not area_tokens:
        return 0.5

    learned_tokens: set[str] = set()
    for phrase in learned_topics or []:
        learned_tokens.update(tokenize(phrase))

    title_overlap_topics = _overlap_score(title_tokens, topic_tokens) if topic_tokens else 0.0
    body_overlap_topics = _overlap_score(body_tokens, topic_tokens) if topic_tokens else 0.0
    title_overlap_area = _overlap_score(title_tokens, area_tokens) if area_tokens else 0.0
    body_overlap_area = _overlap_score(body_tokens, area_tokens) if area_tokens else 0.0

    title_overlap = max(title_overlap_topics, title_overlap_area * 0.9)
    body_overlap = max(body_overlap_topics, body_overlap_area * 0.9)

    avoided_tokens: set[str] = set()
    for phrase in avoided_topics or []:
        avoided_tokens.update(tokenize(phrase))
    avoid_penalty = 0.0
    if avoided_tokens and body_tokens & avoided_tokens:
        distinctive_hits = body_tokens & (avoided_tokens - topic_tokens)
        avoided_overlap = _overlap_score(body_tokens, avoided_tokens)
        if len(distinctive_hits) >= 2 or avoided_overlap >= 0.45:
            avoid_penalty = 0.35

    citations = paper.get("citation_count") or 0
    citation_boost = min(math.log1p(citations) / 12.0, 0.15)

    score = (0.55 * title_overlap) + (0.30 * body_overlap) + citation_boost - avoid_penalty

    if area_tokens and title_overlap_area >= 0.12 and (title_overlap_topics >= 0.10 or body_overlap_topics >= 0.12):
        score += 0.06

    if learned_tokens:
        learned_overlap = max(
            _overlap_score(title_tokens, learned_tokens),
            _overlap_score(body_tokens, learned_tokens),
        )
        if learned_overlap >= 0.20:
            score += min(0.05, learned_overlap * 0.08)

    if title_overlap < 0.08 and body_overlap < 0.12:
        if area_tokens and body_overlap_area >= 0.18 and body_overlap_topics >= 0.08:
            score = max(score, 0.23)
        else:
            score = min(score, 0.18)

    score, _ = qualis_service.apply_relevance_boost(score, paper)

    settings = get_settings()
    if settings.retrieval_openalex_fwci_boost_enabled:
        fwci = paper.get("openalex_fwci")
        if isinstance(fwci, (int, float)) and fwci > 1.0:
            score += min(0.06, (float(fwci) - 1.0) * 0.03)

    if settings.retrieval_domain_filter_enabled and (research_area or topics):
        alignment = compute_context_alignment(
            paper,
            research_area=research_area,
            topics=topics,
            learned_topics=learned_topics,
            avoided_topics=avoided_topics,
            pass_threshold=settings.retrieval_min_domain_alignment,
        )
        score = apply_context_alignment_to_score(score, alignment)
        if not alignment.passes:
            score = min(score, max(0.12, settings.retrieval_min_relevance_score - 0.08))

    return max(0.0, min(score, 1.0))


def min_publication_year(max_age_years: int) -> int:
    return datetime.now(UTC).year - max_age_years


def filter_papers_by_max_age(
    papers: list[dict[str, Any]],
    *,
    max_age_years: int,
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """Drop papers older than ``max_age_years``. Papers without a year are kept."""
    cutoff = min_publication_year(max_age_years)
    kept: list[dict[str, Any]] = []
    stats = {"input": len(papers), "filtered_out": 0, "kept": 0}

    for paper in papers:
        if not isinstance(paper, dict):
            stats["filtered_out"] += 1
            continue
        year = paper.get("year")
        if isinstance(year, int) and year < cutoff:
            stats["filtered_out"] += 1
            continue
        kept.append(paper)

    stats["kept"] = len(kept)
    return kept, stats


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
    stats = {
        "input": len(papers),
        "filtered_out": 0,
        "kept": 0,
        "alignment_rejected": 0,
        "keyword_traps_seen": 0,
    }

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
        alignment = compute_context_alignment(
            paper,
            research_area=research_area,
            topics=topics,
            learned_topics=learned_topics,
            avoided_topics=avoided_topics,
            pass_threshold=get_settings().retrieval_min_domain_alignment,
        )
        if alignment.keyword_trap:
            stats["keyword_traps_seen"] += 1
        paper = {
            **paper,
            "relevance_score": round(score, 4),
            "domain_alignment_score": alignment.score,
            "domain_alignment_passes": alignment.passes,
            "context_alignment_rationale": alignment.rationale,
            "context_keyword_trap": alignment.keyword_trap,
        }
        settings = get_settings()
        if settings.retrieval_domain_filter_enabled and (research_area or topics) and not alignment.passes:
            stats["alignment_rejected"] += 1
            stats["filtered_out"] += 1
            continue
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
