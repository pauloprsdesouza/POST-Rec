#!/usr/bin/env python3
"""Finish server-side setup: pip, schema, minio bucket. No app deployment."""

import argparse

import paramiko


def run(client, cmd, timeout=600):
    _, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode("utf-8", errors="replace")
    err = stderr.read().decode("utf-8", errors="replace")
    code = stdout.channel.recv_exit_status()
    return code, out, err


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="192.168.10.13")
    parser.add_argument("--user", default="paulo")
    parser.add_argument("--password", required=True)
    parser.add_argument("--remote-dir", default="/home/paulo/post-rec")
    args = parser.parse_args()

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(args.host, username=args.user, password=args.password, timeout=15)

    rd = args.remote_dir

    cmds = [
        (
            "minio bucket",
            'docker run --rm --network portainer-stack_backend --entrypoint /bin/sh '
            'minio/mc:RELEASE.2025-08-13T08-35-41Z -c '
            '"mc alias set local http://minio:9000 minioadmin CmC3Hzi9Klu34V && '
            'mc mb --ignore-existing local/postrec-artifacts && mc ls local/" 2>&1',
        ),
        (
            "python venv",
            f"cd {rd} && python3 -m venv .venv && .venv/bin/pip install --upgrade pip setuptools wheel 2>&1",
        ),
        (
            "install deps",
            f"cd {rd} && .venv/bin/pip install -e '.[dev]' 2>&1",
        ),
        (
            "bootstrap schema",
            f"cd {rd} && .venv/bin/python scripts/bootstrap_homelab.py 2>&1",
        ),
        (
            "verify tables",
            'docker exec stack_postgres psql -U app -d epilogik -c "\\dt" 2>&1',
        ),
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


if __name__ == "__main__":
    main()
