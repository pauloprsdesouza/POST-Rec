#!/usr/bin/env python3
"""Deploy Portainer and update Traefik routing on the VPS."""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

import paramiko

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DOMAIN = "paulorobertosouza.com.br"


def run(client: paramiko.SSHClient, cmd: str, timeout: int = 600) -> tuple[int, str, str]:
    _, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode("utf-8", errors="replace")
    err = stderr.read().decode("utf-8", errors="replace")
    return stdout.channel.recv_exit_status(), out, err


def main() -> int:
    parser = argparse.ArgumentParser(description="Deploy Portainer on VPS")
    parser.add_argument("--host", default=os.environ.get("HOSTINGER_HOST"))
    parser.add_argument("--user", default="root")
    parser.add_argument("--password", default=os.environ.get("HOSTINGER_SSH_PASSWORD"))
    parser.add_argument("--remote-dir", default="/opt/post-rec")
    args = parser.parse_args()

    if not args.password:
        print("Error: set --password or HOSTINGER_SSH_PASSWORD", file=sys.stderr)
        return 1

    if not args.host:
        print("Error: set --host or HOSTINGER_HOST", file=sys.stderr)
        return 1

    password = args.password

    subprocess.run(
        [sys.executable, str(PROJECT_ROOT / "scripts" / "generate_traefik_apps.py"), "--write"],
        check=True,
        cwd=PROJECT_ROOT,
    )

    traefik = (PROJECT_ROOT / "deploy" / "traefik" / "apps.yaml").read_text(encoding="utf-8")
    files = {
        f"{args.remote_dir}/deploy/apps/registry.json": (PROJECT_ROOT / "deploy/apps/registry.json").read_text(
            encoding="utf-8"
        ),
        f"{args.remote_dir}/docker-compose.prod.yml": (PROJECT_ROOT / "docker-compose.prod.yml").read_text(
            encoding="utf-8"
        ),
        f"{args.remote_dir}/docker-compose.yml": (PROJECT_ROOT / "docker-compose.yml").read_text(encoding="utf-8"),
        f"{args.remote_dir}/deploy/landing/index.html": (
            PROJECT_ROOT / "deploy/landing/index.html"
        ).read_text(encoding="utf-8"),
        f"{args.remote_dir}/deploy/portainer/nginx.conf": (
            PROJECT_ROOT / "deploy/portainer/nginx.conf"
        ).read_text(encoding="utf-8"),
        f"{args.remote_dir}/deploy/portainer/Dockerfile": (
            PROJECT_ROOT / "deploy/portainer/Dockerfile"
        ).read_text(encoding="utf-8"),
    }

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(
        args.host,
        username=args.user,
        password=password,
        timeout=30,
        look_for_keys=False,
        allow_agent=False,
    )

    sftp = client.open_sftp()
    with sftp.open("/data/coolify/proxy/dynamic/apps.yaml", "w") as f:
        f.write(traefik.replace("\r\n", "\n"))
    run(client, f"mkdir -p {args.remote_dir}/deploy/portainer")
    for remote, content in files.items():
        with sftp.open(remote, "w") as f:
            f.write(content.replace("\r\n", "\n"))
    sftp.close()
    print("Uploaded Traefik config and compose files.")

    compose_cmd = (
        f"cd {args.remote_dir} && "
        "docker compose -f docker-compose.yml -f docker-compose.prod.yml "
        "up -d --build portainer portainer-proxy landing"
    )
    code, out, err = run(client, compose_cmd, timeout=300)
    print((out + err)[-4000:])
    if code != 0:
        client.close()
        return code

    run(client, "docker network connect --alias postrec-portainer-proxy coolify postrec-portainer-proxy 2>/dev/null || true")
    run(client, "docker restart coolify-proxy")

    verify_cmds = [
        "docker ps --filter name=postrec-portainer --format '{{.Names}} {{.Status}}'",
        f"curl -sI -H 'Host: {DOMAIN}' http://127.0.0.1/portainer/ | head -5",
        f"curl -sI https://{DOMAIN}/portainer/ | head -8",
    ]
    for cmd in verify_cmds:
        print("===", cmd)
        _, o, e = client.exec_command(cmd, timeout=60)
        print((o.read() + e.read()).decode("utf-8", errors="replace"))

    client.close()

    print("\n" + "=" * 60)
    print("PORTAINER DEPLOYED")
    print("=" * 60)
    print(f"URL:      https://{DOMAIN}/portainer/")
    print("Username: admin")
    print("Password: CmC3Hzi9Klu34V")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
