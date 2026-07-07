"""Redis-backed IP rate limiting for sensitive API routes."""

from __future__ import annotations

import ipaddress

from fastapi import Request, status
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request as StarletteRequest
from starlette.responses import JSONResponse, Response

from apps.api.shared.observability.logging import get_logger
from apps.api.shared.settings import get_settings

logger = get_logger("postrec-rate-limit")

AUTH_PREFIX = "/api/v1/auth"
SENSITIVE_PREFIXES = (
    AUTH_PREFIX,
    "/api/v1/recommendation-runs",
    "/api/v1/sessions",
    "/api/v1/feedback",
)


def _client_ip(request: StarletteRequest) -> str:
    forwarded = request.headers.get("X-Forwarded-For", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client and request.client.host:
        return request.client.host
    return "unknown"


def _is_private_ip(host: str) -> bool:
    if host in {"unknown", "127.0.0.1", "::1"}:
        return True
    try:
        return ipaddress.ip_address(host).is_private
    except ValueError:
        return False


def _limit_for_path(path: str, auth_limit: int, default_limit: int) -> int:
    if path.startswith(AUTH_PREFIX):
        return auth_limit
    return default_limit


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app) -> None:
        super().__init__(app)
        self._client = None
        self._enabled = False
        self._configure()

    def _configure(self) -> None:
        settings = get_settings()
        if not settings.api_rate_limit_enabled or not settings.redis_url:
            return
        try:
            import redis

            self._client = redis.from_url(
                settings.redis_url,
                decode_responses=True,
                socket_connect_timeout=2,
                socket_timeout=2,
            )
            self._client.ping()
            self._enabled = True
        except Exception as exc:
            logger.warning("rate_limit_redis_unavailable", error=str(exc))
            self._client = None
            self._enabled = False

    def _check(self, request: StarletteRequest) -> Response | None:
        if not self._enabled or request.method == "OPTIONS":
            return None

        path = request.url.path
        if not any(path.startswith(prefix) for prefix in SENSITIVE_PREFIXES):
            return None

        settings = get_settings()
        client_ip = _client_ip(request)
        limit = _limit_for_path(path, settings.auth_rate_limit_per_minute, settings.api_rate_limit_per_minute)
        window = 60
        key = f"ratelimit:{client_ip}:{request.method}:{path.split('?')[0]}"

        try:
            count = self._client.incr(key)
            if count == 1:
                self._client.expire(key, window)
            if count > limit:
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={"detail": "Too many requests. Try again later."},
                )
        except Exception as exc:
            logger.warning("rate_limit_check_failed", error=str(exc))
        return None

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        blocked = self._check(request)
        if blocked is not None:
            return blocked
        return await call_next(request)


def metrics_access_allowed(request: Request) -> bool:
    settings = get_settings()
    if settings.app_env != "production":
        return True

    token = request.headers.get("X-Metrics-Token", "")
    if settings.metrics_token and token == settings.metrics_token:
        return True

    client_ip = _client_ip(request)
    return _is_private_ip(client_ip)
