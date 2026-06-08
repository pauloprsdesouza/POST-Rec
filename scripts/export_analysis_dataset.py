#!/usr/bin/env python3
"""Export analysis-ready datasets for offline research."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from apps.api.shared.database import SessionLocal
from apps.api.features.validation.analysis_service import analysis_data_service


def export_analysis_dataset(output_dir: str = "analysis/exports") -> None:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    db = SessionLocal()
    try:
        dataset = analysis_data_service.load_dataset(db)
        from datetime import UTC, datetime

        manifest = {
            "exported_at": datetime.now(UTC).isoformat(),
            "sessions": len(dataset["sessions"]),
            "runs": len(dataset["runs"]),
            "feedback": len(dataset["feedback"]),
            "surveys": len(dataset["surveys"]),
            "candidates": len(dataset["candidates"]),
        }

        (out / "analysis_manifest.json").write_text(
            json.dumps(manifest, indent=2),
            encoding="utf-8",
        )
        (out / "full_dataset.json").write_text(
            json.dumps(dataset, indent=2, default=str),
            encoding="utf-8",
        )

        for name, rows in (
            ("feedback_long", dataset["feedback"]),
            ("runs", dataset["runs"]),
            ("candidates", dataset["candidates"]),
            ("surveys", dataset["surveys"]),
            ("sessions", dataset["sessions"]),
        ):
            if not rows:
                continue
            path = out / f"{name}.csv"
            with path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
                writer.writeheader()
                writer.writerows(rows)

        print(f"Exported analysis dataset to {out.resolve()}")
    finally:
        db.close()


if __name__ == "__main__":
    export_analysis_dataset(sys.argv[1] if len(sys.argv) > 1 else "analysis/exports")
