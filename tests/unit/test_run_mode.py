"""Unit tests for run mode domain."""

from packages.postrec_core.domain.run_mode import RunMode


def test_run_mode_parse_defaults_to_quick():
    assert RunMode.parse(None) == RunMode.QUICK
    assert RunMode.parse("unknown") == RunMode.QUICK


def test_run_mode_parse_accepts_values():
    assert RunMode.parse("sota") == RunMode.SOTA
    assert RunMode.parse("EXPLORATORY") == RunMode.EXPLORATORY
    assert RunMode.parse("fggv") == RunMode.FGGV


def test_run_mode_pipeline_flags():
    assert RunMode.QUICK.uses_full_sota_pipeline is False
    assert RunMode.SOTA.uses_full_sota_pipeline is True
    assert RunMode.EXPLORATORY.uses_full_sota_pipeline is True
    assert RunMode.FGGV.uses_full_sota_pipeline is True
    assert RunMode.FGGV.uses_fggv_verification is True
    assert RunMode.SOTA.strict_critic is True
    assert RunMode.FGGV.strict_critic is True
    assert RunMode.EXPLORATORY.strict_critic is False
