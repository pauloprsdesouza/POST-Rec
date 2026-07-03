"""HTTP middleware for request correlation and structured access logs."""

from __future__ import annotations

import time
import uuid

import structlog
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from apps.api.shared.observability.logging import get_logger
from apps.api.shared.observability.metrics import normalize_endpoint, record_http_request

logger = get_logger("postrec-http")


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        endpoint = normalize_endpoint(request.url.path)

        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            http_method=request.method,
            http_path=endpoint,
        )

        start = time.perf_counter()
        status_code = 500
        response: Response | None = None
        try:
            response = await call_next(request)
            status_code = response.status_code
            response.headers["X-Request-ID"] = request_id
            return response
        finally:
            duration = time.perf_counter() - start
            if request.url.path != "/metrics":
                record_http_request(
                    method=request.method,
                    endpoint=endpoint,
                    status=str(status_code),
                    duration_seconds=duration,
                )
            logger.info(
                "http_request",
                status_code=status_code,
                duration_ms=round(duration * 1000, 2),
            )
            structlog.contextvars.clear_contextvars()
