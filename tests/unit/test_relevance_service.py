"""Tests for relevance filtering."""

from apps.api.services.relevance_service import compute_relevance_score, filter_and_rank_papers


def test_relevant_paper_scores_high():
    paper = {
        "title": "Graph neural networks for recommender systems",
        "abstract": "We study GNN-based collaborative filtering for recommendation.",
        "venue": "RecSys",
        "citation_count": 100,
    }
    score = compute_relevance_score(
        paper,
        topics=["recommender systems", "graph neural networks"],
        research_area="Recommender Systems",
    )
    assert score >= 0.4


def test_irrelevant_paper_scores_low():
    paper = {
        "title": "Social capital in rural sociology",
        "abstract": "A qualitative study of community networks in agriculture.",
        "venue": "American Journal of Sociology",
        "citation_count": 500,
    }
    score = compute_relevance_score(
        paper,
        topics=["recommender systems", "graph neural networks"],
        research_area="Recommender Systems and LLMs",
    )
    assert score < 0.22


def test_filter_and_rank_removes_irrelevant():
    papers = [
        {
            "title": "Deep learning for recommender systems",
            "abstract": "Survey of neural recommenders.",
            "citation_count": 200,
        },
        {
            "title": "Crop rotation in medieval Europe",
            "abstract": "Historical agricultural practices.",
            "citation_count": 900,
        },
    ]
    ranked, stats = filter_and_rank_papers(
        papers,
        topics=["recommender systems"],
        research_area="Machine Learning",
        min_score=0.22,
    )
    assert stats["filtered_out"] == 1
    assert len(ranked) == 1
    assert "recommender" in ranked[0]["title"].lower()
