"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse, Response

from apps.api.features import api_router
from apps.api.shared.database import init_db
from apps.api.shared.infra.embedding_config import validate_embedding_configuration
from apps.api.shared.observability.logging import configure_logging, get_logger
from apps.api.shared.observability.metrics import metrics_payload
from apps.api.shared.observability.middleware import RequestContextMiddleware
from apps.api.shared.observability.telemetry import setup_observability
from apps.api.shared.security.headers import SecurityHeadersMiddleware
from apps.api.shared.security.rate_limit import RateLimitMiddleware, metrics_access_allowed
from apps.api.shared.settings import get_settings

configure_logging()
logger = get_logger("postrec-api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    validate_embedding_configuration(settings.gemini_embedding_model)
    # Alembic upgrade reconfigures root logging via alembic.ini; restore before OTEL.
    init_db()
    configure_logging()
    setup_observability(app=app)
    logger.info("app_start")
    yield
    logger.info("app_stop")


_settings = get_settings()
_docs_enabled = _settings.app_env != "production"

app = FastAPI(
    title="Researchly API",
    description="Research smarter — literature-grounded research ideas",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs" if _docs_enabled else None,
    redoc_url="/redoc" if _docs_enabled else None,
    openapi_url="/openapi.json" if _docs_enabled else None,
)

settings = get_settings()
cors_origins = settings.cors_origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials="*" not in cors_origins,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID", "X-Metrics-Token"],
)
app.add_middleware(GZipMiddleware, minimum_size=500)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(RequestContextMiddleware)

app.include_router(api_router)


@app.get("/metrics", include_in_schema=False)
def prometheus_metrics(request: Request) -> Response:
    if not metrics_access_allowed(request):
        raise HTTPException(status_code=403, detail="Metrics access denied")
    payload, content_type = metrics_payload()
    return Response(content=payload, media_type=content_type)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("unhandled_exception", exc_type=type(exc).__name__)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})
