"""Tests for OpenAlex fetch job planning."""

from apps.api.features.retrieval.service import RetrievalService


def _settings(**overrides):
    class _Settings:
        dual_retrieval_enabled = True
        retrieval_learned_topic_cap = 2
        retrieval_openalex_per_page_max = 100
        retrieval_openalex_filter_tier = "balanced"
        retrieval_openalex_use_search = True

    for key, value in overrides.items():
        setattr(_Settings, key, value)
    return _Settings()


def test_build_jobs_from_plan_openalex_only(monkeypatch):
    service = RetrievalService()
    monkeypatch.setattr(service, "settings", _settings())

    jobs = service._build_jobs_from_plan(
        ["graph neural networks"],
        fetch_target=100,
        research_area="Recommender Systems",
        learned_topics=["collaborative filtering"],
    )

    assert {job.source for job in jobs} == {"openalex"}
    assert all(job.research_area == "Recommender Systems" for job in jobs)
    assert all(job.openalex_tier == "balanced" for job in jobs)
    assert len(jobs) < 10
