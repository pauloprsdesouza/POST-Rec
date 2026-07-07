#!/usr/bin/env python3
"""Deploy Grafana observability stack and update Traefik routing on the VPS."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

import paramiko

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.deploy_config import require_deploy_domain


def run(client: paramiko.SSHClient, cmd: str, timeout: int = 900) -> tuple[int, str, str]:
    _, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode("utf-8", errors="replace")
    err = stderr.read().decode("utf-8", errors="replace")
    return stdout.channel.recv_exit_status(), out, err


def main() -> int:
    parser = argparse.ArgumentParser(description="Deploy Grafana on VPS")
    parser.add_argument("--host", default=os.environ.get("HOSTINGER_HOST"))
    parser.add_argument("--user", default="root")
    parser.add_argument("--password", default=os.environ.get("HOSTINGER_SSH_PASSWORD"))
    parser.add_argument("--remote-dir", default="/opt/post-rec")
    parser.add_argument("--grafana-password", default=os.environ.get("GRAFANA_ADMIN_PASSWORD", os.environ.get("GRAFANA_PASSWORD")))
    args = parser.parse_args()

    if not args.password:
        print("Error: set --password or HOSTINGER_SSH_PASSWORD", file=sys.stderr)
        return 1
    if not args.host:
        print("Error: set --host or HOSTINGER_HOST", file=sys.stderr)
        return 1
    if not args.grafana_password:
        print("Error: set --grafana-password or GRAFANA_ADMIN_PASSWORD", file=sys.stderr)
        return 1

    try:
        domain = require_deploy_domain()
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    subprocess.run(
        [sys.executable, str(PROJECT_ROOT / "scripts" / "generate_traefik_apps.py"), "--write"],
        check=True,
        cwd=PROJECT_ROOT,
    )

    upload_paths = [
        "deploy/apps/registry.json",
        "deploy/traefik/traefik.yml",
        "deploy/traefik/apps.yaml",
        "docker-compose.prod.yml",
        "docker-compose.yml",
        "deploy/landing/index.html",
        "deploy/grafana/nginx.conf",
        "deploy/grafana/Dockerfile",
        "deploy/observability/prometheus.yml",
        "deploy/observability/promtail-config.yaml",
        "deploy/observability/grafana/provisioning/datasources/datasources.yaml",
        "deploy/observability/grafana/provisioning/dashboards/dashboards.yaml",
        "deploy/observability/grafana/dashboards/postrec-operations.json",
        "deploy/homelab/grafana-business-panels.json",
        "scripts/grafana_dashboard.py",
        "scripts/import_grafana_dashboard.py",
        "scripts/deploy_config.py",
    ]

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(
        args.host,
        username=args.user,
        password=args.password,
        timeout=30,
        look_for_keys=False,
        allow_agent=False,
    )

    sftp = client.open_sftp()
    for rel in upload_paths:
        local = PROJECT_ROOT / rel
        remote = f"{args.remote_dir}/{rel}"
        run(client, f"mkdir -p $(dirname {remote})")
        sftp.put(str(local), remote)
    sftp.close()
    print("Uploaded Grafana stack files and Traefik config.")

    compose_cmd = (
        f"cd {args.remote_dir} && "
        "docker compose -f docker-compose.yml -f docker-compose.prod.yml "
        "up -d --build grafana grafana-proxy prometheus loki promtail landing traefik"
    )
    code, out, err = run(client, compose_cmd, timeout=600)
    print((out + err)[-5000:])
    if code != 0:
        client.close()
        return code

    run(
        client,
        f"cd {args.remote_dir} && docker compose -f docker-compose.yml -f docker-compose.prod.yml restart traefik",
    )

    grafana_url = f"https://{domain}/grafana"
    grafana_user = os.environ.get("GRAFANA_USER", "admin")
    print("Importing homelab dashboard (ops + business panels)...")
    import_cmd = (
        f"cd {args.remote_dir} && docker compose -f docker-compose.yml -f docker-compose.prod.yml "
        f"exec -T -e GRAFANA_URL={grafana_url} -e GRAFANA_PASSWORD={args.grafana_password} api "
        "python scripts/import_grafana_dashboard.py --write-file"
    )
    code, out, err = run(client, import_cmd, timeout=120)
    print((out + err)[-3000:])
    if code != 0:
        from scripts.grafana_dashboard import import_homelab_dashboard, write_merged_dashboard

        write_merged_dashboard()
        result = import_homelab_dashboard(grafana_url, user=grafana_user, password=args.grafana_password)
        print(f"Imported via local API call: {grafana_url}{result.get('url', '')}")

    run(client, "docker exec postrec-prometheus wget -qO- --post-data='' http://127.0.0.1:9090/-/reload 2>/dev/null || true")

    print("Waiting for Grafana...")
    healthy = False
    auth = f"{grafana_user}:{args.grafana_password}"
    for _ in range(18):
        code, out, _ = run(
            client,
            f"curl -s -o /dev/null -w '%{{http_code}}' -u {auth!r} https://{domain}/grafana/api/health",
            timeout=30,
        )
        if out.strip() == "200":
            healthy = True
            break
        time.sleep(5)

    verify_cmds = [
        "docker ps --filter name=postrec-grafana --format '{{.Names}} {{.Status}}'",
        f"curl -sI https://{domain}/grafana/ | head -8",
        f"curl -s -u {auth!r} https://{domain}/grafana/api/org",
    ]
    for cmd in verify_cmds:
        print("===", cmd)
        _, stdout, stderr = client.exec_command(cmd, timeout=60)
        print((stdout.read() + stderr.read()).decode("utf-8", errors="replace")[:800])

    client.close()

    print("\n" + "=" * 60)
    print("GRAFANA DEPLOYED")
    print("=" * 60)
    print(f"URL:      https://{domain}/grafana/")
    print(f"Username: {grafana_user}")
    print("Password: (GRAFANA_ADMIN_PASSWORD env)")
    if not healthy:
        print("\nWARNING: Grafana health check did not return 200 yet — it may still be starting.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
