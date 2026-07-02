#!/usr/bin/env python3
"""Migrate Coolify from bundled coolify-db/coolify-redis to POST-Rec shared instances.

Run on the VPS as root after POST-Rec postgres/redis are on the `coolify` network
(docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d postgres redis).

Steps:
  1. Create coolify DB/user on shared-postgres (password from Coolify .env)
  2. pg_dump coolify-db -> restore into shared postgres (if target empty)
  3. Patch /data/coolify/source/.env (DB_HOST, REDIS_HOST, REDIS_DB indexes)
  4. Install compose override; restart Coolify without bundled postgres/redis
  5. Optionally remove stopped evolution-postgres/redis and coolify-db/redis containers

Usage:
  python3 /opt/post-rec/scripts/migrate_coolify_shared_db.py
  python3 /opt/post-rec/scripts/migrate_coolify_shared_db.py --dry-run
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

COOLIFY_ENV = Path("/data/coolify/source/.env")
COOLIFY_SOURCE = Path("/data/coolify/source")
COOLIFY_OVERRIDE_SRC = Path("/opt/post-rec/deploy/coolify/docker-compose.shared-db.yml")
COOLIFY_OVERRIDE_DST = COOLIFY_SOURCE / "docker-compose.shared-db.yml"

POSTREC_COMPOSE = Path("/opt/post-rec")
SHARED_PG_ALIAS = "shared-postgres"
SHARED_REDIS_ALIAS = "shared-redis"
COOLIFY_REDIS_DB = "4"
COOLIFY_REDIS_CACHE_DB = "5"


def run(cmd: list[str] | str, *, check: bool = True, capture: bool = True) -> subprocess.CompletedProcess[str]:
    if isinstance(cmd, str):
        cmd = ["/bin/sh", "-c", cmd]
    result = subprocess.run(cmd, text=True, capture_output=capture)
    if check and result.returncode != 0:
        raise RuntimeError(
            f"Command failed ({result.returncode}): {' '.join(cmd) if isinstance(cmd, list) else cmd}\n"
            f"{result.stdout}\n{result.stderr}"
        )
    return result


def parse_env(path: Path) -> dict[str, str]:
    data: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        data[key.strip()] = value.strip().strip('"').strip("'")
    return data


def write_env(path: Path, data: dict[str, str]) -> None:
    lines = path.read_text(encoding="utf-8").splitlines()
    out: list[str] = []
    seen: set[str] = set()
    for line in lines:
        if "=" in line and not line.strip().startswith("#"):
            key = line.split("=", 1)[0].strip()
            if key in data:
                out.append(f"{key}={data[key]}")
                seen.add(key)
                continue
        out.append(line)
    for key, value in data.items():
        if key not in seen:
            out.append(f"{key}={value}")
    path.write_text("\n".join(out) + "\n", encoding="utf-8")


def shared_postgres_container() -> str:
    result = run(
        "docker ps --format '{{.Names}}' | grep -E 'post-rec-postgres-1$' | head -1",
        check=False,
    )
    name = result.stdout.strip()
    if not name:
        raise RuntimeError("post-rec-postgres-1 not running — start POST-Rec postgres first")
    return name


def ensure_on_coolify_network(container: str) -> None:
    aliases = run(
        f"docker network inspect coolify --format '{{{{json .Containers}}}}' 2>/dev/null",
        check=False,
    ).stdout
    if container not in aliases:
        run(f"docker network connect --alias {SHARED_PG_ALIAS} coolify {container} 2>/dev/null || "
            f"docker network connect coolify {container}")


def ensure_coolify_db(pg_container: str, env: dict[str, str], dry_run: bool) -> None:
    user = env.get("DB_USERNAME", "coolify")
    password = env.get("DB_PASSWORD", "")
    database = env.get("DB_DATABASE", "coolify")
    if not password:
        raise RuntimeError("DB_PASSWORD missing in Coolify .env")

    escaped = password.replace("'", "''")
    user_sql = f"""
DO $$ BEGIN
  CREATE USER {user} WITH PASSWORD '{escaped}';
EXCEPTION WHEN duplicate_object THEN
  ALTER USER {user} WITH PASSWORD '{escaped}';
END $$;
"""
    db_sql = (
        f"SELECT 'CREATE DATABASE {database} OWNER {user}' "
        f"WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '{database}')\\gexec\n"
        f"GRANT ALL PRIVILEGES ON DATABASE {database} TO {user};"
    )
    if dry_run:
        print(f"[dry-run] Would bootstrap database {database} for user {user} on {pg_container}")
        return
    for sql in (user_sql, db_sql):
        proc = subprocess.run(
            ["docker", "exec", "-i", pg_container, "psql", "-U", "postrec", "-d", "postgres", "-v", "ON_ERROR_STOP=1"],
            input=sql,
            text=True,
            capture_output=True,
        )
        if proc.returncode != 0:
            raise RuntimeError(f"Bootstrap SQL failed:\n{proc.stdout}\n{proc.stderr}")


def table_count(pg_container: str, user: str, database: str) -> int:
    result = run(
        f"docker exec {pg_container} psql -U {user} -d {database} -tc "
        f"\"SELECT count(*) FROM information_schema.tables WHERE table_schema='public';\"",
        check=False,
    )
    try:
        return int(result.stdout.strip())
    except ValueError:
        return 0


def migrate_postgres_data(
    pg_container: str,
    env: dict[str, str],
    dry_run: bool,
) -> None:
    user = env.get("DB_USERNAME", "coolify")
    database = env.get("DB_DATABASE", "coolify")
    target_tables = table_count(pg_container, user, database)

    if target_tables > 5:
        print(f"Shared postgres database '{database}' already has {target_tables} tables — skipping dump/restore")
        return

    if not run("docker ps --format '{{.Names}}' | grep -x coolify-db", check=False).stdout.strip():
        print("coolify-db not running — assuming postgres data already migrated or fresh install")
        return

    dump_cmd = f"docker exec coolify-db pg_dump -U {user} -d {database} --no-owner --no-acl"
    restore_cmd = f"docker exec -i {pg_container} psql -U {user} -d {database} -v ON_ERROR_STOP=1"
    if dry_run:
        print(f"[dry-run] Would pipe: {dump_cmd} | {restore_cmd}")
        return

    print("Dumping coolify-db and restoring to shared postgres...")
    dump = subprocess.run(
        dump_cmd,
        shell=True,
        text=True,
        capture_output=True,
    )
    if dump.returncode != 0:
        raise RuntimeError(f"pg_dump failed:\n{dump.stdout}\n{dump.stderr}")
    restore = subprocess.run(
        restore_cmd,
        shell=True,
        input=dump.stdout,
        text=True,
        capture_output=True,
    )
    if restore.returncode != 0:
        raise RuntimeError(f"Restore failed:\n{restore.stdout}\n{restore.stderr}")
    print("Postgres migration complete")


def patch_coolify_env(env_path: Path, dry_run: bool) -> None:
    env = parse_env(env_path)
    updates = {
        "DB_HOST": SHARED_PG_ALIAS,
        "DB_PORT": "5432",
        "REDIS_HOST": SHARED_REDIS_ALIAS,
        "REDIS_PORT": "6379",
        "REDIS_PASSWORD": "",
        "REDIS_DB": COOLIFY_REDIS_DB,
        "REDIS_CACHE_DB": COOLIFY_REDIS_CACHE_DB,
    }
    env.update(updates)
    if dry_run:
        print(f"[dry-run] Would patch {env_path}: {updates}")
        return
    backup = env_path.parent / f"{env_path.name}.bak-shared-db"
    if not backup.exists():
        shutil.copy2(env_path, backup)
    write_env(env_path, updates)
    print(f"Patched {env_path} (backup at {backup})")


def install_compose_override(dry_run: bool) -> None:
    if not COOLIFY_OVERRIDE_SRC.is_file():
        raise RuntimeError(f"Missing {COOLIFY_OVERRIDE_SRC}")
    if dry_run:
        print(f"[dry-run] Would copy override to {COOLIFY_OVERRIDE_DST}")
        return
    shutil.copy2(COOLIFY_OVERRIDE_SRC, COOLIFY_OVERRIDE_DST)
    print(f"Installed {COOLIFY_OVERRIDE_DST}")


def restart_coolify(dry_run: bool) -> None:
    cmd = (
        f"cd {COOLIFY_SOURCE} && "
        "docker compose -f docker-compose.shared-db.yml up -d --remove-orphans"
    )
    if dry_run:
        print(f"[dry-run] Would run: {cmd}")
        return
    run(cmd)
    for attempt in range(18):
        health = run("curl -sf http://127.0.0.1:8000/api/health", check=False)
        if health.returncode == 0:
            print("Coolify healthy on shared postgres/redis")
            return
        time.sleep(5)
    raise RuntimeError("Coolify health check failed after restart — see docker logs coolify")


def cleanup_old_containers(dry_run: bool) -> None:
    old = [
        "coolify-db",
        "coolify-redis",
        "post-rec-evolution-postgres-1",
        "post-rec-evolution-redis-1",
    ]
    running = run("docker ps -a --format '{{.Names}}'", check=False).stdout.splitlines()
    for name in old:
        if name in running:
            msg = f"{'[dry-run] Would remove' if dry_run else 'Removing'} container {name}"
            print(msg)
            if not dry_run:
                run(f"docker rm -f {name}", check=False)


def main() -> int:
    parser = argparse.ArgumentParser(description="Migrate Coolify to shared Postgres/Redis")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--skip-cleanup", action="store_true")
    args = parser.parse_args()

    if not COOLIFY_ENV.is_file():
        print(f"Coolify not installed at {COOLIFY_ENV}", file=sys.stderr)
        return 1

    env = parse_env(COOLIFY_ENV)
    pg = shared_postgres_container()
    redis_container = run(
        "docker ps --format '{{.Names}}' | grep -E 'post-rec-redis-1$' | head -1",
        check=False,
    ).stdout.strip()
    if not redis_container:
        raise RuntimeError("post-rec-redis-1 not running")

    print(f"Using postgres container: {pg}")
    print(f"Using redis container: {redis_container}")

    if not args.dry_run:
        ensure_on_coolify_network(pg)
        run(
            f"docker network connect --alias {SHARED_REDIS_ALIAS} coolify {redis_container} 2>/dev/null || true",
            check=False,
        )

    ensure_coolify_db(pg, env, args.dry_run)
    migrate_postgres_data(pg, env, args.dry_run)
    patch_coolify_env(COOLIFY_ENV, args.dry_run)
    install_compose_override(args.dry_run)
    restart_coolify(args.dry_run)

    if not args.skip_cleanup:
        cleanup_old_containers(args.dry_run)

    print("\nDone. Verify:")
    print("  curl -sf http://127.0.0.1:8000/api/health")
    print(f"  docker exec {pg} psql -U postrec -d postgres -c '\\l'")
    print(f"  docker exec {redis_container} redis-cli INFO keyspace")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
