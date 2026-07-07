#!/usr/bin/env python3
"""Upload current workspace to Hostinger, deploy stack, and run smoke tests."""

from __future__ import annotations

import os
import re
import subprocess
import sys
import time
from pathlib import Path

import httpx
import paramiko

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.deploy_config import load_env_file, require_deploy_domain

HOST = os.environ.get("HOSTINGER_HOST", "187.127.39.214")
PASSWORD = os.environ.get("HOSTINGER_SSH_PASSWORD", "")
REMOTE_DIR = "/opt/post-rec"

SKIP_DIRS = frozenset({".git", ".venv", "node_modules", "__pycache__", ".pytest_cache", "dist", "build"})

# Keys synced from local .env when non-empty (secrets never printed).
SYNC_KEYS = (
    "APP_NAME",
    "AUTH_ENABLED",
    "ADMIN_BOOTSTRAP_EMAILS",
    "GEMINI_API_KEY",
    "GEMINI_GENERATION_MODEL",
    "GEMINI_EMBEDDING_MODEL",
    "GEMINI_EMBEDDING_DIMENSIONS",
    "OPENALEX_API_KEY",
    "OPENALEX_EMAIL",
    "CROSSREF_EMAIL",
    "SEMANTIC_SCHOLAR_API_KEY",
    "EVOLUTION_API_URL",
    "EVOLUTION_API_KEY",
    "EVOLUTION_INSTANCE_NAME",
    "WHATSAPP_NOTIFICATIONS_ENABLED",
    "SMTP_HOST",
    "SMTP_PORT",
    "SMTP_USER",
    "SMTP_PASSWORD",
    "SMTP_USE_TLS",
    "EMAIL_FROM",
    "EMAIL_FROM_NAME",
    "OTP_LENGTH",
    "OTP_TTL_MINUTES",
    "OTP_RESEND_SECONDS",
    "OTP_MAX_ATTEMPTS",
    "PHONE_DEFAULT_COUNTRY_CODE",
    "LOG_LEVEL",
    "LOG_FORMAT",
    "OTEL_ENABLED",
    "QUALIS_ENABLED",
    "QUALIS_CSV_PATH",
    "QUALIS_BOOST_WEIGHT",
    "QUALIS_USE_REDIS_CACHE",
    "QUALIS_CACHE_TTL",
    "EXPERIMENT_FGGV_VS_SOTA_ID",
    "EXPERIMENT_TREATMENT_FRACTION",
    "PORTAINER_ADMIN_PASSWORD_HASH",
    "METRICS_TOKEN",
    "EVOLUTION_CORS_ORIGIN",
)

# Never overwrite server-generated secrets from a developer .env.
SKIP_SYNC_KEYS = frozenset({"JWT_SECRET"})


def upsert_env_line(text: str, key: str, value: str) -> str:
    pattern = re.compile(rf"^{re.escape(key)}=.*$", re.MULTILINE)
    line = f"{key}={value}"
    if pattern.search(text):
        return pattern.sub(line, text)
    if text and not text.endswith("\n"):
        text += "\n"
    return text + line + "\n"


def merge_remote_env(
    remote: str,
    local: dict[str, str],
    *,
    app_url: str,
    domain: str,
    grafana_password_fallback: str = "",
) -> str:
    env = remote
    for key in SYNC_KEYS:
        if key in SKIP_SYNC_KEYS:
            continue
        value = local.get(key, "").strip()
        if value:
            env = upsert_env_line(env, key, value)
    env = upsert_env_line(env, "APP_ENV", "production")
    env = upsert_env_line(env, "APP_NAME", "researchly")
    env = upsert_env_line(env, "API_BASE_URL", app_url)
    env = upsert_env_line(env, "FRONTEND_APP_URL", app_url)
    env = upsert_env_line(env, "DEPLOY_DOMAIN", domain)
    if "LETSENCRYPT_EMAIL=" not in env:
        email = local.get("LETSENCRYPT_EMAIL", "").strip() or f"admin@{domain}"
        env = upsert_env_line(env, "LETSENCRYPT_EMAIL", email)
    grafana_root = local.get("GRAFANA_ROOT_URL", "").strip() or f"https://{domain}/grafana/"
    if not grafana_root.endswith("/"):
        grafana_root += "/"
    env = upsert_env_line(env, "GRAFANA_ROOT_URL", grafana_root)
    if "GRAFANA_ADMIN_PASSWORD=" not in env:
        grafana_password = local.get("GRAFANA_ADMIN_PASSWORD", "").strip() or grafana_password_fallback.strip()
        if grafana_password:
            env = upsert_env_line(env, "GRAFANA_ADMIN_PASSWORD", grafana_password)
    if "GRAFANA_ADMIN_USER=" not in env:
        env = upsert_env_line(env, "GRAFANA_ADMIN_USER", "admin")
    if "GEMINI_GENERATION_MODEL=" not in env:
        env = upsert_env_line(env, "GEMINI_GENERATION_MODEL", "gemini-2.5-flash")
    if "QUALIS_ENABLED=" not in env:
        env = upsert_env_line(env, "QUALIS_ENABLED", "true")
    if "AUTH_ENABLED=" not in env:
        env = upsert_env_line(env, "AUTH_ENABLED", "true")
    if "EVOLUTION_CORS_ORIGIN=" not in env:
        cors_origin = local.get("EVOLUTION_CORS_ORIGIN", "").strip() or f"https://{domain}"
        env = upsert_env_line(env, "EVOLUTION_CORS_ORIGIN", cors_origin)
    if "PORTAINER_ADMIN_PASSWORD_HASH=" not in env:
        portainer_hash = local.get("PORTAINER_ADMIN_PASSWORD_HASH", "").strip()
        if portainer_hash:
            env = upsert_env_line(env, "PORTAINER_ADMIN_PASSWORD_HASH", portainer_hash)
    return env


def verify_production_runtime(client: paramiko.SSHClient) -> tuple[bool, str]:
    """Ensure api container runs in production with SMTP configured (no OTP dev fallback)."""
    cmd = (
        "docker exec post-rec-api-1 python -c "
        "\"from apps.api.shared.settings import get_settings; "
        "from apps.api.features.auth.email import email_service; "
        "s=get_settings(); "
        "print('app_env', s.app_env); "
        "print('smtp_host', s.smtp_host or ''); "
        "print('email_configured', email_service.is_configured())\""
    )
    code, out = ssh_run(client, cmd, timeout=60)
    if code != 0:
        return False, out.strip() or "runtime check failed"

    lines = dict(line.split(" ", 1) for line in out.strip().splitlines() if " " in line)
    app_env = lines.get("app_env", "")
    smtp_host = lines.get("smtp_host", "")
    email_configured = lines.get("email_configured", "")

    issues: list[str] = []
    if app_env != "production":
        issues.append(f"APP_ENV is {app_env!r}, expected 'production'")
    if not smtp_host:
        issues.append("SMTP_HOST is empty in running api container")
    if email_configured.lower() != "true":
        issues.append("email_service.is_configured() is false")

    if issues:
        return False, "; ".join(issues)
    return True, f"production OK (SMTP: {smtp_host})"


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

COOLIFY_CONTAINERS = (
    "coolify-proxy",
    "coolify",
    "coolify-realtime",
    "coolify-db",
    "coolify-redis",
)


def cleanup_coolify(client: paramiko.SSHClient) -> None:
    """Stop legacy Coolify containers if present (does not delete /data/coolify)."""
    for name in COOLIFY_CONTAINERS:
        ssh_run(client, f"docker stop {name} 2>/dev/null || true")
        ssh_run(client, f"docker rm {name} 2>/dev/null || true")
    print("Cleaned up legacy Coolify containers (if any)")


def restart_traefik(client: paramiko.SSHClient) -> None:
    ssh_run(
        client,
        f"cd {REMOTE_DIR} && docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d traefik",
    )
    ssh_run(
        client,
        f"cd {REMOTE_DIR} && docker compose -f docker-compose.yml -f docker-compose.prod.yml restart traefik",
    )


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
    if not HOST:
        print("Error: set HOSTINGER_HOST", file=sys.stderr)
        return 1

    try:
        domain = require_deploy_domain()
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    app_url = f"https://{domain}/researchly"

    local_env = load_env_file(PROJECT_ROOT / ".env")
    if not local_env.get("OPENALEX_EMAIL") and local_env.get("ADMIN_BOOTSTRAP_EMAILS"):
        local_env["OPENALEX_EMAIL"] = local_env["ADMIN_BOOTSTRAP_EMAILS"].split(",")[0].strip()
    if not local_env.get("GEMINI_API_KEY"):
        print("Warning: GEMINI_API_KEY missing in local .env — LLM runs may fail.", file=sys.stderr)
    if not local_env.get("SMTP_HOST"):
        print("Warning: SMTP_HOST missing in local .env — OTP emails will fall back to dev code.", file=sys.stderr)

    print("Generating Traefik assets...")
    generate_assets()

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

    grafana_password_fallback = ""
    if "GRAFANA_ADMIN_PASSWORD=" not in remote_env:
        _, grafana_password_fallback = ssh_run(
            client,
            "docker inspect postrec-grafana --format '{{range .Config.Env}}{{println .}}{{end}}' 2>/dev/null "
            "| grep '^GF_SECURITY_ADMIN_PASSWORD=' | cut -d= -f2-",
            timeout=30,
        )
        grafana_password_fallback = grafana_password_fallback.strip()

    if "PORTAINER_ADMIN_PASSWORD_HASH=" not in remote_env and not local_env.get("PORTAINER_ADMIN_PASSWORD_HASH", "").strip():
        _, portainer_hash_out = ssh_run(
            client,
            "docker inspect postrec-portainer --format '{{range .Config.Cmd}}{{println .}}{{end}}' 2>/dev/null "
            "| grep '^--admin-password=' | cut -d= -f2-",
            timeout=30,
        )
        portainer_hash = portainer_hash_out.strip()
        if portainer_hash:
            remote_env = upsert_env_line(remote_env, "PORTAINER_ADMIN_PASSWORD_HASH", portainer_hash)

    merged = merge_remote_env(
        remote_env,
        local_env,
        app_url=app_url,
        domain=domain,
        grafana_password_fallback=grafana_password_fallback,
    )
    with sftp.open(f"{REMOTE_DIR}/.env", "w") as f:
        f.write(merged)
    synced = [k for k in SYNC_KEYS if k not in SKIP_SYNC_KEYS and local_env.get(k, "").strip()]
    print(f"Merged .env (synced {len(synced)} keys from local .env, APP_ENV=production)")

    sftp.close()

    cleanup_coolify(client)

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

    restart_traefik(client)
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

    print("Verifying production runtime (APP_ENV + SMTP)...")
    prod_ok, prod_detail = verify_production_runtime(client)
    print(prod_detail)

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
        ("landing", f"https://{domain}/"),
        ("researchly health", f"{app_url}/api/v1/health"),
        ("researchly web", f"{app_url}/"),
        ("evolution root", f"https://{domain}/evolution/"),
        ("evolution manager", f"https://{domain}/evolution/manager/"),
        ("portainer", f"https://{domain}/portainer/"),
        ("portainer locales", f"https://{domain}/locales/en/translation.json"),
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

    gemini_status, gemini_body = public_get(f"{app_url}/api/v1/health")
    try:
        c2 = paramiko.SSHClient()
        c2.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        c2.connect(HOST, username="root", password=PASSWORD, timeout=30, look_for_keys=False, allow_agent=False)
        worker_code_check, worker_out = ssh_run(
            c2,
            "docker exec post-rec-worker-1 sh -c "
            "'echo APP_ENV=$APP_ENV; echo SMTP_HOST=$SMTP_HOST; "
            "test -n \"$OPENALEX_API_KEY\" && echo OPENALEX_API_KEY=set || echo OPENALEX_API_KEY=missing; "
            "test -n \"$GEMINI_API_KEY\" && echo GEMINI_API_KEY=set || echo GEMINI_API_KEY=missing'",
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
    print(f"Researchly:  {app_url}")
    print(f"Stack verify: {'PASS' if stack_ok else 'FAIL'}")
    print(f"Production config: {'PASS' if prod_ok else 'FAIL'}")
    print(f"Public tests: {len(tests) - failed}/{len(tests)} passed")
    if not stack_ok or failed or not prod_ok:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
