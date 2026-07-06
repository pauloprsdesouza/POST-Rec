#!/usr/bin/env python3
"""Deploy POST-Rec to homelab, wire Prometheus, and import Grafana dashboard."""

from __future__ import annotations

import io
import json
import os
import sys
import tarfile
import time
from pathlib import Path

import paramiko
import requests

ROOT = Path(__file__).resolve().parents[1]
REMOTE_DIR = os.environ.get("HOMELAB_REMOTE_DIR", "/home/paulo/post-rec")
HOST = os.environ.get("HOMELAB_HOST", "")
USER = os.environ.get("HOMELAB_USER", "paulo")
PASSWORD = os.environ.get("SSH_PASSWORD", "")
GRAFANA_URL = os.environ.get("GRAFANA_URL", "")
GRAFANA_USER = os.environ.get("GRAFANA_USER", "admin")
GRAFANA_PASSWORD = os.environ.get("GRAFANA_PASSWORD", PASSWORD)
POSTGRES_DS_UID = "postrec-postgres"
POSTGRES_DOCKER_HOST = os.environ.get("POSTGRES_GRAFANA_HOST", "stack_postgres")

EXCLUDES = {
    ".git",
    "apps/web/node_modules",
    "apps/web/dist",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    ".mypy_cache",
}


def ssh_client() -> paramiko.SSHClient:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD, timeout=30)
    return client


def run(client: paramiko.SSHClient, cmd: str) -> tuple[int, str, str]:
    _, stdout, stderr = client.exec_command(cmd)
    out = stdout.read().decode("utf-8", errors="replace")
    err = stderr.read().decode("utf-8", errors="replace")
    code = stdout.channel.recv_exit_status()
    return code, out, err


def upload_project(client: paramiko.SSHClient) -> None:
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        for path in ROOT.iterdir():
            if path.name in EXCLUDES:
                continue
            tar.add(path, arcname=path.name, filter=_tar_filter)
    buf.seek(0)
    sftp = client.open_sftp()
    remote_tar = f"{REMOTE_DIR}/.deploy/post-rec-sync.tar.gz"
    run(client, f"mkdir -p {REMOTE_DIR}/.deploy")
    with sftp.file(remote_tar, "wb") as remote:
        remote.write(buf.read())
    sftp.close()
    code, out, err = run(
        client,
        f"mkdir -p {REMOTE_DIR} && tar -xzf {remote_tar} -C {REMOTE_DIR} && rm -f {remote_tar}",
    )
    if code != 0:
        raise RuntimeError(f"extract failed: {err or out}")


def _tar_filter(tarinfo: tarfile.TarInfo) -> tarfile.TarInfo | None:
    parts = Path(tarinfo.name).parts
    if any(part in EXCLUDES for part in parts):
        return None
    if parts and parts[0] == "apps" and len(parts) > 2 and parts[2] == "node_modules":
        return None
    return tarinfo


def patch_env(client: paramiko.SSHClient) -> None:
    env_path = f"{REMOTE_DIR}/.env"
    code, content, _ = run(client, f"cat {env_path} 2>/dev/null || true")
    if not content:
        raise RuntimeError(f"missing {env_path}")

    lines = content.splitlines()
    updates = {
        "OTEL_ENABLED": "true",
        "OTEL_EXPORTER_OTLP_ENDPOINT": "http://epilogik-otel-collector:4317",
        "OTEL_SERVICE_NAME": "postrec-api",
        "LOG_FORMAT": "json",
    }
    seen: set[str] = set()
    patched: list[str] = []
    for line in lines:
        key = line.split("=", 1)[0] if "=" in line else ""
        if key in updates:
            patched.append(f"{key}={updates[key]}")
            seen.add(key)
        elif key == "OTEL_SERVICE_NAME":
            continue
        else:
            patched.append(line)
    for key, value in updates.items():
        if key not in seen:
            patched.append(f"{key}={value}")
    body = "\n".join(patched).rstrip() + "\n"
    run(client, f"cat > {env_path} << 'ENVEOF'\n{body}ENVEOF")


def deploy_stack(client: paramiko.SSHClient) -> None:
    cmd = (
        f"cd {REMOTE_DIR} && docker compose -f deploy/homelab/docker-compose.app.yml "
        f"up -d --build migrate api worker"
    )
    code, out, err = run(client, cmd)
    sys.stdout.buffer.write(out.encode("utf-8", errors="replace"))
    if err:
        sys.stderr.buffer.write(err.encode("utf-8", errors="replace"))
    if code != 0:
        raise RuntimeError("docker compose up failed")


def patch_prometheus(client: paramiko.SSHClient) -> None:
    jobs = """
  - job_name: postrec-api
    scrape_interval: 15s
    metrics_path: /metrics
    static_configs:
      - targets: ['postrec-api:8000']
        labels:
          service_name: postrec-api

  - job_name: postrec-worker
    scrape_interval: 15s
    metrics_path: /metrics
    static_configs:
      - targets: ['postrec-worker:9101']
        labels:
          service_name: postrec-worker
"""
    code, current, _ = run(client, "docker exec prometheus cat /etc/prometheus/prometheus.yml")
    if code != 0:
        raise RuntimeError("could not read prometheus config")

    import re

    cleaned = re.sub(
        r"\n  - job_name: postrec-api.*?service_name: postrec-api\n",
        "\n",
        current,
        flags=re.DOTALL,
    )
    cleaned = re.sub(
        r"\n  - job_name: postrec-worker.*?service_name: postrec-worker\n",
        "\n",
        cleaned,
        flags=re.DOTALL,
    )
    updated = cleaned.rstrip() + jobs
    run(client, f"cat > /tmp/prometheus.yml << 'PROMEOF'\n{updated}\nPROMEOF")
    code, _, err = run(client, "docker cp /tmp/prometheus.yml prometheus:/etc/prometheus/prometheus.yml")
    if code != 0:
        raise RuntimeError(f"docker cp prometheus config failed: {err}")
    run(client, "docker exec prometheus wget -qO- --post-data='' http://127.0.0.1:9090/-/reload")
    print("Prometheus reloaded with postrec-api + postrec-worker scrape jobs")


def _parse_database_url_line(line: str) -> dict[str, str]:
    from urllib.parse import urlparse

    raw = line.split("=", 1)[1].strip().strip('"').strip("'")
    raw = raw.replace("postgresql+psycopg://", "postgresql://")
    parsed = urlparse(raw)
    if not parsed.username or not parsed.path:
        raise ValueError("invalid DATABASE_URL")
    return {
        "user": parsed.username,
        "password": parsed.password or "",
        "database": parsed.path.lstrip("/"),
    }


def _load_database_creds(client: paramiko.SSHClient | None) -> dict[str, str]:
    if client is not None:
        _, content, _ = run(client, f"grep '^DATABASE_URL=' {REMOTE_DIR}/.env | head -1")
        if content.strip():
            return _parse_database_url_line(content.strip())

    for env_path in (ROOT / ".env", ROOT / ".env.remote"):
        if env_path.exists():
            for line in env_path.read_text(encoding="utf-8").splitlines():
                if line.startswith("DATABASE_URL="):
                    creds = _parse_database_url_line(line)
                    return creds
    raise RuntimeError("DATABASE_URL not found for Grafana PostgreSQL datasource")


def ensure_postgres_datasource(creds: dict[str, str]) -> str:
    payload = {
        "name": "POST-Rec PostgreSQL",
        "type": "grafana-postgresql-datasource",
        "uid": POSTGRES_DS_UID,
        "url": f"{POSTGRES_DOCKER_HOST}:5432",
        "user": creds["user"],
        "database": creds["database"],
        "access": "proxy",
        "isDefault": False,
        "jsonData": {
            "sslmode": "disable",
            "postgresVersion": 1600,
        },
        "secureJsonData": {
            "password": creds["password"],
        },
    }
    ds_resp = requests.get(
        f"{GRAFANA_URL}/api/datasources",
        auth=(GRAFANA_USER, GRAFANA_PASSWORD),
        timeout=30,
    )
    ds_resp.raise_for_status()
    existing = next(
        (
            d
            for d in ds_resp.json()
            if d.get("uid") == POSTGRES_DS_UID or d.get("name") == "POST-Rec PostgreSQL"
        ),
        None,
    )
    if existing:
        resp = requests.put(
            f"{GRAFANA_URL}/api/datasources/{existing['id']}",
            json=payload,
            auth=(GRAFANA_USER, GRAFANA_PASSWORD),
            timeout=30,
        )
    else:
        resp = requests.post(
            f"{GRAFANA_URL}/api/datasources",
            json=payload,
            auth=(GRAFANA_USER, GRAFANA_PASSWORD),
            timeout=30,
        )
    resp.raise_for_status()
    print(f"Grafana PostgreSQL datasource: {POSTGRES_DS_UID} -> {POSTGRES_DOCKER_HOST}")
    return POSTGRES_DS_UID


def load_dashboard_payload() -> dict:
    sys.path.insert(0, str(ROOT))
    from scripts.grafana_dashboard import load_dashboard_payload as load_payload

    return load_payload(include_business=True)


def import_grafana_dashboard(client: paramiko.SSHClient | None = None) -> None:
    creds = _load_database_creds(client)
    ensure_postgres_datasource(creds)
    sys.path.insert(0, str(ROOT))
    from scripts.grafana_dashboard import import_homelab_dashboard

    result = import_homelab_dashboard(
        GRAFANA_URL,
        user=GRAFANA_USER,
        password=GRAFANA_PASSWORD,
        include_business=True,
    )
    print(f"Grafana dashboard: {GRAFANA_URL}{result.get('url', '')}")


def validate(client: paramiko.SSHClient) -> None:
    for _ in range(12):
        code, out, _ = run(client, "curl -sf http://127.0.0.1:8010/api/v1/health")
        if code == 0 and "ok" in out:
            print("Health:", out.strip())
            break
        time.sleep(5)
    else:
        raise RuntimeError("POST-Rec API health check failed")

    code, out, _ = run(client, "curl -sf http://127.0.0.1:8010/metrics | grep postrec_http_requests_total | head -3")
    print("Metrics sample:\n", out or "(no metrics yet — generate traffic)")

    code, out, _ = run(
        client,
        "curl -sf 'http://127.0.0.1:9090/api/v1/query?query=up{job=\"postrec-api\"}'",
    )
    print("Prometheus target:", out[:300] if out else "pending scrape")


def main() -> int:
    global GRAFANA_URL

    if not PASSWORD:
        print("Set SSH_PASSWORD env var", file=sys.stderr)
        return 1
    if not HOST:
        print("Set HOMELAB_HOST env var", file=sys.stderr)
        return 1
    if not GRAFANA_URL:
        GRAFANA_URL = f"http://{HOST}:3000"

    print(f"Deploying POST-Rec to {HOST}...")
    client = ssh_client()
    try:
        upload_project(client)
        patch_env(client)
        deploy_stack(client)
        patch_prometheus(client)
        validate(client)
    finally:
        client.close()
    import_grafana_dashboard(client)
    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
