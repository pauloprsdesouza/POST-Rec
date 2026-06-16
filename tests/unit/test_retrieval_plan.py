"""Tests for consolidated OpenAlex retrieval plan."""

from packages.postrec_core.retrieval.retrieval_plan import build_retrieval_plan


def test_build_retrieval_plan_fewer_than_legacy_expansion():
    plan = build_retrieval_plan(
        ["graph neural networks", "collaborative filtering"],
        research_area="Recommender Systems",
        learned_topics=["matrix factorization", "session-based", "extra topic"],
        learned_topic_cap=2,
    )
    assert plan.searches
    assert len(plan.learned_queries) == 2
    job_estimate = sum(len(search.pass_kinds) for search in plan.searches)
    job_estimate += len(plan.learned_queries)
    assert job_estimate < 15


def test_build_retrieval_plan_includes_intent_and_sota():
    plan = build_retrieval_plan(
        ["transformers for ranking"],
        research_area="Information Retrieval",
        dual_pass=True,
    )
    queries = [search.query.lower() for search in plan.searches]
    assert any("information retrieval" in q for q in queries)
    assert any("state of the art" in q for q in queries)
