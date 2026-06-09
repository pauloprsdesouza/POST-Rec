#!/usr/bin/env python3
"""Generate full research report JSON for reviewers/co-authors."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from apps.api.shared.database import SessionLocal
from apps.api.features.validation.analysis_service import analysis_data_service


def generate_research_report(output_path: str = "analysis/outputs/research_report.json") -> None:
    db = SessionLocal()
    try:
        report = analysis_data_service.build_report(db)
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
        print(f"Research report written to {path.resolve()}")
        print(f"  Sessions: {report['sample']['sessions']}")
        print(f"  Feedback: {report['sample']['feedback']}")
        print(f"  NDCG@5: {report['ranking_metrics']['overall'].get('ndcg@5', 'N/A')}")
    finally:
        db.close()


if __name__ == "__main__":
    generate_research_report(sys.argv[1] if len(sys.argv) > 1 else "analysis/outputs/research_report.json")
