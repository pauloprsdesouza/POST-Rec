"""Build and import POST-Rec Grafana dashboards (ops + homelab business panels)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import requests

ROOT = Path(__file__).resolve().parents[1]
OPS_DASHBOARD = ROOT / "deploy/observability/grafana/dashboards/postrec-operations.json"
BUSINESS_PANELS = ROOT / "deploy/homelab/grafana-business-panels.json"
MERGED_DASHBOARD = ROOT / "deploy/observability/grafana/dashboards/postrec-operations-business.json"

POSTGRES_DS_UID = "postrec-postgres"
HOMELAB_PROM_UID = "PBFA97CFB590B2093"
HOMELAB_LOKI_UID = "P8E80F9AEF21F6940"


def load_dashboard_payload(*, include_business: bool = True) -> dict[str, Any]:
    if not OPS_DASHBOARD.is_file():
        raise FileNotFoundError(f"missing dashboard at {OPS_DASHBOARD}")

    payload = json.loads(OPS_DASHBOARD.read_text(encoding="utf-8"))
    if not include_business or not BUSINESS_PANELS.is_file():
        return payload

    business_panels = json.loads(BUSINESS_PANELS.read_text(encoding="utf-8"))
    payload["panels"] = payload.get("panels", []) + business_panels
    payload["title"] = "POST-Rec Operations & Business"
    payload["time"] = {"from": "now-90d", "to": "now"}
    payload["refresh"] = "1m"
    payload["version"] = int(payload.get("version", 1)) + 1
    _normalize_logs_panel(payload)
    return payload


def _normalize_logs_panel(payload: dict[str, Any]) -> None:
    for panel in payload.get("panels", []):
        if panel.get("type") != "logs":
            continue
        for target in panel.get("targets", []):
            expr = str(target.get("expr", ""))
            if "container=~" in expr:
                target["expr"] = '{container=~".*(post-rec|postrec).*(api|worker).*"}'


def write_merged_dashboard(path: Path = MERGED_DASHBOARD) -> Path:
    payload = load_dashboard_payload(include_business=True)
    dashboard = prepare_dashboard_for_import(
        payload,
        prom_uid=HOMELAB_PROM_UID,
        loki_uid=HOMELAB_LOKI_UID,
        pg_uid=POSTGRES_DS_UID,
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dashboard, indent=2) + "\n", encoding="utf-8")
    return path


def fetch_datasource_uids(
    grafana_url: str,
    *,
    user: str,
    password: str,
) -> tuple[str, str, str]:
    resp = requests.get(
        f"{grafana_url.rstrip('/')}/api/datasources",
        auth=(user, password),
        timeout=30,
    )
    resp.raise_for_status()
    items = resp.json()
    prom_uid = next(d["uid"] for d in items if d.get("type") == "prometheus")
    loki_uid = next(d["uid"] for d in items if d.get("type") == "loki")
    pg_uid = next(
        (
            d["uid"]
            for d in items
            if d.get("type") == "grafana-postgresql-datasource"
            or d.get("name") == "POST-Rec PostgreSQL"
        ),
        POSTGRES_DS_UID,
    )
    return prom_uid, loki_uid, pg_uid


def prepare_dashboard_for_import(
    payload: dict[str, Any],
    *,
    prom_uid: str,
    loki_uid: str,
    pg_uid: str,
) -> dict[str, Any]:
    dash_str = json.dumps(payload)
    dash_str = (
        dash_str.replace("${DS_PROMETHEUS}", prom_uid)
        .replace("${DS_LOKI}", loki_uid)
        .replace(HOMELAB_PROM_UID, prom_uid)
        .replace(HOMELAB_LOKI_UID, loki_uid)
        .replace("POSTREC_POSTGRES", pg_uid)
    )
    dash = json.loads(dash_str)
    dash.pop("__inputs", None)
    dash.pop("__requires", None)
    dash.setdefault("uid", "postrec-ops-business")
    return dash


def import_dashboard(
    grafana_url: str,
    *,
    user: str,
    password: str,
    dashboard: dict[str, Any],
) -> dict[str, Any]:
    resp = requests.post(
        f"{grafana_url.rstrip('/')}/api/dashboards/db",
        json={"dashboard": dashboard, "overwrite": True, "message": "sync homelab dashboard"},
        auth=(user, password),
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()


def import_homelab_dashboard(
    grafana_url: str,
    *,
    user: str = "admin",
    password: str,
    include_business: bool = True,
) -> dict[str, Any]:
    payload = load_dashboard_payload(include_business=include_business)
    prom_uid, loki_uid, pg_uid = fetch_datasource_uids(grafana_url, user=user, password=password)
    dashboard = prepare_dashboard_for_import(payload, prom_uid=prom_uid, loki_uid=loki_uid, pg_uid=pg_uid)
    return import_dashboard(grafana_url, user=user, password=password, dashboard=dashboard)
