#!/usr/bin/env python3
"""Verify POST-Rec infrastructure and worker connectivity from current .env."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import amqp
import redis
from sqlalchemy import create_engine, text

from apps.api.shared.settings import get_settings


def check_postgres(database_url: str) -> tuple[bool, str]:
    try:
        engine = create_engine(database_url, connect_args={"connect_timeout": 5})
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            version = conn.execute(
                text("SELECT extversion FROM pg_extension WHERE extname = 'vector'")
            ).scalar()
            if not version:
                return False, "connected but pgvector extension missing"
            tables = conn.execute(
                text(
                    "SELECT COUNT(*) FROM information_schema.tables "
                    "WHERE table_schema = 'public' AND table_name = 'recommendation_run'"
                )
            ).scalar()
            if not tables:
                return False, f"connected (pgvector {version}) but schema not migrated"
            return True, f"ok (pgvector {version})"
    except Exception as exc:
        return False, str(exc)


def check_redis(redis_url: str) -> tuple[bool, str]:
    try:
        client = redis.from_url(redis_url, socket_connect_timeout=5)
        client.ping()
        return True, "ok"
    except Exception as exc:
        return False, str(exc)


def check_rabbitmq(host: str, port: int, user: str, password: str) -> tuple[bool, str]:
    try:
        conn = amqp.Connection(
            host=f"{host}:{port}",
            userid=user,
            password=password,
            connect_timeout=5,
        )
        conn.connect()
        conn.close()
        return True, "ok"
    except Exception as exc:
        return False, str(exc)


def check_minio(endpoint: str, access_key: str, secret_key: str, bucket: str, *, use_ssl: bool) -> tuple[bool, str]:
    try:
        from minio import Minio

        client = Minio(endpoint, access_key=access_key, secret_key=secret_key, secure=use_ssl)
        exists = client.bucket_exists(bucket)
        return True, f"ok (bucket '{bucket}' {'exists' if exists else 'missing'})"
    except Exception as exc:
        return False, str(exc)


def check_evolution(api_url: str, api_key: str, instance_name: str) -> tuple[bool, str]:
    if not api_url or not api_key or not instance_name:
        return True, "not configured (skipped)"

    try:
        import httpx

        headers = {"apikey": api_key}
        with httpx.Client(timeout=10.0) as client:
            root = client.get(f"{api_url.rstrip('/')}/", headers=headers)
            if root.status_code >= 500:
                return False, f"API unreachable (HTTP {root.status_code})"

            response = client.get(
                f"{api_url.rstrip('/')}/instance/fetchInstances",
                headers=headers,
            )
            response.raise_for_status()
            data = response.json()

        instances = data if isinstance(data, list) else data.get("instances") or data.get("data") or []
        names = {
            str(item.get("name") or item.get("instanceName") or "")
            for item in instances
            if isinstance(item, dict)
        }
        if instance_name not in names:
            return (
                False,
                f"instance '{instance_name}' missing — open http://localhost:3000 and scan QR",
            )
        return True, f"ok (instance '{instance_name}')"
    except Exception as exc:
        return False, str(exc)


def main() -> int:
    settings = get_settings()
    print(f"POST-Rec stack verification ({settings.app_env})\n")

    checks: list[tuple[str, bool, str]] = []

    ok, msg = check_postgres(settings.database_url)
    checks.append(("postgres", ok, msg))

    if settings.redis_url:
        ok, msg = check_redis(settings.redis_url)
        checks.append(("redis", ok, msg))
    else:
        checks.append(("redis", False, "REDIS_URL not set"))

    ok, msg = check_rabbitmq(
        settings.rabbitmq_host,
        settings.rabbitmq_port,
        settings.rabbitmq_user,
        settings.rabbitmq_password,
    )
    checks.append(("rabbitmq", ok, msg))

    ok, msg = check_minio(
        settings.minio_endpoint,
        settings.minio_access_key,
        settings.minio_secret_key,
        settings.minio_bucket,
        use_ssl=settings.minio_use_ssl,
    )
    checks.append(("minio", ok, msg))

    if settings.celery_broker_url:
        checks.append(("celery_broker", True, settings.celery_broker_url.split("@")[-1]))
    else:
        checks.append(("celery_broker", False, "CELERY_BROKER_URL not set"))

    ok, msg = check_evolution(
        settings.evolution_api_url,
        settings.evolution_api_key,
        settings.evolution_instance_name,
    )
    checks.append(("evolution_api", ok, msg))

    failed = 0
    for name, ok, msg in checks:
        status = "OK" if ok else "FAIL"
        print(f"[{name}] {status} — {msg}")
        if not ok:
            failed += 1

    if failed:
        print(f"\n{failed} check(s) failed.")
        print("Local Docker infra: copy .env.local.infra.example to .env")
        print("Full Docker stack:  copy .env.docker.example to .env")
        print("Remote homelab:     use 192.168.10.13 hosts in .env")
        return 1

    print("\nAll infrastructure checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
