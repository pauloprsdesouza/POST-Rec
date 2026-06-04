#!/usr/bin/env python3
"""Run offline baseline vs FGGV evaluation and print paper-ready summary."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from packages.postrec_core.evaluation.harness import run_offline_evaluation


def main() -> int:
    parser = argparse.ArgumentParser(description="Offline evaluation: baselines vs FGGV")
    parser.add_argument(
        "--fixture",
        type=Path,
        default=None,
        help="Path to golden_eval_topics.json",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Write full JSON report to this path",
    )
    parser.add_argument(
        "--ablations",
        action="store_true",
        help="Include FGGV ablation methods in the report",
    )
    args = parser.parse_args()

    report = run_offline_evaluation(args.fixture, include_ablations=args.ablations)
    print(json.dumps(report["summary"], indent=2))
    if report.get("sota_positioning"):
        print("\n--- positioning ---")
        print(json.dumps(report["sota_positioning"], indent=2))

    if args.output:
        args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"\nFull report written to {args.output}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
