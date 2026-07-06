#!/usr/bin/env python3
"""Finish server-side setup: pip, schema, minio bucket. No app deployment."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import paramiko

from scripts.deploy_config import load_env_file

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def run(client, cmd, timeout=600):
    _, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode("utf-8", errors="replace")
    err = stderr.read().decode("utf-8", errors="replace")
    code = stdout.channel.recv_exit_status()
    return code, out, err


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default=os.environ.get("HOMELAB_HOST", os.environ.get("SSH_HOST")))
    parser.add_argument("--user", default=os.environ.get("HOMELAB_USER", os.environ.get("SSH_USER", "paulo")))
    parser.add_argument("--password", default=os.environ.get("SSH_PASSWORD"))
    parser.add_argument("--remote-dir", default=os.environ.get("HOMELAB_REMOTE_DIR", "/home/paulo/post-rec"))
    parser.add_argument("--env-file", default=str(PROJECT_ROOT / ".env"))
    args = parser.parse_args()

    if not args.host:
        print("Error: set --host, HOMELAB_HOST, or SSH_HOST", file=sys.stderr)
        return 1
    if not args.password:
        print("Error: set --password or SSH_PASSWORD", file=sys.stderr)
        return 1

    local_env = load_env_file(Path(args.env_file))
    minio_secret = (
        os.environ.get("MINIO_SECRET_KEY", local_env.get("MINIO_SECRET_KEY", local_env.get("RABBITMQ_PASSWORD", "")))
        .strip()
    )
    if not minio_secret:
        print("Error: set MINIO_SECRET_KEY or RABBITMQ_PASSWORD in .env", file=sys.stderr)
        return 1

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(args.host, username=args.user, password=args.password, timeout=15)

    rd = args.remote_dir
    minio_cmd = (
        "docker run --rm --network portainer-stack_backend --entrypoint /bin/sh "
        "minio/mc:RELEASE.2025-08-13T08-35-41Z -c "
        f"'mc alias set local http://minio:9000 minioadmin {minio_secret} && "
        "mc mb --ignore-existing local/postrec-artifacts && mc ls local/' 2>&1"
    )

    cmds = [
        ("minio bucket", minio_cmd),
        ("python venv", f"cd {rd} && python3 -m venv .venv && .venv/bin/pip install --upgrade pip setuptools wheel 2>&1"),
        ("install deps", f"cd {rd} && .venv/bin/pip install -e '.[dev]' 2>&1"),
        ("bootstrap schema", f"cd {rd} && .venv/bin/python scripts/bootstrap_homelab.py 2>&1"),
        ("verify tables", 'docker exec stack_postgres psql -U app -d epilogik -c "\\dt" 2>&1'),
    ]

    for name, cmd in cmds:
        print(f"\n=== {name} ===")
        code, out, err = run(client, cmd)
        text = (out + err).strip()
        if text:
            print(text[-5000:])
        print(f"exit: {code}")

    client.close()
    print("\nServer infrastructure setup complete (no app containers started).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
