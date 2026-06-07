"""Tests for ranking calibration service."""

import json
from unittest.mock import MagicMock

from apps.api.features.feedback.calibration import RankingCalibrationService


def test_load_calibrated_weights_reads_modes_key(tmp_path, monkeypatch):
    path = tmp_path / "ranking_weights_calibrated.json"
    path.write_text(
        json.dumps(
            {
                "version": 1,
                "modes": {
                    "quick": {
                        "relevance": 0.18,
                        "novelty": 0.12,
                        "evidence": 0.13,
                        "feasibility": 0.12,
                        "trend": 0.08,
                        "publication_potential": 0.08,
                        "strategic_fit": 0.08,
                        "sota_fit": 0.15,
                        "novelty_verified": 0.16,
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "apps.api.features.feedback.calibration.CALIBRATION_PATH",
        path,
    )
    service = RankingCalibrationService()
    weights = service.load_calibrated_weights("quick")
    assert weights is not None
    assert weights.sota_fit == 0.15


def test_compute_sota_quality_metrics_empty_db():
    from apps.api.features.validation.metrics import compute_sota_quality_metrics

    db = MagicMock()
    db.query.return_value.scalar.return_value = 0
    metrics = compute_sota_quality_metrics(db)
    assert metrics["sota_anchor_rate"] == 0.0
