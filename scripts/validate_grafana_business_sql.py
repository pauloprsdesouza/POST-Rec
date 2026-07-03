#!/usr/bin/env python3
"""Validate all business panel SQL queries against homelab PostgreSQL."""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

import paramiko

ROOT = Path(__file__).resolve().parents[1]
PWD = os.environ.get("SSH_PASSWORD", "")
HOST = os.environ.get("HOMELAB_HOST", "")
USER = os.environ.get("HOMELAB_USER", "paulo")
REMOTE_ENV = os.environ.get("HOMELAB_REMOTE_DIR", "/home/paulo/post-rec")
PANELS_PATH = ROOT / "deploy/homelab/grafana-business-panels.json"


def load_creds() -> tuple[str, str, str]:
    if not PWD:
        raise RuntimeError("Set SSH_PASSWORD")
    if not HOST:
        raise RuntimeError("Set HOMELAB_HOST")

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PWD, timeout=20)

    def run(cmd: str) -> str:
        _, o, e = client.exec_command(cmd, timeout=120)
        return o.read().decode(errors="replace") + e.read().decode(errors="replace")

    line = run(f"grep '^DATABASE_URL=' {REMOTE_ENV}/.env | head -1").strip()
    client.close()
    # postgresql+psycopg://app:pass@host:5432/postrec
    m = re.match(r"DATABASE_URL=postgresql\+psycopg://([^:]+):([^@]+)@", line)
    if not m:
        raise RuntimeError(f"Could not parse DATABASE_URL from: {line[:50]}")
    return m.group(1), m.group(2), "postrec"


def prepare_sql(raw: str) -> str:
    sql = raw
    sql = sql.replace("$__timeFilter(created_at)", "created_at >= NOW() - INTERVAL '90 days'")
    sql = sql.replace("$__timeFilter(started_at)", "started_at >= NOW() - INTERVAL '90 days'")
    sql = sql.replace("$__timeFilter(finished_at)", "finished_at >= NOW() - INTERVAL '90 days'")
    sql = re.sub(
        r"\$__timeGroup\(([^,]+),\s*'1d'\)",
        r"DATE_TRUNC('day', \1)",
        sql,
    )
    sql = re.sub(
        r"\$__timeGroup\(([^,]+),\s*'1w'\)",
        r"DATE_TRUNC('week', \1)",
        sql,
    )
    sql = re.sub(
        r"\$__timeGroupAlias\(([^,]+),\s*'1d',\s*0\)",
        r"DATE_TRUNC('day', \1)",
        sql,
    )
    sql = re.sub(
        r"\$__timeGroupAlias\(([^,]+),\s*'1w',\s*0\)",
        r"DATE_TRUNC('week', \1)",
        sql,
    )
    return sql


def run_sql(user: str, password: str, db: str, sql: str) -> tuple[bool, str]:
    if not HOST:
        raise RuntimeError("Set HOMELAB_HOST")

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PWD, timeout=20)

    # Escape single quotes in SQL for shell
    escaped = sql.replace("'", "'\"'\"'")
    cmd = (
        f"docker exec stack_postgres psql -U {user} -d {db} -v ON_ERROR_STOP=1 "
        f"-c '{escaped}' 2>&1 | tail -5"
    )
    _, o, e = client.exec_command(cmd, timeout=120)
    out = o.read().decode(errors="replace") + e.read().decode(errors="replace")
    client.close()
    ok = "ERROR:" not in out and "FATAL:" not in out
    return ok, out.strip()


def main() -> int:
    if not PWD:
        print("Set SSH_PASSWORD", file=sys.stderr)
        return 1
    if not HOST:
        print("Set HOMELAB_HOST", file=sys.stderr)
        return 1

    user, password, db = load_creds()
    panels = json.loads(PANELS_PATH.read_text(encoding="utf-8"))
    failures: list[tuple[int, str, str, str]] = []

    for panel in panels:
        if panel.get("type") == "row":
            continue
        pid = panel.get("id")
        title = panel.get("title", "?")
        for target in panel.get("targets", []):
            raw = target.get("rawSql")
            if not raw:
                continue
            sql = prepare_sql(raw)
            ok, out = run_sql(user, password, db, sql)
            status = "OK" if ok else "FAIL"
            print(f"[{status}] {pid} {title}")
            if not ok:
                failures.append((pid, title, raw[:120], out))
                print(f"       {out[:300]}")

    print(f"\n{len(failures)} failing panel(s) of {sum(1 for p in panels if p.get('type')!='row')}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
