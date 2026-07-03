#!/usr/bin/env python3
"""Bootstrap Hostinger VPS: Docker, Coolify, and POST-Rec full stack."""

from __future__ import annotations

import argparse
import os
import secrets
import sys
import time
from pathlib import Path

import paramiko

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def load_gemini_key_from_env_file(env_path: Path = PROJECT_ROOT / ".env") -> str:
    if not env_path.is_file():
        return ""
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("GEMINI_API_KEY="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    return ""


def run(client: paramiko.SSHClient, cmd: str, timeout: int = 900) -> tuple[int, str, str]:
    _, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode("utf-8", errors="replace")
    err = stderr.read().decode("utf-8", errors="replace")
    code = stdout.channel.recv_exit_status()
    return code, out, err


def log_step(name: str, code: int, out: str, err: str, tail: int = 4000) -> None:
    print(f"\n{'=' * 60}\n{name}\n{'=' * 60}")
    text = (out + err).strip()
    if text:
        print(text[-tail:])
    print(f"exit: {code}")
    if code != 0:
        raise RuntimeError(f"Step failed: {name}")


def upload_tree(
    client: paramiko.SSHClient,
    sftp: paramiko.SFTPClient,
    local_root: Path,
    remote_root: str,
    *,
    skip_dirs: frozenset[str] = frozenset({".git", ".venv", "node_modules", "__pycache__"}),
) -> None:
    for root, dirs, files in os.walk(local_root):
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        rel_root = Path(root).relative_to(local_root)
        remote_dir = f"{remote_root}/{rel_root.as_posix()}".rstrip("/")
        if str(rel_root) != ".":
            run(client, f"mkdir -p {remote_dir}")
        for name in files:
            if name.endswith((".pyc", ".pyo")) or name == ".env":
                continue
            local_path = Path(root) / name
            remote_path = f"{remote_dir}/{name}"
            sftp.put(str(local_path), remote_path)


def connect(host: str, user: str, password: str | None, key_file: str | None) -> paramiko.SSHClient:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    kwargs: dict = {
        "hostname": host,
        "username": user,
        "timeout": 30,
        "look_for_keys": False,
        "allow_agent": False,
    }
    if key_file:
        kwargs["key_filename"] = key_file
    elif password:
        kwargs["password"] = password
    else:
        raise ValueError("Provide --password or --key-file")
    print(f"Connecting to {user}@{host}...")
    client.connect(**kwargs)
    return client


def main() -> int:
    parser = argparse.ArgumentParser(description="Deploy POST-Rec to Hostinger VPS")
    parser.add_argument("--host", default=os.environ.get("HOSTINGER_HOST"))
    parser.add_argument("--user", default="root")
    parser.add_argument("--password", default=os.environ.get("HOSTINGER_SSH_PASSWORD"))
    parser.add_argument("--key-file", default=os.environ.get("HOSTINGER_SSH_KEY"))
    parser.add_argument("--remote-dir", default="/opt/post-rec")
    parser.add_argument("--repo", default="https://github.com/pauloprsdesouza/POST-Rec.git")
    parser.add_argument("--branch", default="main")
    parser.add_argument("--gemini-api-key", default=os.environ.get("GEMINI_API_KEY", ""))
    parser.add_argument("--base-url", default=os.environ.get("DEPLOY_BASE_URL", ""))
    parser.add_argument(
        "--admin-emails",
        default=os.environ.get("ADMIN_BOOTSTRAP_EMAILS", ""),
        help="Comma-separated admin bootstrap emails (ADMIN_BOOTSTRAP_EMAILS)",
    )
    parser.add_argument("--skip-coolify", action="store_true", help="Only install Docker + compose stack")
    parser.add_argument("--skip-deploy", action="store_true", help="Install Coolify/Docker only")
    parser.add_argument(
        "--from-local",
        action="store_true",
        default=True,
        help="Upload project from this workspace (default; avoids waiting for git push)",
    )
    parser.add_argument("--from-git", action="store_true", help="Clone/pull from --repo instead of local upload")
    args = parser.parse_args()
    if args.from_git:
        args.from_local = False

    if not args.gemini_api_key:
        args.gemini_api_key = load_gemini_key_from_env_file()
        if args.gemini_api_key:
            print("Using GEMINI_API_KEY from local .env")

    if not args.password and not args.key_file:
        print("Error: set --password, HOSTINGER_SSH_PASSWORD, or --key-file", file=sys.stderr)
        return 1

    if not args.host:
        print("Error: set --host or HOSTINGER_HOST", file=sys.stderr)
        return 1

    client = connect(args.host, args.user, args.password, args.key_file)

    jwt_secret = secrets.token_urlsafe(48)
    evolution_key = secrets.token_urlsafe(24)
    base_url = args.base_url.rstrip("/") if args.base_url else f"https://{args.host}"

    steps: list[tuple[str, str]] = [
        ("system info", "uname -a && cat /etc/os-release | head -5 && free -h | head -2 && df -h /"),
        ("apt update", "export DEBIAN_FRONTEND=noninteractive && apt-get update -qq"),
        (
            "install prerequisites",
            "export DEBIAN_FRONTEND=noninteractive && apt-get install -y -qq git curl ca-certificates",
        ),
    ]

    if not args.skip_coolify:
        steps.append(
            (
                "install coolify (includes docker)",
                "curl -fsSL https://cdn.coollabs.io/coolify/install.sh | bash",
            )
        )
    else:
        steps.append(
            (
                "install docker",
                "curl -fsSL https://get.docker.com | sh && systemctl enable --now docker",
            )
        )

    steps.append(("docker version", "docker --version && docker compose version"))

    for name, cmd in steps:
        code, out, err = run(client, cmd)
        log_step(name, code, out, err, tail=6000)

    if args.from_local:
        print(f"\nUploading project from {PROJECT_ROOT} to {args.remote_dir}...")
        run(client, f"mkdir -p {args.remote_dir}")
        sftp = client.open_sftp()
        upload_tree(client, sftp, PROJECT_ROOT, args.remote_dir)
        sftp.close()
        print("Local upload complete.")
    else:
        code, out, err = run(
            client,
            f"mkdir -p {args.remote_dir} && "
            f"(test -d {args.remote_dir}/.git || git clone --branch {args.branch} {args.repo} {args.remote_dir}) && "
            f"cd {args.remote_dir} && git fetch origin && git checkout {args.branch} && git pull --ff-only origin {args.branch}",
        )
        log_step("prepare app directory (git)", code, out, err, tail=6000)

    if args.skip_deploy:
        client.close()
        print("\nCoolify/Docker installed. Skipping POST-Rec deploy (--skip-deploy).")
        print(f"Coolify UI: http://{args.host}:8000")
        return 0

    env_content = f"""APP_ENV=production
APP_NAME=post-rec
API_BASE_URL={base_url}
FRONTEND_APP_URL={base_url}
JWT_SECRET={jwt_secret}
GEMINI_API_KEY={args.gemini_api_key}
GEMINI_GENERATION_MODEL=gemini-2.5-flash
GEMINI_EMBEDDING_MODEL=gemini-embedding-001
GEMINI_EMBEDDING_DIMENSIONS=768
AUTH_ENABLED=true
ADMIN_BOOTSTRAP_EMAILS={args.admin_emails}
DATABASE_URL=postgresql+psycopg://postrec:postrec@postgres:5432/postrec
RABBITMQ_HOST=rabbitmq
RABBITMQ_PORT=5672
RABBITMQ_USER=postrec
RABBITMQ_PASSWORD=postrec
CELERY_BROKER_URL=pyamqp://postrec:postrec@rabbitmq:5672//
REDIS_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/1
CACHE_ENABLED=true
CACHE_REDIS_DB=2
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_USE_SSL=false
MINIO_BUCKET=postrec-artifacts
EVOLUTION_API_URL=http://evolution-api:8080
EVOLUTION_API_KEY={evolution_key}
EVOLUTION_INSTANCE_NAME=postrec
WHATSAPP_NOTIFICATIONS_ENABLED=true
RETRIEVAL_CACHE_ENABLED=true
RETRIEVAL_USE_CELERY_DEFERRED=true
OTEL_ENABLED=false
"""

    sftp = client.open_sftp()
    with sftp.open(f"{args.remote_dir}/.env", "w") as env_file:
        env_file.write(env_content)
    sftp.close()
    print(f"\nWrote {args.remote_dir}/.env with generated secrets")

    deploy_cmd = (
        f"cd {args.remote_dir} && "
        "docker compose -f docker-compose.yml -f docker-compose.prod.yml pull --ignore-buildable 2>/dev/null || true && "
        "docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build"
    )
    code, out, err = run(client, deploy_cmd, timeout=1800)
    log_step("docker compose up", code, out, err, tail=8000)

    migrate_cmd = (
        f"cd {args.remote_dir} && "
        "docker compose -f docker-compose.yml -f docker-compose.prod.yml run --rm migrate"
    )
    code, out, err = run(client, migrate_cmd, timeout=600)
    log_step("database migrate", code, out, err, tail=4000)

    print("\nWaiting for API health...")
    healthy = False
    for attempt in range(24):
        code, out, err = run(
            client,
            f"cd {args.remote_dir} && docker compose exec -T api curl -sf http://localhost:8000/api/v1/health",
            timeout=30,
        )
        if code == 0:
            healthy = True
            print(f"API healthy: {out.strip()}")
            break
        time.sleep(10)
        print(f"  attempt {attempt + 1}/24...")

    code, out, err = run(
        client,
        f"cd {args.remote_dir} && docker compose exec -T api python scripts/verify_stack.py",
        timeout=120,
    )
    log_step("verify stack", code, out, err, tail=6000) if code == 0 else print(out + err)

    code, out, err = run(
        client,
        f"cd {args.remote_dir} && docker compose ps",
        timeout=60,
    )
    log_step("compose ps", code, out, err)

    client.close()

    print("\n" + "=" * 60)
    print("DEPLOYMENT COMPLETE")
    print("=" * 60)
    print(f"Web UI:        {base_url}")
    print(f"API health:    {base_url}/api/v1/health")
    print(f"Coolify:       http://{args.host}:8000")
    print(f"Evolution QR:  docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d evolution-manager")
    print(f"               then expose port 3000 temporarily or use Coolify to proxy")
    if not args.gemini_api_key:
        print("\nWARNING: GEMINI_API_KEY is empty — LLM runs in fallback/dev mode.")
    if not healthy:
        print("\nWARNING: API health check did not pass within timeout. Check: docker compose logs api worker")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
