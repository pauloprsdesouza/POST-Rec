"""Shared tokenization helpers for retrieval scoring."""

from __future__ import annotations

import re

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

TERM_FAMILIES: dict[str, frozenset[str]] = {
    "recommender": frozenset({"recommendation", "recommendations", "recommend", "recsys", "recommenders"}),
    "recommendation": frozenset({"recommender", "recommenders", "recsys", "recommend", "recommendations"}),
    "system": frozenset({"systems"}),
    "systems": frozenset({"system"}),
    "learn": frozenset({"learning", "learned", "learner", "learners"}),
    "learning": frozenset({"learn", "learned", "learner", "learners", "machine"}),
    "network": frozenset({"networks", "networking"}),
    "networks": frozenset({"network", "networking"}),
    "model": frozenset({"models", "modeling", "modelling", "modelled", "modeled"}),
    "models": frozenset({"model", "modeling", "modelling"}),
    "modeling": frozenset({"model", "models", "modelling", "profile"}),
    "clinical": frozenset({"clinically", "clinic", "clinics", "patient", "patients"}),
    "patient": frozenset({"patients", "clinical"}),
    "psycholog": frozenset({"psychology", "psychological", "psychologist"}),
    "psychology": frozenset({"psycholog", "psychological", "psychologist"}),
}


def expand_tokens(tokens: set[str]) -> set[str]:
    expanded = set(tokens)
    for token in tokens:
        expanded.update(TERM_FAMILIES.get(token, ()))
    return expanded


def tokenize(text: str | None) -> set[str]:
    if not text:
        return set()
    return {token for token in TOKEN_PATTERN.findall(text.lower()) if len(token) > 2 and token not in STOPWORDS}


def phrase_tokens(phrases: list[str] | None) -> set[str]:
    tokens: set[str] = set()
    for phrase in phrases or []:
        if phrase and phrase.strip():
            tokens.update(tokenize(phrase))
    return tokens


def overlap_score(text_tokens: set[str], query_tokens: set[str]) -> float:
    if not query_tokens or not text_tokens:
        return 0.0
    return len(text_tokens & query_tokens) / len(query_tokens)
