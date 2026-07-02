#!/usr/bin/env python3
"""Upload POST-Rec shared-infra changes and apply on VPS."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import paramiko

PROJECT_ROOT = Path(__file__).resolve().parents[1]
REMOTE_DIR = "/opt/post-rec"


def run(client: paramiko.SSHClient, cmd: str, timeout: int = 1800) -> tuple[int, str, str]:
    _, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode("utf-8", errors="replace")
    err = stderr.read().decode("utf-8", errors="replace")
    return stdout.channel.recv_exit_status(), out, err


def upload_tree(client, sftp, local_root: Path, remote_root: str) -> None:
    skip = {".git", ".venv", "node_modules", "__pycache__"}
    for root, dirs, files in os.walk(local_root):
        dirs[:] = [d for d in dirs if d not in skip]
        rel = Path(root).relative_to(local_root)
        remote_dir = f"{remote_root}/{rel.as_posix()}".rstrip("/")
        if str(rel) != ".":
            run(client, f"mkdir -p {remote_dir}")
        for name in files:
            if name.endswith((".pyc", ".pyo")) or name == ".env":
                continue
            sftp.put(str(Path(root) / name), f"{remote_dir}/{name}")


def main() -> int:
    password = os.environ.get("HOSTINGER_SSH_PASSWORD", "LMYTYvPWQJaQbcd2AMkLuAj-QFbQkh3WzrAhTTcv2ruBPNvwLx")
    host = os.environ.get("HOSTINGER_HOST", "187.127.39.214")

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, username="root", password=password, timeout=30, look_for_keys=False, allow_agent=False)

    run(client, f"mkdir -p {REMOTE_DIR}")
    sftp = client.open_sftp()
    upload_tree(client, sftp, PROJECT_ROOT, REMOTE_DIR)
    sftp.close()
    print("Upload complete")

    steps = [
        (
            "shared-db-init + compose up",
            f"cd {REMOTE_DIR} && "
            "docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d shared-db-init && "
            "docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build --remove-orphans",
        ),
        (
            "migrate coolify to shared db",
            f"python3 {REMOTE_DIR}/scripts/migrate_coolify_shared_db.py",
        ),
        (
            "verify",
            f"cd {REMOTE_DIR} && docker compose ps && "
            "curl -sf http://127.0.0.1:8000/api/health && echo ' coolify-ok'",
        ),
    ]

    for name, cmd in steps:
        print(f"\n=== {name} ===")
        code, out, err = run(client, cmd)
        text = (out + err).strip()
        if text:
            print(text[-8000:])
        print(f"exit: {code}")
        if code != 0:
            client.close()
            return 1

    client.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
