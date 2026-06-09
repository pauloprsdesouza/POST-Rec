"""Tests for run retry, archive, and learned-topic cleanup."""

import uuid
from datetime import UTC, datetime

from apps.api.features.profile.service import ProfileService
from apps.api.features.runs.cleanup import (
    is_run_cancellable,
    is_run_retryable,
    learned_topics_matching_run,
)
from apps.api.shared.models import RecommendationCandidate, RecommendationRun, UserResearchProfile


def test_is_run_retryable_for_failed_and_incomplete():
    assert is_run_retryable("failed", 0) is True
    assert is_run_retryable("cancelled", 0) is True
    assert is_run_retryable("cost_limit_exceeded", 0) is True
    assert is_run_retryable("completed", 0) is True
    assert is_run_retryable("completed", 3) is False
    assert is_run_retryable("generating_recommendations", 0) is False


def test_is_run_cancellable_only_for_active_pipeline():
    assert is_run_cancellable("queued") is True
    assert is_run_cancellable("searching_papers") is True
    assert is_run_cancellable("completed") is False
    assert is_run_cancellable("failed") is False


def test_learned_topics_matching_run_uses_topics_and_candidates():
    run = RecommendationRun(
        id=uuid.uuid4(),
        input={"topics": ["Graph Neural Networks", "social capital"]},
        mode="quick",
        status="completed",
        progress=100,
        max_papers=10,
        max_recommendations=5,
    )
    candidates = [
        RecommendationCandidate(
            run_id=run.id,
            title="Contrastive learning for recommender systems in large graphs",
            technique_name="Contrastive Learning",
            status="published",
        )
    ]
    profile = UserResearchProfile(
        user_id=uuid.uuid4(),
        learned_topics=["Social Capital", "Contrastive Learning", "unrelated topic"],
    )

    matched = learned_topics_matching_run(profile, run, candidates)

    assert matched == ["Contrastive Learning", "Social Capital"]


class _FakeProfileQuery:
    def __init__(self, profile):
        self._profile = profile

    def filter_by(self, **_kwargs):
        return self

    def first(self):
        return self._profile


class _FakeCandidateQuery:
    def __init__(self, candidates):
        self._candidates = candidates

    def filter_by(self, **_kwargs):
        return self

    def all(self):
        return self._candidates


class _FakeSession:
    def __init__(self, profile, candidates):
        self._profile = profile
        self._candidates = candidates
        self.committed = False

    def query(self, model):
        if model is UserResearchProfile:
            return _FakeProfileQuery(self._profile)
        if model is RecommendationCandidate:
            return _FakeCandidateQuery(self._candidates)
        raise AssertionError(f"Unexpected model {model}")

    def commit(self):
        self.committed = True

    def refresh(self, _obj):
        return None


def test_remove_learned_topics_is_case_insensitive():
    profile = UserResearchProfile(
        user_id=uuid.uuid4(),
        learned_topics=["Graph Neural Networks", "Social Capital"],
        preferred_techniques=["Contrastive Learning"],
    )
    db = _FakeSession(profile, [])
    service = ProfileService()

    updated = service.remove_learned_topics(
        db,
        profile.user_id,
        ["social capital", "contrastive learning"],
    )

    assert updated.learned_topics == ["Graph Neural Networks"]
    assert updated.preferred_techniques == []
    assert db.committed is True
