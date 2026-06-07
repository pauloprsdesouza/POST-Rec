"""Feedback-driven ranking weight calibration."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from apps.api.models import RecommendationCandidate, RecommendationFeedback
from apps.api.observability.logging import get_logger
from packages.postrec_core.domain.run_mode import RunMode
from packages.postrec_core.scoring.ranking_weights import RankingWeights, weights_for_mode

logger = get_logger("postrec-ranking-calibration")

CALIBRATION_PATH = Path(__file__).resolve().parents[3] / "data" / "ranking_weights_calibrated.json"


def _positive_label(feedback: RecommendationFeedback) -> bool:
    return feedback.decision in {"approved", "save"} or (feedback.would_use_in_real_paper or "") == "yes"


class RankingCalibrationService:
    """Fit lightweight ranking weight adjustments from user feedback."""

    def load_calibrated_weights(self, mode: str) -> RankingWeights | None:
        if not CALIBRATION_PATH.exists():
            return None
        try:
            payload = json.loads(CALIBRATION_PATH.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
        mode_weights = payload.get("modes", {}).get(mode)
        if not isinstance(mode_weights, dict):
            mode_weights = payload.get(mode)
        if not isinstance(mode_weights, dict):
            return None
        try:
            return RankingWeights(**mode_weights)
        except TypeError:
            return None

    def calibrate(self, db: Session) -> dict[str, Any]:
        feedback_rows = db.query(RecommendationFeedback).all()
        if not feedback_rows:
            return {"updated": False, "reason": "no_feedback"}

        by_mode: dict[str, list[tuple[float, float, float, bool]]] = {}
        for feedback in feedback_rows:
            candidate = db.query(RecommendationCandidate).filter_by(id=feedback.recommendation_id).first()
            if not candidate or not candidate.scores:
                continue
            run = candidate.run
            mode = run.mode if run else "quick"
            scores = candidate.scores
            novelty_verified = float(scores.get("novelty_verified") or 0) / 100.0
            sota_fit = float(scores.get("sota_fit") or 0) / 100.0
            feasibility = float(scores.get("feasibility") or 0) / 100.0
            by_mode.setdefault(mode, []).append((novelty_verified, sota_fit, feasibility, _positive_label(feedback)))

        calibrated: dict[str, dict[str, float]] = {}
        for mode, rows in by_mode.items():
            if len(rows) < 5:
                continue
            positives = [row for row in rows if row[3]]
            negatives = [row for row in rows if not row[3]]
            if not positives or not negatives:
                continue

            base = weights_for_mode(RunMode.parse(mode))
            pos_novelty = sum(r[0] for r in positives) / len(positives)
            neg_novelty = sum(r[0] for r in negatives) / len(negatives)
            pos_sota = sum(r[1] for r in positives) / len(positives)
            neg_sota = sum(r[1] for r in negatives) / len(negatives)

            novelty_verified_w = min(0.22, max(0.08, base.novelty_verified + (pos_novelty - neg_novelty) * 0.08))
            sota_fit_w = min(0.22, max(0.08, base.sota_fit + (pos_sota - neg_sota) * 0.08))

            adjusted = RankingWeights(
                relevance=base.relevance,
                novelty=base.novelty,
                evidence=base.evidence,
                feasibility=base.feasibility,
                trend=base.trend,
                publication_potential=base.publication_potential,
                strategic_fit=base.strategic_fit,
                sota_fit=round(sota_fit_w, 4),
                novelty_verified=round(novelty_verified_w, 4),
            )
            calibrated[mode] = asdict(adjusted)

        if not calibrated:
            return {"updated": False, "reason": "insufficient_labeled_feedback"}

        CALIBRATION_PATH.parent.mkdir(parents=True, exist_ok=True)
        payload = {"version": 1, "modes": calibrated}
        CALIBRATION_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        logger.info("ranking_weights_calibrated", modes=list(calibrated.keys()))
        return {"updated": True, "modes": list(calibrated.keys()), "path": str(CALIBRATION_PATH)}


ranking_calibration_service = RankingCalibrationService()
