"""Tests for consolidated fetch job planning."""

from apps.api.features.retrieval.service import RetrievalService

_OPENALEX_JOB_SETTINGS = {
    "retrieval_openalex_filter_tier": "balanced",
    "retrieval_openalex_use_search": True,
}


def _settings(**overrides):
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
        retrieval_source_priority = "openalex"
        retrieval_openalex_enabled = True
        retrieval_crossref_enabled = False
        retrieval_arxiv_enabled = False
        retrieval_core_enabled = False
        retrieval_semantic_scholar_enabled = False
        retrieval_openalex_filter_tier = _OPENALEX_JOB_SETTINGS["retrieval_openalex_filter_tier"]
        retrieval_openalex_use_search = _OPENALEX_JOB_SETTINGS["retrieval_openalex_use_search"]
        core_api_key = ""

    for key, value in overrides.items():
        setattr(_Settings, key, value)
    return _Settings()


def test_build_jobs_from_plan_openalex_only_by_default(monkeypatch):
    service = RetrievalService()
    monkeypatch.setattr(service, "settings", _settings())

    jobs = service._build_jobs_from_plan(
        ["graph neural networks"],
        fetch_target=100,
        research_area="Recommender Systems",
        learned_topics=["collaborative filtering"],
    )

    sources = {job.source for job in jobs}
    assert sources == {"openalex"}
    assert all(job.research_area == "Recommender Systems" for job in jobs)
    assert len(jobs) < 25


def test_build_jobs_from_plan_reduces_fan_out(monkeypatch):
    service = RetrievalService()
    monkeypatch.setattr(
        service,
        "settings",
        _settings(
            retrieval_source_priority="openalex,crossref,semantic_scholar,core,arxiv",
            retrieval_crossref_enabled=True,
            retrieval_arxiv_enabled=True,
            retrieval_semantic_scholar_enabled=True,
        ),
    )

    jobs = service._build_jobs_from_plan(
        ["graph neural networks"],
        fetch_target=100,
        research_area="Recommender Systems",
        learned_topics=["collaborative filtering"],
    )

    sources = {job.source for job in jobs}
    assert "openalex" in sources
    assert "semantic_scholar" in sources
    assert len(jobs) < 25
    assert sum(1 for job in jobs if job.source == "arxiv") <= 1


def test_build_fetch_jobs_uses_consolidated_plan(monkeypatch):
    service = RetrievalService()
    monkeypatch.setattr(
        service,
        "settings",
        _settings(
            retrieval_source_priority="openalex,crossref,semantic_scholar,core,arxiv",
            retrieval_crossref_enabled=True,
            retrieval_arxiv_enabled=True,
            retrieval_semantic_scholar_enabled=True,
        ),
    )

    jobs = service._build_fetch_jobs(
        ["topic a", "topic b"],
        100,
        research_area=None,
        learned_topics=None,
    )
    assert len(jobs) > 0
    assert len(jobs) < 25


def test_build_jobs_from_plan_excludes_semantic_scholar_by_default(monkeypatch):
    service = RetrievalService()
    monkeypatch.setattr(
        service,
        "settings",
        _settings(retrieval_source_priority="openalex,crossref,core,arxiv"),
    )

    jobs = service._build_jobs_from_plan(
        ["graph neural networks"],
        fetch_target=100,
        research_area="Recommender Systems",
        learned_topics=None,
    )

    assert "semantic_scholar" not in {job.source for job in jobs}
