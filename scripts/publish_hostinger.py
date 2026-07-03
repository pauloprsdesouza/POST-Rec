#!/usr/bin/env python3
"""Upload current workspace to Hostinger, deploy stack, and run smoke tests."""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

import httpx
import paramiko

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DOMAIN = "paulorobertosouza.com.br"
HOST = os.environ.get("HOSTINGER_HOST", "187.127.39.214")
PASSWORD = os.environ.get("HOSTINGER_SSH_PASSWORD", "")
REMOTE_DIR = "/opt/post-rec"
APP_URL = f"https://{DOMAIN}/researchly"

SKIP_DIRS = frozenset({".git", ".venv", "node_modules", "__pycache__", ".pytest_cache", "dist", "build"})

# Keys synced from local .env when set (never printed).
SYNC_KEYS = (
    "GEMINI_API_KEY",
    "GEMINI_GENERATION_MODEL",
    "GEMINI_EMBEDDING_MODEL",
    "GEMINI_EMBEDDING_DIMENSIONS",
    "OPENALEX_API_KEY",
    "OPENALEX_EMAIL",
    "ADMIN_BOOTSTRAP_EMAILS",
    "CROSSREF_EMAIL",
    "SEMANTIC_SCHOLAR_API_KEY",
    "QUALIS_ENABLED",
    "QUALIS_CSV_PATH",
    "QUALIS_BOOST_WEIGHT",
    "QUALIS_USE_REDIS_CACHE",
    "QUALIS_CACHE_TTL",
)


def load_env_file(path: Path) -> dict[str, str]:
    if not path.is_file():
        return {}
    out: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        out[key.strip()] = value.strip().strip('"').strip("'")
    return out


def upsert_env_line(text: str, key: str, value: str) -> str:
    pattern = re.compile(rf"^{re.escape(key)}=.*$", re.MULTILINE)
    line = f"{key}={value}"
    if pattern.search(text):
        return pattern.sub(line, text)
    if text and not text.endswith("\n"):
        text += "\n"
    return text + line + "\n"


def merge_remote_env(remote: str, local: dict[str, str]) -> str:
    env = remote
    for key in SYNC_KEYS:
        value = local.get(key, "").strip()
        if value:
            env = upsert_env_line(env, key, value)
    env = upsert_env_line(env, "API_BASE_URL", APP_URL)
    env = upsert_env_line(env, "FRONTEND_APP_URL", APP_URL)
    env = upsert_env_line(env, "APP_ENV", "production")
    if "GEMINI_GENERATION_MODEL=" not in env:
        env = upsert_env_line(env, "GEMINI_GENERATION_MODEL", "gemini-2.5-flash")
    if "QUALIS_ENABLED=" not in env:
        env = upsert_env_line(env, "QUALIS_ENABLED", "true")
    return env


def ssh_run(client: paramiko.SSHClient, cmd: str, timeout: int = 1800) -> tuple[int, str]:
    _, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    out = (stdout.read() + stderr.read()).decode("utf-8", errors="replace")
    return stdout.channel.recv_exit_status(), out


def upload_tree(sftp: paramiko.SFTPClient, client: paramiko.SSHClient, local_root: Path, remote_root: str) -> None:
    for root, dirs, files in os.walk(local_root):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        rel = Path(root).relative_to(local_root)
        remote_dir = f"{remote_root}/{rel.as_posix()}".rstrip("/")
        if str(rel) != ".":
            ssh_run(client, f"mkdir -p {remote_dir}")
        for name in files:
            if name.endswith((".pyc", ".pyo")) or name == ".env":
                continue
            sftp.put(str(Path(root) / name), f"{remote_dir}/{name}")


def generate_assets() -> None:
    subprocess.run(
        [sys.executable, str(PROJECT_ROOT / "scripts" / "generate_traefik_apps.py"), "--write"],
        check=True,
        cwd=PROJECT_ROOT,
    )


def public_get(url: str, *, timeout: float = 30.0) -> tuple[int, str]:
    try:
        r = httpx.get(url, timeout=timeout, follow_redirects=True)
        return r.status_code, r.text[:500]
    except Exception as exc:
        return 0, str(exc)


def main() -> int:
    if not PASSWORD:
        print("Error: set HOSTINGER_SSH_PASSWORD", file=sys.stderr)
        return 1

    local_env = load_env_file(PROJECT_ROOT / ".env")
    if not local_env.get("OPENALEX_EMAIL") and local_env.get("ADMIN_BOOTSTRAP_EMAILS"):
        local_env["OPENALEX_EMAIL"] = local_env["ADMIN_BOOTSTRAP_EMAILS"].split(",")[0].strip()
    if not local_env.get("GEMINI_API_KEY"):
        print("Warning: GEMINI_API_KEY missing in local .env — LLM runs may fail.", file=sys.stderr)

    print("Generating Traefik assets...")
    generate_assets()
    traefik_yaml = (PROJECT_ROOT / "deploy" / "traefik" / "apps.yaml").read_text(encoding="utf-8")

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    print(f"Connecting to root@{HOST}...")
    client.connect(HOST, username="root", password=PASSWORD, timeout=30, look_for_keys=False, allow_agent=False)

    print(f"Uploading project to {REMOTE_DIR}...")
    ssh_run(client, f"mkdir -p {REMOTE_DIR}")
    sftp = client.open_sftp()
    upload_tree(sftp, client, PROJECT_ROOT, REMOTE_DIR)

    try:
        with sftp.open(f"{REMOTE_DIR}/.env", "r") as f:
            remote_env = f.read().decode("utf-8", errors="replace")
    except FileNotFoundError:
        remote_env = (PROJECT_ROOT / ".env.production.example").read_text(encoding="utf-8")

    merged = merge_remote_env(remote_env, local_env)
    with sftp.open(f"{REMOTE_DIR}/.env", "w") as f:
        f.write(merged)
    print("Merged .env (preserved remote secrets, synced API keys)")

    with sftp.open("/data/coolify/proxy/dynamic/apps.yaml", "w") as f:
        f.write(traefik_yaml.replace("\r\n", "\n"))
    print("Updated Traefik apps.yaml")
    sftp.close()

    compose = (
        f"cd {REMOTE_DIR} && "
        "docker stop post-rec-evolution-manager-1 2>/dev/null || true && "
        "docker rm post-rec-evolution-manager-1 2>/dev/null || true && "
        "docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build"
    )
    print("Building and starting stack (this may take several minutes)...")
    code, out = ssh_run(client, compose, timeout=2400)
    print(out[-8000:])
    if code != 0:
        print(f"compose failed (exit {code})")
        client.close()
        return code

    print("Running database migrations...")
    code, out = ssh_run(
        client,
        f"cd {REMOTE_DIR} && docker compose -f docker-compose.yml -f docker-compose.prod.yml run --rm migrate",
        timeout=600,
    )
    print(out[-3000:])
    if code != 0:
        print(f"migrate failed (exit {code})")
        client.close()
        return code

    ssh_run(client, "docker restart coolify-proxy")
    ssh_run(client, "docker network connect --alias postrec-web coolify post-rec-web-1 2>/dev/null || true")
    time.sleep(12)

    print("Running in-container stack verification...")
    code, out = ssh_run(
        client,
        f"cd {REMOTE_DIR} && docker compose -f docker-compose.yml -f docker-compose.prod.yml exec -T api "
        "python scripts/verify_stack.py",
        timeout=120,
    )
    print(out)
    stack_ok = code == 0

    print("Container status:")
    _, ps_out = ssh_run(
        client,
        f"cd {REMOTE_DIR} && docker compose -f docker-compose.yml -f docker-compose.prod.yml ps",
        timeout=60,
    )
    print(ps_out[-4000:])

    client.close()

    print("\nPublic endpoint smoke tests:")
    tests = [
        ("landing", f"https://{DOMAIN}/"),
        ("researchly health", f"{APP_URL}/api/v1/health"),
        ("researchly web", f"{APP_URL}/"),
        ("evolution root", f"https://{DOMAIN}/evolution/"),
        ("evolution manager", f"https://{DOMAIN}/evolution/manager/"),
        ("portainer", f"https://{DOMAIN}/portainer/"),
        ("portainer locales", f"https://{DOMAIN}/locales/en/translation.json"),
    ]
    failed = 0
    results: list[dict] = []
    for name, url in tests:
        status, body = public_get(url)
        ok = status == 200 or (name == "evolution root" and status in (200, 301, 302))
        if name == "portainer locales" and status == 200 and body.strip().startswith("{"):
            ok = True
        if not ok:
            failed += 1
        results.append({"name": name, "url": url, "status": status, "ok": ok})
        mark = "OK" if ok else "FAIL"
        print(f"  [{mark}] {name}: HTTP {status} — {url}")

    gemini_status, gemini_body = public_get(f"{APP_URL}/api/v1/health")
    worker_code_check = 0
    try:
        c2 = paramiko.SSHClient()
        c2.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        c2.connect(HOST, username="root", password=PASSWORD, timeout=30, look_for_keys=False, allow_agent=False)
        worker_code_check, worker_out = ssh_run(
            c2,
            "docker exec post-rec-worker-1 sh -c '"
            "echo GEMINI_GENERATION_MODEL=$GEMINI_GENERATION_MODEL; "
            "echo OPENALEX_EMAIL=$OPENALEX_EMAIL; "
            "test -n \"$OPENALEX_API_KEY\" && echo OPENALEX_API_KEY=set || echo OPENALEX_API_KEY=missing; "
            "test -n \"$GEMINI_API_KEY\" && echo GEMINI_API_KEY=set || echo GEMINI_API_KEY=missing'"
            "'",
            timeout=30,
        )
        print("\nWorker env:")
        print(worker_out.strip())
        c2.close()
    except Exception as exc:
        print(f"Worker env check failed: {exc}")

    print("\n" + "=" * 60)
    print("PUBLISH SUMMARY")
    print("=" * 60)
    print(f"Researchly:  {APP_URL}")
    print(f"Stack verify: {'PASS' if stack_ok else 'FAIL'}")
    print(f"Public tests: {len(tests) - failed}/{len(tests)} passed")
    if not stack_ok or failed:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
