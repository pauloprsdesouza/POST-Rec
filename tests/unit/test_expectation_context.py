"""Tests for session expectation constraint merging."""

from types import SimpleNamespace

from packages.postrec_core.domain.expectation_context import (
    format_user_expectations,
    merge_expectation_into_constraints,
)


def test_merge_expectation_into_constraints():
    expectation = SimpleNamespace(
        preferred_validation=["simulation", "benchmark"],
        publication_goal="workshop paper",
        expects_original_ideas=True,
        expects_datasets=True,
        expects_experimental_plan=False,
        expects_references=True,
        avoid_real_user_experiments=True,
    )

    merged = merge_expectation_into_constraints(
        expectation,
        {"prefer_public_datasets": True},
    )

    assert merged["preferred_validation"] == ["simulation", "benchmark"]
    assert merged["publication_goal"] == "workshop paper"
    assert merged["expects_original_ideas"] is True
    assert merged["expects_datasets"] is True
    assert merged["expects_experimental_plan"] is False
    assert merged["avoid_real_user_experiments"] is True


def test_format_user_expectations():
    text = format_user_expectations(
        {
            "publication_goal": "journal",
            "expects_references": True,
            "avoid_real_user_experiments": True,
        }
    )

    assert "Publication goal: journal" in text
    assert "references" in text.lower()
    assert "user studies" in text.lower()
