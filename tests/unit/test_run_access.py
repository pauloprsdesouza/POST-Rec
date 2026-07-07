"""Tests for run access control."""

import uuid
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from apps.api.features.runs.access import ensure_run_access
from apps.api.shared.models import RecommendationRun, User


def _run(user_id: uuid.UUID | None) -> RecommendationRun:
    return RecommendationRun(
        id=uuid.uuid4(),
        user_id=user_id,
        input={},
        mode="quick",
        status="completed",
        progress=100,
        max_papers=10,
        max_recommendations=5,
    )


def _user() -> User:
    return User(id=uuid.uuid4(), email="user@example.com", full_name="User")


def test_anonymous_run_allows_unauthenticated_access():
    ensure_run_access(_run(None), None)


def test_anonymous_run_allows_authenticated_access():
    user = _user()
    ensure_run_access(_run(None), user)


def test_owned_run_requires_authentication():
    owner_id = uuid.uuid4()
    with pytest.raises(HTTPException) as exc:
        ensure_run_access(_run(owner_id), None)
    assert exc.value.status_code == 401


def test_owned_run_denies_other_users():
    owner = _user()
    other = User(id=uuid.uuid4(), email="other@example.com", full_name="Other")
    with pytest.raises(HTTPException) as exc:
        ensure_run_access(_run(owner.id), other)
    assert exc.value.status_code == 403


def test_owned_run_allows_owner():
    owner = _user()
    ensure_run_access(_run(owner.id), owner)
