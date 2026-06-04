#!/usr/bin/env python3
"""Verify homelab connectivity and initialize POST-Rec schema."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import amqp
import redis
from sqlalchemy import create_engine, text

from apps.api.database import init_db
from apps.api.settings import get_settings


def main() -> int:
    settings = get_settings()
    print(f"Checking homelab stack for POST-Rec ({settings.app_name})...\n")

    # PostgreSQL + pgvector
    try:
        engine = create_engine(settings.database_url, connect_args={"connect_timeout": 5})
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            version = conn.execute(text("SELECT extversion FROM pg_extension WHERE extname = 'vector'")).scalar()
            if not version:
                print("[postgres] pgvector extension not found — enabling...")
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
                conn.commit()
                version = conn.execute(text("SELECT extversion FROM pg_extension WHERE extname = 'vector'")).scalar()
            print(f"[postgres] OK — pgvector {version}")
    except Exception as exc:
        print(f"[postgres] FAIL — {exc}")
        return 1

    # Redis
    try:
        client = redis.from_url(settings.redis_url, socket_connect_timeout=5)
        client.ping()
        print("[redis] OK")
    except Exception as exc:
        print(f"[redis] FAIL — {exc}")
        return 1

    # RabbitMQ
    try:
        conn = amqp.Connection(
            host=f"{settings.rabbitmq_host}:{settings.rabbitmq_port}",
            userid=settings.rabbitmq_user,
            password=settings.rabbitmq_password,
            connect_timeout=5,
        )
        conn.connect()
        conn.close()
        print("[rabbitmq] OK")
    except Exception as exc:
        print(f"[rabbitmq] FAIL — {exc}")
        return 1

    # MinIO (optional)
    try:
        from minio import Minio

        host = settings.minio_endpoint
        secure = settings.minio_use_ssl
        client = Minio(host, access_key=settings.minio_access_key, secret_key=settings.minio_secret_key, secure=secure)
        if not client.bucket_exists(settings.minio_bucket):
            client.make_bucket(settings.minio_bucket)
            print(f"[minio] OK — created bucket '{settings.minio_bucket}'")
        else:
            print(f"[minio] OK — bucket '{settings.minio_bucket}' exists")
    except Exception as exc:
        print(f"[minio] WARN — {exc} (optional)")

    # Gemini
    if settings.gemini_api_key:
        print(f"[gemini] OK — model {settings.gemini_generation_model}")
    else:
        print("[gemini] WARN — no API key (fallback mode)")

    # Initialize schema
    print("\nInitializing POST-Rec database schema...")
    init_db()
    print("[schema] OK — all tables created")

    print("\nHomelab bootstrap complete. Start services with:")
    print("  uvicorn apps.api.main:app --reload")
    print("  celery -A apps.api.workers.celery_app worker --loglevel=INFO")
    print("  cd apps/web && npm install && npm run dev")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
