"""Tests for max article age filtering."""

from apps.api.features.retrieval.relevance import filter_papers_by_max_age, min_publication_year


def test_min_publication_year():
    current = min_publication_year(0) + 0
    assert min_publication_year(5) == current - 5


def test_filter_papers_by_max_age_drops_old_papers():
    cutoff = min_publication_year(5)
    papers = [
        {"title": "Recent", "year": cutoff},
        {"title": "Too old", "year": cutoff - 1},
        {"title": "Unknown year"},
    ]
    kept, stats = filter_papers_by_max_age(papers, max_age_years=5)

    assert [paper["title"] for paper in kept] == ["Recent", "Unknown year"]
    assert stats == {"input": 3, "filtered_out": 1, "kept": 2}
