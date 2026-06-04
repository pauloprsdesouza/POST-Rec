#!/usr/bin/env python3
"""Remote server setup for POST-Rec infrastructure (no app deployment)."""

import argparse
import os
import sys
from pathlib import Path

import paramiko


def run(client: paramiko.SSHClient, cmd: str, timeout: int = 120) -> tuple[int, str, str]:
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode("utf-8", errors="replace")
    err = stderr.read().decode("utf-8", errors="replace")
    code = stdout.channel.recv_exit_status()
    return code, out, err


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="192.168.10.13")
    parser.add_argument("--user", default="paulo")
    parser.add_argument("--password", required=True)
    parser.add_argument("--remote-dir", default="/home/paulo/post-rec")
    args = parser.parse_args()

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    print(f"Connecting to {args.user}@{args.host}...")
    client.connect(args.host, username=args.user, password=args.password, timeout=15)

    steps = [
        ("hostname", "hostname && whoami"),
        ("docker services", 'docker ps --format "{{.Names}}: {{.Status}}" | grep -E "stack_|postgres|redis|rabbit|minio" || docker ps --format "{{.Names}}: {{.Status}}"'),
        (
            "postgres pgvector",
            'docker exec stack_postgres psql -U app -d epilogik -c "CREATE EXTENSION IF NOT EXISTS vector;" '
            '-c "SELECT extname, extversion FROM pg_extension WHERE extname = \'vector\';" 2>&1 || '
            'docker exec stack_postgres psql -U app -d automation -c "SELECT 1;" 2>&1',
        ),
        (
            "list databases",
            'docker exec stack_postgres psql -U app -d postgres -c "\\l" 2>&1',
        ),
        (
            "create epilogik if missing",
            'docker exec stack_postgres psql -U app -d postgres -tc "SELECT 1 FROM pg_database WHERE datname=\'epilogik\'" | grep -q 1 || '
            'docker exec stack_postgres psql -U app -d postgres -c "CREATE DATABASE epilogik;" 2>&1',
        ),
        (
            "pgvector on epilogik",
            'docker exec stack_postgres psql -U app -d epilogik -c "CREATE EXTENSION IF NOT EXISTS vector;" '
            '-c "SELECT extname, extversion FROM pg_extension WHERE extname = \'vector\';" 2>&1',
        ),
        (
            "redis ping",
            'docker exec stack_redis redis-cli -a "CmC3Hzi9Klu34V" ping 2>&1',
        ),
        (
            "rabbitmq status",
            'docker exec stack_rabbitmq rabbitmq-diagnostics ping 2>&1',
        ),
        (
            "minio bucket",
            'docker run --rm --network portainer-stack_backend minio/mc:RELEASE.2025-08-13T08-35-41Z '
            'sh -c \'mc alias set local http://minio:9000 minioadmin CmC3Hzi9Klu34V && mc mb --ignore-existing local/postrec-artifacts && mc ls local/\' 2>&1 || '
            'docker run --rm minio/mc:RELEASE.2025-08-13T08-35-41Z '
            'sh -c \'mc alias set local http://192.168.10.13:9000 minioadmin CmC3Hzi9Klu34V && mc mb --ignore-existing local/postrec-artifacts && mc ls local/\' 2>&1',
        ),
    ]

    for name, cmd in steps:
        print(f"\n=== {name} ===")
        code, out, err = run(client, cmd)
        if out.strip():
            print(out.strip())
        if err.strip():
            print(err.strip())
        if code != 0 and name not in ("minio bucket",):
            print(f"WARNING: exit code {code}")

    # Upload project and run bootstrap (schema only, no deploy)
    print(f"\n=== preparing remote dir {args.remote_dir} ===")
    run(client, f"mkdir -p {args.remote_dir}")

    sftp = client.open_sftp()

    def upload_tree(local_base: str, remote_base: str, paths: list[str]) -> None:
        local_root = Path(local_base)
        for rel in paths:
            src = local_root / rel
            if src.is_file():
                remote_path = f"{remote_base}/{rel}".replace("\\", "/")
                remote_parent = "/".join(remote_path.split("/")[:-1])
                run(client, f"mkdir -p {remote_parent}")
                sftp.put(str(src), remote_path)
            elif src.is_dir():
                for root, _, files in os.walk(src):
                    for f in files:
                        if f.endswith((".pyc",)) or "__pycache__" in root:
                            continue
                        lp = Path(root) / f
                        rp = f"{remote_base}/{lp.relative_to(local_root)}".replace("\\", "/")
                        remote_parent = "/".join(rp.split("/")[:-1])
                        run(client, f"mkdir -p {remote_parent}")
                        sftp.put(str(lp), rp)

    project_root = Path(__file__).resolve().parents[1]
    upload_paths = [
        "pyproject.toml",
        "README.md",
        "alembic.ini",
        "apps",
        "packages",
        "migrations",
        "scripts/bootstrap_homelab.py",
        "scripts/remote_setup.py",
        ".env.example",
    ]

    print("Uploading project files...")
    upload_tree(str(project_root), args.remote_dir, upload_paths)

    # Write .env on server for bootstrap (infrastructure verification only)
    env_content = """APP_ENV=development
APP_NAME=post-rec
DATABASE_URL=postgresql+psycopg://app:CmC3Hzi9Klu34V@192.168.10.13:5432/epilogik
RABBITMQ_HOST=192.168.10.13
RABBITMQ_PORT=5672
RABBITMQ_USER=admin
RABBITMQ_PASSWORD=CmC3Hzi9Klu34V
CELERY_BROKER_URL=pyamqp://admin:CmC3Hzi9Klu34V@192.168.10.13:5672//
REDIS_URL=redis://:CmC3Hzi9Klu34V@192.168.10.13:6379/0
CELERY_RESULT_BACKEND=redis://:CmC3Hzi9Klu34V@192.168.10.13:6379/1
MINIO_ENDPOINT=192.168.10.13:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=CmC3Hzi9Klu34V
MINIO_USE_SSL=false
MINIO_BUCKET=postrec-artifacts
GEMINI_API_KEY=AIzaSyA_l0JhSvA6UEqjiNp5yZElDRSTLKzNUCk
GEMINI_GENERATION_MODEL=gemini-2.5-flash-lite
GEMINI_EMBEDDING_MODEL=gemini-embedding-001
GEMINI_EMBEDDING_DIMENSIONS=768
LOG_LEVEL=INFO
LOG_FORMAT=console
AUTH_ENABLED=false
API_BASE_URL=http://localhost:8000
"""
    with sftp.open(f"{args.remote_dir}/.env", "w") as f:
        f.write(env_content)

    sftp.close()

    bootstrap_cmds = [
        f"cd {args.remote_dir} && python3 --version 2>&1 || python --version 2>&1",
        f"cd {args.remote_dir} && (python3 -m pip install -e '.[dev]' 2>&1 || python -m pip install -e '.[dev]' 2>&1)",
        f"cd {args.remote_dir} && (python3 scripts/bootstrap_homelab.py 2>&1 || python scripts/bootstrap_homelab.py 2>&1)",
    ]

    for cmd in bootstrap_cmds:
        print(f"\n=== running: {cmd[:80]}... ===")
        code, out, err = run(client, cmd, timeout=600)
        if out.strip():
            print(out.strip()[-4000:])
        if err.strip():
            print(err.strip()[-2000:])
        if code != 0:
            print(f"Exit code: {code}")

    # Verify tables created
    print("\n=== verify post-rec tables ===")
    code, out, err = run(
        client,
        'docker exec stack_postgres psql -U app -d epilogik -c "\\dt" 2>&1',
    )
    print(out.strip() or err.strip())

    client.close()
    print("\nDone. Infrastructure ready on server. App NOT deployed — test locally.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
