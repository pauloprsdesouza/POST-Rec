#!/usr/bin/env python3
"""Validate Prometheus and Loki panels on the ops dashboard."""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
GRAFANA_URL = os.environ.get("GRAFANA_URL", "")
GRAFANA_USER = os.environ.get("GRAFANA_USER", "admin")
GRAFANA_PASSWORD = os.environ.get("GRAFANA_PASSWORD", os.environ.get("SSH_PASSWORD", ""))


def main() -> int:
    global GRAFANA_URL

    if not GRAFANA_PASSWORD:
        print("Set GRAFANA_PASSWORD or SSH_PASSWORD", file=sys.stderr)
        return 1
    if not GRAFANA_URL:
        host = os.environ.get("HOMELAB_HOST", "")
        if not host:
            print("Set GRAFANA_URL or HOMELAB_HOST", file=sys.stderr)
            return 1
        GRAFANA_URL = f"http://{host}:3000"

    sys.path.insert(0, str(ROOT))
    from scripts.deploy_observability_homelab import load_dashboard_payload

    dash = load_dashboard_payload()
    ds_resp = requests.get(
        f"{GRAFANA_URL}/api/datasources",
        auth=(GRAFANA_USER, GRAFANA_PASSWORD),
        timeout=30,
    )
    ds_resp.raise_for_status()
    by_type = {d["type"]: d["uid"] for d in ds_resp.json()}

    now = int(time.time() * 1000)
    frm = now - 6 * 3600 * 1000
    failures = []

    for panel in dash.get("panels", []):
        if panel.get("type") == "row":
            continue
        ds = panel.get("datasource") or {}
        ds_type = ds.get("type", "")
        if "postgres" in ds_type:
            continue
        uid = ds.get("uid") or by_type.get(ds_type)
        if not uid:
            continue
        for target in panel.get("targets", []):
            expr = target.get("expr")
            if not expr:
                continue
            payload = {
                "queries": [
                    {
                        "refId": target.get("refId", "A"),
                        "datasource": {"type": ds_type, "uid": uid},
                        "expr": expr,
                        "queryType": "range" if ds_type == "loki" else "",
                        "maxLines": 10,
                    }
                ],
                "from": str(frm),
                "to": str(now),
            }
            r = requests.post(
                f"{GRAFANA_URL}/api/ds/query",
                json=payload,
                auth=(GRAFANA_USER, GRAFANA_PASSWORD),
                timeout=60,
            )
            title = panel.get("title", "?")
            pid = panel.get("id")
            if r.status_code != 200:
                failures.append((pid, title, r.text[:200]))
                print(f"[FAIL] {pid} {title} HTTP {r.status_code}")
                continue
            err = r.json().get("results", {}).get(target.get("refId", "A"), {}).get("error")
            if err:
                failures.append((pid, title, err))
                print(f"[FAIL] {pid} {title}: {err}")
            else:
                print(f"[OK] {pid} {title}")

    print(f"\n{len(failures)} ops panel failure(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
