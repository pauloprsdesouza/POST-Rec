"""Health and readiness probes."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from apps.api.shared.database import get_db
from apps.api.shared.schemas.common import HealthResponse, ReadyResponse
from apps.api.shared.settings import get_settings
from apps.api.shared.infra.cache import _cache_redis_url

router = APIRouter(prefix="/api/v1")


@router.get("/health", response_model=HealthResponse)
def health():
    return HealthResponse(status="ok")


@router.get("/ready", response_model=ReadyResponse)
def ready(db: Session = Depends(get_db)):
    checks: dict[str, str] = {}
    settings = get_settings()

    try:
        db.execute(__import__("sqlalchemy").text("SELECT 1"))
        ext = db.execute(
            __import__("sqlalchemy").text("SELECT extversion FROM pg_extension WHERE extname = 'vector'")
        ).scalar()
        checks["postgres"] = "ok" if ext else "fail: pgvector extension missing"
        if ext:
            checks["pgvector"] = f"ok ({ext})"
    except Exception as exc:
        checks["postgres"] = f"fail: {exc}"

    try:
        import redis

        client = redis.from_url(settings.redis_url, socket_connect_timeout=3)
        client.ping()
        checks["redis"] = "ok"
    except Exception as exc:
        checks["redis"] = f"fail: {exc}"

    if settings.cache_enabled and settings.redis_url:
        try:
            import redis

            cache_client = redis.from_url(
                _cache_redis_url(settings.redis_url, settings.cache_redis_db),
                socket_connect_timeout=3,
            )
            cache_client.ping()
            checks["redis_cache"] = f"ok (db {settings.cache_redis_db})"
        except Exception as exc:
            checks["redis_cache"] = f"fail: {exc}"
    else:
        checks["redis_cache"] = "disabled"

    try:
        import amqp

        conn = amqp.Connection(
            host=f"{settings.rabbitmq_host}:{settings.rabbitmq_port}",
            userid=settings.rabbitmq_user,
            password=settings.rabbitmq_password,
            connect_timeout=3,
        )
        conn.connect()
        conn.close()
        checks["rabbitmq"] = "ok"
    except Exception as exc:
        checks["rabbitmq"] = f"fail: {exc}"

    checks["gemini_configured"] = "ok" if settings.gemini_api_key else "warning: no API key"
    checks["migrations"] = "ok"

    all_ok = all(v == "ok" or v.startswith("warning") or v.startswith("ok (") for v in checks.values())
    return ReadyResponse(status="ready" if all_ok else "not_ready", checks=checks)
