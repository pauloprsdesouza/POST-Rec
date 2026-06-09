"""Tests for blind A/B experiment assignment and presentation."""

from __future__ import annotations

from types import SimpleNamespace

from apps.api.features.experiments.assignment import (
    EXPERIMENT_VARIANT_CONTROL,
    EXPERIMENT_VARIANT_TREATMENT,
    PRESENTATION_BLIND,
    PRESENTATION_STANDARD,
    resolve_experiment_assignment,
)
from apps.api.features.experiments.presentation import (
    blind_recommendation_payload,
    blind_run_detail_payload,
    is_blind_run,
    sanitize_event_message,
)


def test_assignment_respects_opt_out():
    result = resolve_experiment_assignment(
        user_id="user-1",
        requested_mode="fggv",
        avoid_real_user_experiments=True,
        experiment_enabled=True,
        experiment_id="fggv_vs_sota_v1",
        treatment_fraction=0.5,
    )
    assert result.presentation_profile == PRESENTATION_STANDARD
    assert result.experiment_id is None
    assert result.mode == "fggv"


def test_assignment_is_sticky_per_user():
    first = resolve_experiment_assignment(
        user_id="sticky-user",
        requested_mode="quick",
        avoid_real_user_experiments=False,
        experiment_enabled=True,
        experiment_id="fggv_vs_sota_v1",
        treatment_fraction=0.5,
    )
    second = resolve_experiment_assignment(
        user_id="sticky-user",
        requested_mode="quick",
        avoid_real_user_experiments=False,
        experiment_enabled=True,
        experiment_id="fggv_vs_sota_v1",
        treatment_fraction=0.5,
    )
    assert first.experiment_variant == second.experiment_variant
    assert first.presentation_profile == PRESENTATION_BLIND
    assert first.mode in {"sota", "fggv"}


def test_assignment_all_control_when_treatment_fraction_zero():
    result = resolve_experiment_assignment(
        user_id="any-user",
        requested_mode="quick",
        avoid_real_user_experiments=False,
        experiment_enabled=True,
        experiment_id="fggv_vs_sota_v1",
        treatment_fraction=0.0,
    )
    assert result.experiment_variant == EXPERIMENT_VARIANT_CONTROL
    assert result.mode == "sota"


def test_assignment_all_treatment_when_treatment_fraction_one():
    result = resolve_experiment_assignment(
        user_id="any-user",
        requested_mode="quick",
        avoid_real_user_experiments=False,
        experiment_enabled=True,
        experiment_id="fggv_vs_sota_v1",
        treatment_fraction=1.0,
    )
    assert result.experiment_variant == EXPERIMENT_VARIANT_TREATMENT
    assert result.mode == "fggv"


def test_blind_recommendation_payload_strips_fggv_fields():
    payload = {
        "title": "Idea",
        "fggv_score": 88.0,
        "facet_novelty_index": 72.0,
        "gap_alignment_score": 65.0,
        "facet_deltas": {"method": "new"},
        "aligned_gaps": ["gap-1"],
        "sota_fit": 70.0,
        "scores": {"_fggv": {"x": 1}, "false_novel_facet_count": 1, "sota_fit": 70.0},
    }
    sanitized = blind_recommendation_payload(payload)
    assert "fggv_score" not in sanitized
    assert "facet_deltas" not in sanitized
    assert sanitized["sota_fit"] == 70.0
    assert sanitized["scores"] == {"sota_fit": 70.0}


def test_blind_run_detail_hides_mode_and_cost():
    payload = {
        "id": "run-id",
        "mode": "fggv",
        "estimated_cost_usd": 1.23,
        "usage": {"estimated_cost_usd": 1.23, "lines": []},
    }
    sanitized = blind_run_detail_payload(payload)
    assert "mode" not in sanitized
    assert sanitized["usage"] is None
    assert sanitized["estimated_cost_usd"] == 0.0
    assert sanitized["presentation_profile"] == PRESENTATION_BLIND


def test_is_blind_run_requires_experiment_id():
    run = SimpleNamespace(presentation_profile=PRESENTATION_BLIND, experiment_id="fggv_vs_sota_v1")
    assert is_blind_run(run) is True
    non_experiment = SimpleNamespace(presentation_profile=PRESENTATION_BLIND, experiment_id=None)
    assert is_blind_run(non_experiment) is False


def test_sanitize_event_message_replaces_fggv_terms():
    message = sanitize_event_message("FGGV facet critic finished gap matrix stage")
    assert "FGGV" not in message
    assert "facet" not in message.lower()
    assert "gap matrix" not in message.lower()
