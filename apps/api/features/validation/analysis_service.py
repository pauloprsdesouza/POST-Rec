"""Load analysis datasets from the database."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from apps.api.shared.models import (
    LLMUsage,
    RecommendationCandidate,
    RecommendationFeedback,
    RecommendationRun,
    SessionFinalSurvey,
    StudySession,
)
from packages.postrec_core.evaluation.report_builder import build_research_report


def _flatten_candidate(candidate: RecommendationCandidate) -> dict[str, Any]:
    scores = candidate.scores if isinstance(candidate.scores, dict) else {}
    sota = scores.get("_sota") if isinstance(scores.get("_sota"), dict) else {}
    fggv = scores.get("_fggv") if isinstance(scores.get("_fggv"), dict) else {}
    anchors = sota.get("sota_anchors") or []

    return {
        "id": str(candidate.id),
        "run_id": str(candidate.run_id),
        "title": candidate.title,
        "status": candidate.status,
        "final_score": float(candidate.final_score) if candidate.final_score is not None else None,
        "has_sota_anchor": bool(anchors),
        "novelty_verified": _score_value(scores, "novelty_verified"),
        "sota_fit": _score_value(scores, "sota_fit"),
        "facet_novelty_index": _score_value(scores, "facet_novelty_index") or _score_value(fggv, "facet_novelty_index"),
        "gap_alignment_score": _score_value(scores, "gap_alignment_score") or _score_value(fggv, "gap_alignment_score"),
        "fggv_score": _score_value(scores, "fggv_score") or _score_value(fggv, "fggv_score"),
        "created_at": candidate.created_at.isoformat() if candidate.created_at else None,
    }


def _score_value(scores: dict, key: str) -> float | None:
    value = scores.get(key)
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


class AnalysisDataService:
    def load_dataset(self, db: Session) -> dict[str, Any]:
        sessions = [
            {
                "id": str(s.id),
                "status": s.status,
                "started_at": s.started_at.isoformat() if s.started_at else None,
                "finished_at": s.finished_at.isoformat() if s.finished_at else None,
            }
            for s in db.query(StudySession).all()
        ]

        runs = [
            {
                "id": str(r.id),
                "mode": r.mode,
                "assigned_mode": r.assigned_mode,
                "status": r.status,
                "experiment_id": r.experiment_id,
                "experiment_variant": r.experiment_variant,
                "estimated_cost_usd": float(r.estimated_cost_usd or 0),
                "max_recommendations": r.max_recommendations,
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "started_at": r.started_at.isoformat() if r.started_at else None,
                "finished_at": r.finished_at.isoformat() if r.finished_at else None,
            }
            for r in db.query(RecommendationRun).all()
        ]

        llm_usage = [
            {
                "run_id": str(row.run_id) if row.run_id else None,
                "provider": row.provider,
                "model": row.model,
                "operation": row.operation,
                "input_tokens": row.input_tokens,
                "output_tokens": row.output_tokens,
                "total_tokens": row.total_tokens,
                "estimated_cost_usd": float(row.estimated_cost_usd or 0),
            }
            for row in db.query(LLMUsage).all()
        ]

        feedback = [
            {
                "id": str(f.id),
                "run_id": str(f.run_id),
                "recommendation_id": str(f.recommendation_id),
                "session_id": str(f.session_id),
                "relevance_score": f.relevance_score,
                "originality_score": f.originality_score,
                "clarity_score": f.clarity_score,
                "feasibility_score": f.feasibility_score,
                "trust_score": f.trust_score,
                "usefulness_score": f.usefulness_score,
                "would_use_in_real_paper": f.would_use_in_real_paper,
                "decision": f.decision,
                "comment": f.comment,
                "expectation_alignment_score": float(f.expectation_alignment_score or 0),
                "created_at": f.created_at.isoformat() if f.created_at else None,
            }
            for f in db.query(RecommendationFeedback).all()
        ]

        surveys = [
            {
                "id": str(s.id),
                "session_id": str(s.session_id),
                "run_id": str(s.run_id) if s.run_id else None,
                "expectation_met_score": s.expectation_met_score,
                "would_use_again": s.would_use_again,
                "would_recommend": s.would_recommend,
                "would_use_any_recommendation_in_real_paper": s.would_use_any_recommendation_in_real_paper,
                "most_useful_recommendation_id": str(s.most_useful_recommendation_id)
                if s.most_useful_recommendation_id
                else None,
                "what_helped_most": s.what_helped_most,
                "what_hurt_most": s.what_hurt_most,
                "free_comment": s.free_comment,
                "created_at": s.created_at.isoformat() if s.created_at else None,
            }
            for s in db.query(SessionFinalSurvey).all()
        ]

        candidates = [_flatten_candidate(c) for c in db.query(RecommendationCandidate).all()]
        expert_labels = self._load_expert_labels()

        return {
            "sessions": sessions,
            "runs": runs,
            "feedback": feedback,
            "surveys": surveys,
            "candidates": candidates,
            "expert_labels": expert_labels,
            "llm_usage": llm_usage,
        }

    def build_report(self, db: Session) -> dict[str, Any]:
        dataset = self.load_dataset(db)
        return build_research_report(dataset)

    def _load_expert_labels(self) -> list[dict[str, Any]]:
        path = Path(__file__).resolve().parents[4] / "data" / "expert_labels.json"
        if not path.exists():
            template = Path(__file__).resolve().parents[4] / "data" / "expert_labels_template.json"
            if template.exists():
                path = template
            else:
                return []
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            return payload.get("ratings") or []
        except (json.JSONDecodeError, OSError):
            return []


analysis_data_service = AnalysisDataService()
