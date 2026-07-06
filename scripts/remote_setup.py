#!/usr/bin/env python3
"""Remote server setup for POST-Rec infrastructure (no app deployment)."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import paramiko

from scripts.deploy_config import load_env_file

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def run(client: paramiko.SSHClient, cmd: str, timeout: int = 120) -> tuple[int, str, str]:
    _, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode("utf-8", errors="replace")
    err = stderr.read().decode("utf-8", errors="replace")
    code = stdout.channel.recv_exit_status()
    return code, out, err


def _env_value(local_env: dict[str, str], key: str, default: str = "") -> str:
    return os.environ.get(key, local_env.get(key, default)).strip()


def build_remote_env(local_env: dict[str, str], host: str) -> str:
    rabbitmq_password = _env_value(local_env, "RABBITMQ_PASSWORD")
    rabbitmq_user = _env_value(local_env, "RABBITMQ_USER", "admin")
    rabbitmq_port = _env_value(local_env, "RABBITMQ_PORT", "5672")
    database_url = _env_value(local_env, "DATABASE_URL")
    if not database_url:
        db_user = _env_value(local_env, "POSTGRES_USER", "app")
        db_name = _env_value(local_env, "POSTGRES_DB", "postrec")
        db_password = _env_value(local_env, "POSTGRES_PASSWORD", rabbitmq_password)
        database_url = f"postgresql+psycopg://{db_user}:{db_password}@{host}:5432/{db_name}"

    minio_endpoint = _env_value(local_env, "MINIO_ENDPOINT", f"{host}:9000")
    minio_access_key = _env_value(local_env, "MINIO_ACCESS_KEY", "minioadmin")
    minio_secret_key = _env_value(local_env, "MINIO_SECRET_KEY", rabbitmq_password)

    lines = [
        f"APP_ENV={_env_value(local_env, 'APP_ENV', 'development')}",
        f"APP_NAME={_env_value(local_env, 'APP_NAME', 'post-rec')}",
        f"DATABASE_URL={database_url}",
        f"RABBITMQ_HOST={host}",
        f"RABBITMQ_PORT={rabbitmq_port}",
        f"RABBITMQ_USER={rabbitmq_user}",
        f"RABBITMQ_PASSWORD={rabbitmq_password}",
    ]
    if rabbitmq_password:
        lines.extend(
            [
                f"CELERY_BROKER_URL=pyamqp://{rabbitmq_user}:{rabbitmq_password}@{host}:{rabbitmq_port}//",
                f"REDIS_URL=redis://:{rabbitmq_password}@{host}:6379/0",
                f"CELERY_RESULT_BACKEND=redis://:{rabbitmq_password}@{host}:6379/1",
            ]
        )
    lines.extend(
        [
            f"MINIO_ENDPOINT={minio_endpoint}",
            f"MINIO_ACCESS_KEY={minio_access_key}",
            f"MINIO_SECRET_KEY={minio_secret_key}",
            "MINIO_USE_SSL=false",
            f"MINIO_BUCKET={_env_value(local_env, 'MINIO_BUCKET', 'postrec-artifacts')}",
            f"GEMINI_API_KEY={_env_value(local_env, 'GEMINI_API_KEY')}",
            f"GEMINI_GENERATION_MODEL={_env_value(local_env, 'GEMINI_GENERATION_MODEL', 'gemini-2.5-flash')}",
            f"GEMINI_EMBEDDING_MODEL={_env_value(local_env, 'GEMINI_EMBEDDING_MODEL', 'gemini-embedding-001')}",
            f"GEMINI_EMBEDDING_DIMENSIONS={_env_value(local_env, 'GEMINI_EMBEDDING_DIMENSIONS', '768')}",
            f"LOG_LEVEL={_env_value(local_env, 'LOG_LEVEL', 'INFO')}",
            f"LOG_FORMAT={_env_value(local_env, 'LOG_FORMAT', 'console')}",
            f"AUTH_ENABLED={_env_value(local_env, 'AUTH_ENABLED', 'false')}",
            f"API_BASE_URL={_env_value(local_env, 'API_BASE_URL', 'http://localhost:8000')}",
        ]
    )
    return "\n".join(lines) + "\n"


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
    rabbitmq_password = _env_value(local_env, "RABBITMQ_PASSWORD")
    minio_secret = _env_value(local_env, "MINIO_SECRET_KEY", rabbitmq_password)

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    print(f"Connecting to {args.user}@{args.host}...")
    client.connect(args.host, username=args.user, password=args.password, timeout=15)

    redis_ping = (
        f'docker exec stack_redis redis-cli -a "{rabbitmq_password}" ping 2>&1'
        if rabbitmq_password
        else "docker exec stack_redis redis-cli ping 2>&1"
    )
    minio_cmd = (
        "docker run --rm --network portainer-stack_backend --entrypoint /bin/sh "
        "minio/mc:RELEASE.2025-08-13T08-35-41Z -c "
        f"'mc alias set local http://minio:9000 minioadmin {minio_secret} && "
        "mc mb --ignore-existing local/postrec-artifacts && mc ls local/' 2>&1"
        if minio_secret
        else "echo 'skip minio bucket (MINIO_SECRET_KEY not set)'"
    )

    steps = [
        ("hostname", "hostname && whoami"),
        (
            "docker services",
            'docker ps --format "{{.Names}}: {{.Status}}" | grep -E "stack_|postgres|redis|rabbit|minio" || docker ps --format "{{.Names}}: {{.Status}}"',
        ),
        (
            "postgres pgvector",
            'docker exec stack_postgres psql -U app -d epilogik -c "CREATE EXTENSION IF NOT EXISTS vector;" '
            '-c "SELECT extname, extversion FROM pg_extension WHERE extname = \'vector\';" 2>&1 || '
            'docker exec stack_postgres psql -U app -d automation -c "SELECT 1;" 2>&1',
        ),
        ("list databases", 'docker exec stack_postgres psql -U app -d postgres -c "\\l" 2>&1'),
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
        ("redis ping", redis_ping),
        ("rabbitmq status", "docker exec stack_rabbitmq rabbitmq-diagnostics ping 2>&1"),
        ("minio bucket", minio_cmd),
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
                    for file_name in files:
                        if file_name.endswith((".pyc",)) or "__pycache__" in root:
                            continue
                        lp = Path(root) / file_name
                        rp = f"{remote_base}/{lp.relative_to(local_root)}".replace("\\", "/")
                        remote_parent = "/".join(rp.split("/")[:-1])
                        run(client, f"mkdir -p {remote_parent}")
                        sftp.put(str(lp), rp)

    upload_paths = [
        "pyproject.toml",
        "README.md",
        "alembic.ini",
        "apps",
        "packages",
        "migrations",
        "scripts/bootstrap_homelab.py",
        "scripts/remote_setup.py",
        "scripts/deploy_config.py",
        ".env.example",
    ]

    print("Uploading project files...")
    upload_tree(str(PROJECT_ROOT), args.remote_dir, upload_paths)

    env_content = build_remote_env(local_env, args.host)
    with sftp.open(f"{args.remote_dir}/.env", "w") as remote_env:
        remote_env.write(env_content)

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

    print("\n=== verify post-rec tables ===")
    code, out, err = run(client, 'docker exec stack_postgres psql -U app -d epilogik -c "\\dt" 2>&1')
    print(out.strip() or err.strip())

    client.close()
    print("\nDone. Infrastructure ready on server. App NOT deployed — test locally.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
