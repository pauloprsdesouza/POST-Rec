#!/usr/bin/env python3
"""Import homelab POST-Rec Grafana dashboard to a running Grafana instance."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.grafana_dashboard import import_homelab_dashboard, write_merged_dashboard


def main() -> int:
    parser = argparse.ArgumentParser(description="Import POST-Rec ops+business Grafana dashboard")
    parser.add_argument("--url", default=os.environ.get("GRAFANA_URL", ""))
    parser.add_argument("--user", default=os.environ.get("GRAFANA_USER", "admin"))
    parser.add_argument("--password", default=os.environ.get("GRAFANA_PASSWORD", ""))
    parser.add_argument("--write-file", action="store_true", help="Also write merged JSON for file provisioning")
    parser.add_argument("--ops-only", action="store_true", help="Skip homelab business panels")
    args = parser.parse_args()

    if not args.url:
        print("Error: set --url or GRAFANA_URL", file=sys.stderr)
        return 1
    if not args.password:
        print("Error: set --password or GRAFANA_PASSWORD", file=sys.stderr)
        return 1

    if args.write_file:
        path = write_merged_dashboard()
        print(f"Wrote {path}")

    result = import_homelab_dashboard(
        args.url,
        user=args.user,
        password=args.password,
        include_business=not args.ops_only,
    )
    print(f"Imported dashboard: {args.url.rstrip('/')}{result.get('url', '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
