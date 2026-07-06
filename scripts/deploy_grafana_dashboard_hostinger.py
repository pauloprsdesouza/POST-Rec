#!/usr/bin/env python3
"""Deploy homelab Grafana dashboard (ops + business) to Hostinger."""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

import paramiko

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.deploy_config import require_deploy_domain
from scripts.grafana_dashboard import write_merged_dashboard

PASSWORD = os.environ.get("HOSTINGER_SSH_PASSWORD", "")
HOST = os.environ.get("HOSTINGER_HOST", "")
REMOTE = "/opt/post-rec"
GRAFANA_PASSWORD = os.environ.get("GRAFANA_ADMIN_PASSWORD", os.environ.get("GRAFANA_PASSWORD", ""))
GRAFANA_USER = os.environ.get("GRAFANA_USER", "admin")


def run(client, cmd, timeout=600):
    _, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    out = (stdout.read() + stderr.read()).decode("utf-8", errors="replace")
    return stdout.channel.recv_exit_status(), out


def main() -> int:
    if not PASSWORD:
        print("Set HOSTINGER_SSH_PASSWORD", file=sys.stderr)
        return 1
    if not HOST:
        print("Set HOSTINGER_HOST", file=sys.stderr)
        return 1
    if not GRAFANA_PASSWORD:
        print("Set GRAFANA_ADMIN_PASSWORD", file=sys.stderr)
        return 1

    try:
        domain = require_deploy_domain()
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    merged = write_merged_dashboard()
    print(f"Built {merged}")

    upload_files = [
        merged,
        ROOT / "deploy/homelab/grafana-business-panels.json",
        ROOT / "deploy/observability/prometheus.yml",
        ROOT / "deploy/observability/promtail-config.yaml",
        ROOT / "docker-compose.prod.yml",
    ]

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username="root", password=PASSWORD, timeout=30, look_for_keys=False, allow_agent=False)
    sftp = client.open_sftp()

    remote_dashboard = f"{REMOTE}/deploy/observability/grafana/dashboards/postrec-operations-business.json"
    sftp.put(str(merged), remote_dashboard)

    try:
        sftp.remove(f"{REMOTE}/deploy/observability/grafana/dashboards/postrec-operations.json")
    except OSError:
        pass

    for local in upload_files[1:]:
        rel = local.relative_to(ROOT).as_posix()
        sftp.put(str(local), f"{REMOTE}/{rel}")
    sftp.close()

    code, out = run(
        client,
        f"cd {REMOTE} && docker compose -f docker-compose.yml -f docker-compose.prod.yml "
        "up -d prometheus promtail && docker compose -f docker-compose.yml -f docker-compose.prod.yml restart grafana",
        timeout=300,
    )
    print(out[-4000:])
    if code != 0:
        client.close()
        return code

    run(client, "docker exec postrec-prometheus wget -qO- --post-data='' http://127.0.0.1:9090/-/reload 2>/dev/null || true")

    time.sleep(8)
    auth = f"{GRAFANA_USER}:{GRAFANA_PASSWORD}"
    _, verify = run(
        client,
        f"curl -s -u {auth!r} https://{domain}/grafana/api/search?query=POST-Rec",
        timeout=30,
    )
    print("Dashboards:", verify[:1000])
    client.close()
    print(f"\nOpen: https://{domain}/grafana/d/postrec-ops-business/post-rec-operations-and-business")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
