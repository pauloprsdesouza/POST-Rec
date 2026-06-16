"""Tests for worker run context resolution."""

from unittest.mock import MagicMock
from uuid import uuid4

from apps.api.shared.models import RecommendationRun, UserResearchProfile
from apps.api.workers.tasks import _resolve_run_context


def test_resolve_run_context_uses_profile_when_no_expectation():
    db = MagicMock()
    profile = UserResearchProfile(
        user_id=uuid4(),
        research_area="Recommender Systems",
        learned_topics=["collaborative filtering"],
        avoided_topics=["quantum physics"],
        recommendation_defaults={
            "expected_output": "research ideas",
            "desired_depth": "shallow",
            "max_article_age_years": 5,
        },
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

    expanded, constraints, expectation, research_area, learned, avoided, age, expected_output, depth = (
        _resolve_run_context(
            db,
            run,
            run.input["topics"],
            run.input["constraints"],
        )
    )

    assert expectation is None
    assert research_area == "Recommender Systems"
    assert expected_output == "research ideas"
    assert depth == "shallow"
    assert "Social Capital" in expanded
    assert len(expanded) > len(run.input["topics"])
    assert age == 5
