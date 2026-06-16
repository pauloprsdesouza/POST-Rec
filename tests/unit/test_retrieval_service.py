"""Tests for OpenAlex retrieval normalization."""

from apps.api.features.retrieval.normalizers import (
    _normalize_doi,
    _normalize_openalex_work,
    _reconstruct_abstract,
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
