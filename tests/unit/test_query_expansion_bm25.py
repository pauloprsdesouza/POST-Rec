"""Tests for BM25 sparse scoring."""

from packages.postrec_core.retrieval.bm25 import bm25_score


def test_bm25_score_prefers_relevant_document():
    query = "graph neural recommender systems"
    relevant = bm25_score(query, "graph neural networks for recommender systems benchmark")
    irrelevant = bm25_score(query, "quantum chemistry simulation methods")
    assert relevant > irrelevant
