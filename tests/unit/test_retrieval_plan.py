"""Tests for consolidated retrieval plan."""

from packages.postrec_core.retrieval.retrieval_plan import (
    build_arxiv_search_query,
    build_retrieval_plan,
    should_include_arxiv,
)


def test_build_retrieval_plan_fewer_than_legacy_expansion():
    plan = build_retrieval_plan(
        ["graph neural networks", "collaborative filtering"],
        research_area="Recommender Systems",
        learned_topics=["matrix factorization", "session-based", "extra topic"],
        learned_topic_cap=2,
    )
    assert plan.searches
    assert len(plan.learned_queries) == 2
    job_estimate = sum(len(search.pass_kinds) for search in plan.searches) * 2
    job_estimate += len(plan.learned_queries) * 2
    if plan.arxiv_query:
        job_estimate += 1
    assert job_estimate < 30


def test_build_retrieval_plan_includes_intent_and_sota():
    plan = build_retrieval_plan(
        ["transformers for ranking"],
        research_area="Information Retrieval",
        dual_pass=True,
    )
    queries = [search.query.lower() for search in plan.searches]
    assert any("information retrieval" in q for q in queries)
    assert any("state of the art" in q for q in queries)


def test_should_include_arxiv_for_ml_topics():
    assert should_include_arxiv(["graph neural networks"], research_area="Recommender Systems")
    assert not should_include_arxiv(["medieval history"], research_area="Archaeology")


def test_build_arxiv_search_query_uses_title_and_abstract():
    query = build_arxiv_search_query("deep learning recommender")
    assert query.startswith("(ti:")
    assert " OR abs:" in query
