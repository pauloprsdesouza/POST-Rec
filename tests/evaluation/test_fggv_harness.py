"""Evaluation harness tests on golden fixture."""

from packages.postrec_core.evaluation.harness import run_offline_evaluation


def test_offline_evaluation_fggv_separates_good_from_weak():
    report = run_offline_evaluation()
    fggv = report["summary"]["m_fggv"]
    assert fggv["delta"] > 25
    assert fggv["good_mean"] > fggv["weak_mean"]
    assert fggv["separation_ratio"] > 0.75
