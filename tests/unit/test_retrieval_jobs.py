"""Tests for consolidated fetch job planning."""

from apps.api.features.retrieval.service import RetrievalService


def test_build_jobs_from_plan_reduces_fan_out(monkeypatch):
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
        core_api_key = ""

    monkeypatch.setattr(service, "settings", _Settings())

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
        core_api_key = ""

    monkeypatch.setattr(service, "settings", _Settings())

    jobs = service._build_fetch_jobs(
        ["topic a", "topic b"],
        100,
        research_area=None,
        learned_topics=None,
    )
    assert len(jobs) > 0
    assert len(jobs) < 25
