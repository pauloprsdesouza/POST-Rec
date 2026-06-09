"""Tests for CORE.ac.uk retrieval client and normalizer."""

from unittest.mock import AsyncMock, patch

import httpx
import pytest

from apps.api.features.retrieval.normalizers import normalize_core_work
from apps.api.features.retrieval.source_clients import AcademicSourceClient
from apps.api.shared.settings import Settings


def test_normalize_core_work_maps_fields():
    work = {
        "id": 275187148,
        "title": "Graph neural recommender systems",
        "abstract": "We study GNN recommenders.",
        "authors": [{"name": "Alice Smith"}, {"name": "Bob Jones"}],
        "yearPublished": 2023,
        "journals": [{"title": "RecSys Journal"}],
        "doi": "10.1145/1234567.1234567",
        "citationCount": 42,
        "downloadUrl": "https://core.ac.uk/download/example.pdf",
    }
    result = normalize_core_work(work)
    assert result is not None
    assert result["source"] == "core"
    assert result["external_id"] == "275187148"
    assert result["doi"] == "10.1145/1234567.1234567"
    assert result["authors"] == ["Alice Smith", "Bob Jones"]
    assert result["venue"] == "RecSys Journal"
    assert result["url"] == "https://core.ac.uk/download/example.pdf"
    assert result["citation_count"] == 42


def test_normalize_core_work_missing_title_returns_none():
    assert normalize_core_work({"id": 1}) is None


@pytest.mark.asyncio
async def test_fetch_core_skips_without_api_key():
    settings = Settings(core_api_key="")
    client = AcademicSourceClient(settings, article_age_cutoff=2020)
    async with httpx.AsyncClient() as http_client:
        results = await client.fetch_core(http_client, "machine learning", limit=10)
    assert results == []


@pytest.mark.asyncio
async def test_fetch_core_parses_search_response():
    settings = Settings(core_api_key="test-key")
    source_client = AcademicSourceClient(settings, article_age_cutoff=2020)
    payload = {
        "totalHits": 1,
        "results": [
            {
                "id": 123,
                "title": "Open access paper",
                "abstract": "Summary text.",
                "authors": [{"name": "Jane Doe"}],
                "yearPublished": 2024,
                "citationCount": 3,
            }
        ],
    }
    mock_response = httpx.Response(200, json=payload, request=httpx.Request("GET", "https://example.com"))

    with patch(
        "apps.api.features.retrieval.source_clients.get_with_retry",
        new=AsyncMock(return_value=mock_response),
    ) as mock_get:
        async with httpx.AsyncClient() as http_client:
            results = await source_client.fetch_core(http_client, "open access", limit=5, pass_kind="sota")

    assert len(results) == 1
    assert results[0]["source"] == "core"
    assert results[0]["title"] == "Open access paper"
    mock_get.assert_awaited_once()
    call_kwargs = mock_get.await_args.kwargs
    assert call_kwargs["params"]["sort"] == "recency"
    assert call_kwargs["headers"]["Authorization"] == "Bearer test-key"


@pytest.mark.asyncio
async def test_build_jobs_includes_core_when_api_key_configured(monkeypatch):
    from apps.api.features.retrieval.service import RetrievalService

    service = RetrievalService()

    class _Settings:
        dual_retrieval_enabled = True
        retrieval_learned_topic_cap = 2
        retrieval_crossref_max_queries = 2
        retrieval_core_max_queries = 2
        retrieval_openalex_per_page_max = 100
        retrieval_crossref_rows_max = 80
        retrieval_semantic_scholar_limit_max = 100
        retrieval_core_limit_max = 100
        retrieval_arxiv_max_results = 40
        retrieval_source_priority = "openalex,crossref,semantic_scholar,core,arxiv"
        core_api_key = "configured"

    monkeypatch.setattr(service, "settings", _Settings())

    jobs = service._build_jobs_from_plan(
        ["graph neural networks"],
        fetch_target=100,
        research_area="Recommender Systems",
        learned_topics=None,
    )

    assert "core" in {job.source for job in jobs}
    assert sum(1 for job in jobs if job.source == "core") <= 2
