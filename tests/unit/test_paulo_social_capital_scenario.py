"""Regression tests for Paulo's social-capital × recommender-systems scenario."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from apps.api.features.recommendations.article_validation import article_validation_service
from apps.api.features.retrieval.relevance import compute_relevance_score, filter_and_rank_papers
from packages.postrec_core.retrieval.domain_alignment import compute_domain_alignment
from apps.api.shared.models import RecommendationRun, UserResearchProfile
from apps.api.workers.tasks import _resolve_run_context

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "paulo_social_capital_recsys.json"


@pytest.fixture(autouse=True)
def _mock_qualis_boost():
    with patch(
        "apps.api.features.retrieval.relevance.qualis_service.apply_relevance_boost",
        side_effect=lambda score, paper: (score, {}),
    ):
        yield


@pytest.fixture
def paulo_scenario() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_paulo_fixture_papers_rank_recsys_social_capital_high(paulo_scenario):
    profile = paulo_scenario["profile"]
    papers = paulo_scenario["papers"]
    topics = profile["seed_topics"]

    on_topic = papers[0]
    off_topic = papers[3]
    partial = papers[4]

    on_score = compute_relevance_score(
        on_topic,
        topics=topics,
        research_area=profile["research_area"],
        learned_topics=profile["learned_topics"],
        avoided_topics=profile["avoided_topics"],
    )
    off_score = compute_relevance_score(
        off_topic,
        topics=topics,
        research_area=profile["research_area"],
        learned_topics=profile["learned_topics"],
        avoided_topics=profile["avoided_topics"],
    )
    partial_score = compute_relevance_score(
        partial,
        topics=topics,
        research_area=profile["research_area"],
    )

    assert on_score >= 0.35
    assert partial_score >= 0.22
    assert off_score < 0.22
    assert compute_domain_alignment(
        off_topic,
        profile["research_area"],
        topics=profile["seed_topics"],
    ).passes is False


def test_paulo_fixture_filter_keeps_recsys_social_papers(paulo_scenario):
    profile = paulo_scenario["profile"]
    ranked, stats = filter_and_rank_papers(
        paulo_scenario["papers"],
        topics=profile["seed_topics"],
        research_area=profile["research_area"],
        learned_topics=profile["learned_topics"],
        avoided_topics=profile["avoided_topics"],
        min_score=0.22,
    )
    titles = " ".join(p["title"].lower() for p in ranked)
    assert stats["kept"] >= 2
    assert "recommender" in titles
    assert all(p.get("domain_alignment_passes") for p in ranked)
    assert "sociolog" not in titles


@patch("apps.api.features.recommendations.article_validation.persist_article_validation_scores")
@patch("apps.api.features.recommendations.article_validation.get_settings")
@patch("apps.api.features.recommendations.article_validation.gemini_service")
def test_paulo_scenario_validation_with_research_area(mock_gemini, mock_settings, mock_persist, paulo_scenario):
    profile = paulo_scenario["profile"]
    papers = [{**p, "paper_id": f"P{i + 1}"} for i, p in enumerate(paulo_scenario["papers"][:3])]
    mock_settings.return_value = MagicMock(
        article_llm_validation_enabled=True,
        gemini_api_key="key",
        article_llm_min_relevance_score=0.42,
        article_min_valid_papers=2,
        article_sparse_corpus_threshold=12,
        article_grounding_best_effort_enabled=True,
        retrieval_min_relevance_score=0.22,
    )
    mock_gemini.validate_retrieved_papers.return_value = {
        "papers": [
            {**papers[0], "llm_relevance_score": 0.82, "llm_passes_validation": True},
            {**papers[1], "llm_relevance_score": 0.76, "llm_passes_validation": True},
            {**papers[2], "llm_relevance_score": 0.71, "llm_passes_validation": True},
        ],
        "validations": [],
        "sufficient_evidence": True,
    }

    filtered, stats = article_validation_service.validate_and_filter(
        MagicMock(),
        "run-paulo",
        papers,
        research_area=profile["research_area"],
        seed_topics=profile["seed_topics"],
        avoided_topics=profile["avoided_topics"],
    )

    assert stats["sufficient_evidence"] is True
    assert len(filtered) >= 2
    mock_gemini.validate_retrieved_papers.assert_called_once()
    assert mock_gemini.validate_retrieved_papers.call_args.kwargs["research_area"] == "Recommender Systems"


def test_resolve_run_context_uses_profile_when_no_expectation(paulo_scenario):
    db = MagicMock()
    profile = UserResearchProfile(
        user_id=uuid4(),
        research_area=paulo_scenario["profile"]["research_area"],
        learned_topics=paulo_scenario["profile"]["learned_topics"],
        avoided_topics=paulo_scenario["profile"]["avoided_topics"],
        recommendation_defaults=paulo_scenario["profile"]["recommendation_defaults"],
    )

    def _query(model):
        query = MagicMock()
        if model.__name__ == "SessionExpectation":
            query.filter_by.return_value.first.return_value = None
        else:
            query.filter_by.return_value.first.return_value = profile
        return query

    db.query.side_effect = _query

    run = RecommendationRun(
        user_id=profile.user_id,
        expectation_id=None,
        input={
            "topics": ["Social Capital", "Social Networks", "Profile Modeling"],
            "constraints": {"max_article_age_years": 5},
        },
    )

    expanded, constraints, expectation, research_area, learned, avoided, age, expected_output, depth = _resolve_run_context(
        db,
        run,
        run.input["topics"],
        run.input["constraints"],
    )

    assert expectation is None
    assert research_area == "Recommender Systems"
    assert expected_output == paulo_scenario["profile"]["recommendation_defaults"]["expected_output"]
    assert depth == "shallow"
    assert "Social Capital" in expanded
    assert len(expanded) > len(run.input["topics"])
    assert age == 5


@patch("apps.api.features.recommendations.article_validation.persist_article_validation_scores")
@patch("apps.api.features.recommendations.article_validation.get_settings")
def test_research_area_boosts_recsys_alignment(mock_settings, mock_persist, paulo_scenario):
    profile = paulo_scenario["profile"]
    papers = [{**p, "paper_id": f"P{i + 1}"} for i, p in enumerate(paulo_scenario["papers"][:3])]
    mock_settings.return_value = MagicMock(
        article_llm_validation_enabled=False,
        gemini_api_key="",
        article_llm_min_relevance_score=0.42,
        article_min_valid_papers=2,
        article_sparse_corpus_threshold=12,
        article_grounding_best_effort_enabled=True,
        retrieval_min_relevance_score=0.22,
    )

    filtered_area, stats_area = article_validation_service.validate_and_filter(
        MagicMock(),
        "run-with-area",
        list(papers),
        research_area=profile["research_area"],
        seed_topics=profile["seed_topics"],
        avoided_topics=profile["avoided_topics"],
    )

    assert stats_area["sufficient_evidence"] is True
    assert len(filtered_area) >= 2
    assert any("recommender" in paper["title"].lower() for paper in filtered_area)
