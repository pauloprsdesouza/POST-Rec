"""Tests for academic retrieval normalization."""

from apps.api.features.retrieval.normalizers import (
    _normalize_crossref_work,
    _normalize_doi,
    _normalize_openalex_work,
    _normalize_semantic_scholar_paper,
    _reconstruct_abstract,
    _strip_crossref_abstract,
)


def test_reconstruct_abstract():
    inverted = {"hello": [0], "world": [1]}
    assert _reconstruct_abstract(inverted) == "hello world"


def test_normalize_doi():
    assert _normalize_doi("https://doi.org/10.1234/example") == "10.1234/example"


def test_normalize_openalex_work_with_null_source():
    work = {
        "id": "https://openalex.org/W123",
        "title": "Social capital in networks",
        "publication_year": 2024,
        "primary_location": {"source": None},
        "authorships": [{"author": None}, {"author": {"display_name": "Jane Doe"}}],
        "cited_by_count": 10,
    }
    result = _normalize_openalex_work(work)
    assert result is not None
    assert result["title"] == "Social capital in networks"
    assert result["venue"] is None
    assert result["authors"] == ["Jane Doe"]


def test_normalize_openalex_work_missing_title_returns_none():
    assert _normalize_openalex_work({"id": "W1"}) is None


def test_normalize_semantic_scholar_paper():
    paper = {
        "paperId": "abc123",
        "title": "Graph neural recommender systems",
        "abstract": "We study GNN recommenders.",
        "authors": [{"name": "Alice"}, {"name": "Bob"}],
        "year": 2023,
        "venue": "RecSys",
        "citationCount": 42,
        "externalIds": {"DOI": "10.1145/1234567.1234567"},
        "url": "https://www.semanticscholar.org/paper/abc123",
    }
    result = _normalize_semantic_scholar_paper(paper)
    assert result is not None
    assert result["source"] == "semantic_scholar"
    assert result["doi"] == "10.1145/1234567.1234567"
    assert result["citation_count"] == 42


def test_normalize_crossref_work():
    item = {
        "DOI": "10.1000/test.doi",
        "title": ["Recommender systems survey"],
        "author": [{"given": "John", "family": "Doe"}],
        "published-print": {"date-parts": [[2022, 5, 1]]},
        "container-title": ["ACM Computing Surveys"],
        "is-referenced-by-count": 120,
        "abstract": "<jats:p>Survey of recommender systems.</jats:p>",
        "URL": "https://doi.org/10.1000/test.doi",
    }
    result = _normalize_crossref_work(item)
    assert result is not None
    assert result["source"] == "crossref"
    assert result["year"] == 2022
    assert "Survey of recommender systems" in (result["abstract"] or "")


def test_strip_crossref_abstract():
    assert _strip_crossref_abstract("<jats:p>Hello world</jats:p>") == "Hello world"
