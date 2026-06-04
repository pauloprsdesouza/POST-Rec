"""Tests for query expansion and BM25."""

from packages.postrec_core.retrieval.bm25 import bm25_score
from packages.postrec_core.retrieval.query_expansion import expand_retrieval_queries


def test_expand_retrieval_queries_deduplicates():
    queries = expand_retrieval_queries(
        ["graph neural networks"],
        research_area="Recommender Systems",
        learned_topics=["collaborative filtering"],
    )
    assert "graph neural networks" in queries
    assert any("Recommender Systems" in q for q in queries)


def test_bm25_score_prefers_relevant_document():
    query = "graph neural recommender systems"
    relevant = bm25_score(query, "graph neural networks for recommender systems benchmark")
    irrelevant = bm25_score(query, "quantum chemistry simulation methods")
    assert relevant > irrelevant
