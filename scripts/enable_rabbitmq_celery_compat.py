#!/usr/bin/env python3
"""Enable RabbitMQ 4 compatibility for Celery on homelab server."""

from __future__ import annotations

import argparse
import os
import sys

import paramiko


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default=os.environ.get("HOMELAB_HOST", os.environ.get("SSH_HOST")))
    parser.add_argument("--user", default=os.environ.get("HOMELAB_USER", os.environ.get("SSH_USER", "paulo")))
    parser.add_argument("--password", default=os.environ.get("SSH_PASSWORD"))
    args = parser.parse_args()

    if not args.host:
        print("Error: set --host, HOMELAB_HOST, or SSH_HOST", file=sys.stderr)
        return 1
    if not args.password:
        print("Error: set --password or SSH_PASSWORD", file=sys.stderr)
        return 1

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(args.host, username=args.user, password=args.password, timeout=15)

    cmds = [
        """docker exec stack_rabbitmq sh -c 'cat > /etc/rabbitmq/conf.d/99-celery-compat.conf <<EOF
deprecated_features.permit.transient_nonexcl_queues = true
EOF'""",
        "docker exec stack_rabbitmq cat /etc/rabbitmq/conf.d/99-celery-compat.conf",
        "docker restart stack_rabbitmq",
        "sleep 8",
        "docker exec stack_rabbitmq rabbitmq-diagnostics ping",
    ]

    for cmd in cmds:
        print(f"\n=== {cmd[:60]}... ===")
        _, stdout, stderr = client.exec_command(cmd)
        out = stdout.read().decode("utf-8", errors="replace")
        err = stderr.read().decode("utf-8", errors="replace")
        if out.strip():
            print(out.strip())
        if err.strip():
            print(err.strip())

    client.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
