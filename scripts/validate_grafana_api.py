#!/usr/bin/env python3
"""Validate dashboard panels via Grafana datasource query API."""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

import paramiko
import requests

ROOT = Path(__file__).resolve().parents[1]
HOST = os.environ.get("HOMELAB_HOST", "")
GRAFANA_URL = os.environ.get("GRAFANA_URL", "")
GRAFANA_USER = os.environ.get("GRAFANA_USER", "admin")
GRAFANA_PASSWORD = os.environ.get("GRAFANA_PASSWORD", os.environ.get("SSH_PASSWORD", ""))
PWD = os.environ.get("SSH_PASSWORD", "")


def load_dashboard() -> dict:
    sys.path.insert(0, str(ROOT))
    from scripts.deploy_observability_homelab import load_dashboard_payload

    return load_dashboard_payload()


def grafana_query(ds_uid: str, raw_sql: str, fmt: str) -> dict:
    now_ms = int(time.time() * 1000)
    from_ms = now_ms - 90 * 86400 * 1000
    payload = {
        "queries": [
            {
                "refId": "A",
                "datasource": {"type": "grafana-postgresql-datasource", "uid": ds_uid},
                "rawSql": raw_sql,
                "format": fmt,
                "datasourceId": 0,
            }
        ],
        "from": str(from_ms),
        "to": str(now_ms),
    }
    resp = requests.post(
        f"{GRAFANA_URL}/api/ds/query",
        json=payload,
        auth=(GRAFANA_USER, GRAFANA_PASSWORD),
        timeout=60,
    )
    return {"status": resp.status_code, "body": resp.json() if resp.content else {}}


def main() -> int:
    global GRAFANA_URL

    if not GRAFANA_PASSWORD:
        print("Set GRAFANA_PASSWORD or SSH_PASSWORD", file=sys.stderr)
        return 1
    if not GRAFANA_URL:
        if not HOST:
            print("Set GRAFANA_URL or HOMELAB_HOST", file=sys.stderr)
            return 1
        GRAFANA_URL = f"http://{HOST}:3000"

    ds = requests.get(
        f"{GRAFANA_URL}/api/datasources/uid/postrec-postgres",
        auth=(GRAFANA_USER, GRAFANA_PASSWORD),
        timeout=30,
    )
    ds.raise_for_status()
    pg_uid = ds.json()["uid"]

    dash = load_dashboard()
    failures = []

    for panel in dash.get("panels", []):
        if panel.get("type") == "row":
            continue
        ds_type = (panel.get("datasource") or {}).get("type", "")
        if "postgres" not in ds_type:
            continue
        pid = panel.get("id")
        title = panel.get("title", "?")
        for target in panel.get("targets", []):
            raw = target.get("rawSql")
            if not raw:
                continue
            fmt = target.get("format", "table")
            result = grafana_query(pg_uid, raw, fmt)
            body = result["body"]
            if result["status"] != 200:
                failures.append((pid, title, f"HTTP {result['status']}", str(body)[:200]))
                print(f"[FAIL] {pid} {title} HTTP {result['status']}")
                continue
            # Check for error in results
            results = body.get("results", {}).get("A", {})
            if results.get("error"):
                failures.append((pid, title, results["error"], raw[:100]))
                print(f"[FAIL] {pid} {title}: {results['error']}")
            elif results.get("status") == 500:
                failures.append((pid, title, str(results), raw[:100]))
                print(f"[FAIL] {pid} {title}: {results}")
            else:
                frames = results.get("frames") or []
                print(f"[OK] {pid} {title} ({len(frames)} frame(s))")

    print(f"\n{len(failures)} Grafana query failure(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
