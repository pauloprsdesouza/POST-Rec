#!/usr/bin/env python3
"""Run a remote command over SSH (password via SSH_PASSWORD env)."""

from __future__ import annotations

import os
import sys

import paramiko


def main() -> int:
    password = os.environ.get("SSH_PASSWORD")
    if not password:
        print("Error: set SSH_PASSWORD", file=sys.stderr)
        return 1

    host = os.environ.get("SSH_HOST")
    user = os.environ.get("SSH_USER", "paulo")
    cmd = "hostname"

    positional = sys.argv[1:]
    if not host:
        if not positional:
            print("Error: set SSH_HOST or pass host as first argument", file=sys.stderr)
            return 1
        host = positional.pop(0)

    if positional and not os.environ.get("SSH_USER"):
        user = positional.pop(0)
    if positional:
        cmd = positional[0]

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, username=user, password=password, timeout=20)
    _, stdout, stderr = client.exec_command(cmd)
    out = stdout.read().decode("utf-8", errors="replace")
    err = stderr.read().decode("utf-8", errors="replace")
    sys.stdout.buffer.write(out.encode("utf-8", errors="replace"))
    if err:
        sys.stderr.buffer.write(err.encode("utf-8", errors="replace"))
    client.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
