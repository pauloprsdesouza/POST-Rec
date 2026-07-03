#!/usr/bin/env python3
"""Validate Celery worker metrics on a remote homelab host (SSH_PASSWORD env required)."""

from __future__ import annotations

import json
import os
import sys

import paramiko


def main() -> int:
    password = os.environ.get("SSH_PASSWORD")
    host = os.environ.get("SSH_HOST")
    user = os.environ.get("SSH_USER", "paulo")

    if not password:
        print("Error: set SSH_PASSWORD", file=sys.stderr)
        return 1
    if not host:
        print("Error: set SSH_HOST", file=sys.stderr)
        return 1

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, username=user, password=password, timeout=20)

    def run(cmd: str) -> tuple[str, str]:
        _, stdout, stderr = client.exec_command(cmd)
        return stdout.read().decode(), stderr.read().decode()

    print("=== Worker logs (metrics/otel) ===")
    print(run("docker logs postrec-worker 2>&1 | grep -E 'worker_metrics|otel|embedding' | tail -10")[0])

    print("\n=== Worker /metrics ===")
    print(
        run(
            "docker exec postrec-worker curl -sf http://127.0.0.1:9101/metrics 2>&1 "
            "| grep -E 'postrec_celery|^# HELP postrec' | head -20"
        )[0]
    )

    print("\n=== Prometheus celery series ===")
    out, _ = run('curl -s "http://127.0.0.1:9090/api/v1/query?query=postrec_celery_tasks_total"')
    print(json.dumps(json.loads(out), indent=2)[:1200])

    print("\n=== OTEL collector celery series ===")
    out, _ = run('curl -s "http://127.0.0.1:9090/api/v1/query?query=%7B__name__%3D~%22.*celery.*%22%7D"')
    results = json.loads(out).get("data", {}).get("result", [])
    print(f"found {len(results)} series")
    for result in results[:8]:
        print(result.get("metric"))

    print("\n=== Worker celery concurrency ===")
    print(run("docker exec postrec-worker ps aux | head -10")[0])

    client.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
