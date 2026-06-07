#!/usr/bin/env python3
"""Export anonymized validation data for analysis."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from apps.api.shared.database import SessionLocal
from apps.api.shared.models import RecommendationFeedback, SessionFinalSurvey, VolunteerSession


def export_anonymized(output_path: str = "validation_export.json") -> None:
    db = SessionLocal()
    try:
        data = {
            "sessions": [
                {
                    "id": str(s.id),
                    "status": s.status,
                    "started_at": s.started_at.isoformat() if s.started_at else None,
                }
                for s in db.query(VolunteerSession).all()
            ],
            "feedbacks": [
                {
                    "relevance_score": f.relevance_score,
                    "originality_score": f.originality_score,
                    "clarity_score": f.clarity_score,
                    "feasibility_score": f.feasibility_score,
                    "trust_score": f.trust_score,
                    "usefulness_score": f.usefulness_score,
                    "would_use_in_real_paper": f.would_use_in_real_paper,
                    "decision": f.decision,
                    "expectation_alignment_score": float(f.expectation_alignment_score or 0),
                }
                for f in db.query(RecommendationFeedback).all()
            ],
            "surveys": [
                {
                    "expectation_met_score": s.expectation_met_score,
                    "would_use_again": s.would_use_again,
                    "would_recommend": s.would_recommend,
                }
                for s in db.query(SessionFinalSurvey).all()
            ],
        }
        Path(output_path).write_text(json.dumps(data, indent=2), encoding="utf-8")
        print(f"Exported to {output_path}")
    finally:
        db.close()


if __name__ == "__main__":
    export_anonymized(sys.argv[1] if len(sys.argv) > 1 else "validation_export.json")
