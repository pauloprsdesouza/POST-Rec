#!/usr/bin/env python3
"""Configure path-based app routing on the apex domain (no per-app DNS)."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import paramiko

PROJECT_ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = PROJECT_ROOT / "deploy" / "apps" / "registry.json"
DOMAIN = "paulorobertosouza.com.br"


def run(client: paramiko.SSHClient, cmd: str, timeout: int = 600) -> tuple[int, str, str]:
    _, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode("utf-8", errors="replace")
    err = stderr.read().decode("utf-8", errors="replace")
    return stdout.channel.recv_exit_status(), out, err


def upload_tree(
    client: paramiko.SSHClient,
    sftp: paramiko.SFTPClient,
    local_root: Path,
    remote_root: str,
) -> None:
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


def patch_env(env: str, *, api_url: str, frontend_url: str) -> str:
    env = re.sub(r"^API_BASE_URL=.*$", f"API_BASE_URL={api_url}", env, flags=re.M)
    env = re.sub(r"^FRONTEND_APP_URL=.*$", f"FRONTEND_APP_URL={frontend_url}", env, flags=re.M)
    if "FRONTEND_APP_URL=" not in env:
        env += f"\nFRONTEND_APP_URL={frontend_url}\n"
    return env


def generate_assets(domain: str) -> None:
    subprocess.run(
        [sys.executable, str(PROJECT_ROOT / "scripts" / "generate_traefik_apps.py"), "--write"],
        check=True,
        cwd=PROJECT_ROOT,
    )
    # Ensure registry domain matches CLI override
    reg_path = PROJECT_ROOT / "deploy" / "apps" / "registry.json"
    if reg_path.is_file():
        reg = json.loads(reg_path.read_text(encoding="utf-8"))
        if reg.get("domain") != domain:
            reg["domain"] = domain
            reg_path.write_text(json.dumps(reg, indent=2) + "\n", encoding="utf-8")
            subprocess.run(
                [sys.executable, str(PROJECT_ROOT / "scripts" / "generate_traefik_apps.py"), "--write"],
                check=True,
                cwd=PROJECT_ROOT,
            )


def main() -> int:
    parser = argparse.ArgumentParser(description="Deploy path-based app routing from registry")
    parser.add_argument("--host", default=os.environ.get("HOSTINGER_HOST"))
    parser.add_argument("--user", default="root")
    parser.add_argument("--password", default=os.environ.get("HOSTINGER_SSH_PASSWORD"))
    parser.add_argument("--key-file", default=os.environ.get("HOSTINGER_SSH_KEY"))
    parser.add_argument("--remote-dir", default="/opt/post-rec")
    parser.add_argument("--domain", default=DOMAIN)
    parser.add_argument("--app", default="researchly", help="Primary app name in registry")
    parser.add_argument("--upload-project", action="store_true")
    args = parser.parse_args()

    if not args.password and not args.key_file:
        print("Error: provide --password or --key-file", file=sys.stderr)
        return 1

    if not args.host:
        print("Error: set --host or HOSTINGER_HOST", file=sys.stderr)
        return 1

    generate_assets(args.domain)
    traefik_content = (PROJECT_ROOT / "deploy" / "traefik" / "apps.yaml").read_text(encoding="utf-8")
    app_url = f"https://{args.domain}/{args.app}"

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    kwargs: dict = {
        "hostname": args.host,
        "username": args.user,
        "timeout": 30,
        "look_for_keys": False,
        "allow_agent": False,
    }
    if args.key_file:
        kwargs["key_filename"] = args.key_file
    else:
        kwargs["password"] = args.password

    print(f"Connecting to {args.user}@{args.host}...")
    client.connect(**kwargs)

    sftp = client.open_sftp()
    with sftp.open("/data/coolify/proxy/dynamic/apps.yaml", "w") as f:
        f.write(traefik_content.replace("\r\n", "\n"))
    print("Wrote /data/coolify/proxy/dynamic/apps.yaml")

    if args.upload_project:
        print(f"Uploading project to {args.remote_dir}...")
        run(client, f"mkdir -p {args.remote_dir}")
        upload_tree(client, sftp, PROJECT_ROOT, args.remote_dir)

    with sftp.open(f"{args.remote_dir}/.env", "r") as f:
        env = f.read().decode()
    env = patch_env(env, api_url=app_url, frontend_url=app_url)
    with sftp.open(f"{args.remote_dir}/.env", "w") as f:
        f.write(env)
    sftp.close()
    print(f"Updated {args.remote_dir}/.env -> {app_url}")

    compose = (
        f"cd {args.remote_dir} && "
        "docker stop post-rec-evolution-manager-1 2>/dev/null || true && "
        "docker rm post-rec-evolution-manager-1 2>/dev/null || true && "
        "docker compose -f docker-compose.yml -f docker-compose.prod.yml "
        "up -d --build landing unknown-app web api worker evolution-api portainer portainer-proxy"
    )
    code, out, err = run(client, compose, timeout=1800)
    text = (out + err)[-6000:]
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode("ascii", errors="replace").decode())
    if code != 0:
        client.close()
        return code

    run(client, "docker restart coolify-proxy")
    run(client, "docker network connect --alias postrec-web coolify post-rec-web-1 2>/dev/null || true")

    client.close()

    print("\n" + "=" * 60)
    print("PATH-BASED ROUTING DEPLOYED")
    print("=" * 60)
    print(f"Home:        https://{args.domain}/")
    print(f"Researchly:    https://{args.domain}/researchly")
    print(f"Evolution:   https://{args.domain}/evolution/manager")
    print(f"Unknown app: https://{args.domain}/<name> -> 404 if not in registry")
    print()
    print("Add apps in deploy/apps/registry.json, then re-run this script.")
    print()
    print("DNS at registro.br / Hostinger (only these two):")
    print(f"  A    @      -> {args.host}")
    print(f"  A    www    -> {args.host}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
