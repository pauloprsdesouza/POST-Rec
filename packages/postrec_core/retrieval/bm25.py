"""Lightweight BM25 sparse scoring."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Any

TOKEN_PATTERN = re.compile(r"[a-z0-9]+")
DEFAULT_K1 = 1.2
DEFAULT_B = 0.75


def _tokenize(text: str) -> list[str]:
    return TOKEN_PATTERN.findall(text.lower())


@dataclass(frozen=True)
class Bm25Index:
    """Precomputed corpus statistics for repeated BM25 scoring."""

    avgdl: float
    n_docs: int
    doc_freq: dict[str, int]

    @classmethod
    def from_documents(cls, corpus_docs: list[str]) -> Bm25Index:
        tokenized = [_tokenize(doc) for doc in corpus_docs if doc]
        n_docs = max(len(tokenized), 1)
        avgdl = sum(len(tokens) for tokens in tokenized) / n_docs
        doc_freq: dict[str, int] = {}
        for tokens in tokenized:
            for term in set(tokens):
                doc_freq[term] = doc_freq.get(term, 0) + 1
        return cls(avgdl=avgdl, n_docs=n_docs, doc_freq=doc_freq)

    def score(self, query: str, document: str, *, k1: float = DEFAULT_K1, b: float = DEFAULT_B) -> float:
        query_terms = _tokenize(query)
        if not query_terms:
            return 0.0

        doc_terms = _tokenize(document)
        if not doc_terms:
            return 0.0

        doc_len = len(doc_terms)
        term_freq: dict[str, int] = {}
        for term in doc_terms:
            term_freq[term] = term_freq.get(term, 0) + 1

        score = 0.0
        for term in set(query_terms):
            tf = term_freq.get(term, 0)
            if tf == 0:
                continue
            df = self.doc_freq.get(term, 0)
            idf = math.log(1 + (self.n_docs - df + 0.5) / (df + 0.5))
            denom = tf + k1 * (1 - b + b * (doc_len / max(self.avgdl, 1)))
            score += idf * (tf * (k1 + 1)) / max(denom, 1e-9)

        return max(0.0, min(1.0, score / 8.0))


def bm25_score(
    query: str,
    document: str,
    *,
    corpus_docs: list[str] | None = None,
    index: Bm25Index | None = None,
    k1: float = DEFAULT_K1,
    b: float = DEFAULT_B,
) -> float:
    """Return a normalized BM25 score in [0, 1] for query vs document."""
    if index is not None:
        return index.score(query, document, k1=k1, b=b)

    query_terms = _tokenize(query)
    if not query_terms:
        return 0.0

    doc_terms = _tokenize(document)
    if not doc_terms:
        return 0.0

    doc_len = len(doc_terms)
    avgdl = doc_len
    if corpus_docs:
        lengths = [len(_tokenize(doc)) for doc in corpus_docs if doc]
        avgdl = sum(lengths) / max(len(lengths), 1)

    term_freq: dict[str, int] = {}
    for term in doc_terms:
        term_freq[term] = term_freq.get(term, 0) + 1

    corpus = corpus_docs or [document]
    n_docs = max(len(corpus), 1)
    score = 0.0
    for term in set(query_terms):
        tf = term_freq.get(term, 0)
        if tf == 0:
            continue
        df = sum(1 for doc in corpus if term in _tokenize(doc))
        idf = math.log(1 + (n_docs - df + 0.5) / (df + 0.5))
        denom = tf + k1 * (1 - b + b * (doc_len / max(avgdl, 1)))
        score += idf * (tf * (k1 + 1)) / max(denom, 1e-9)

    return max(0.0, min(1.0, score / 8.0))


def bm25_score_paper(
    query: str,
    paper: dict[str, Any],
    *,
    corpus_docs: list[str] | None = None,
    index: Bm25Index | None = None,
) -> float:
    document = " ".join(
        part
        for part in (
            paper.get("title"),
            paper.get("abstract"),
            paper.get("venue"),
        )
        if part
    )
    return bm25_score(query, document, corpus_docs=corpus_docs, index=index)
