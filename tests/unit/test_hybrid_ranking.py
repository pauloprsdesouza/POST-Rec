"""Unit tests for hybrid ranking."""

from packages.postrec_core.retrieval.hybrid_ranking import (
    cosine_similarity,
    fuse_relevance_scores,
    rank_papers_by_hybrid_score,
)


def test_cosine_similarity_identical_vectors():
    vector = [1.0, 0.0, 0.0]
    assert cosine_similarity(vector, vector) == 1.0


def test_cosine_similarity_orthogonal_vectors():
    assert cosine_similarity([1.0, 0.0], [0.0, 1.0]) == 0.0


def test_fuse_relevance_scores_balances_sparse_and_dense():
    fused = fuse_relevance_scores(0.8, 1.0, sparse_weight=0.5)
    assert 0.85 <= fused <= 0.95


def test_rank_papers_by_hybrid_score_orders_by_hybrid():
    papers = [
        {"title": "Low", "relevance_score": 0.2, "citation_count": 1},
        {"title": "High", "relevance_score": 0.9, "citation_count": 10},
    ]
    embeddings = [[0.1, 0.2], [0.9, 0.8]]
    query = [1.0, 1.0]

    ranked = rank_papers_by_hybrid_score(papers, embeddings, query, sparse_weight=0.4)

    assert ranked[0]["title"] == "High"
    assert "hybrid_score" in ranked[0]
    assert "dense_score" in ranked[0]
