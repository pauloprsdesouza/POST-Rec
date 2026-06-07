"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from apps.api.shared.database import init_db
from apps.api.shared.observability.logging import configure_logging, get_logger
from apps.api.features import api_router, auth_router, users_router
from apps.api.shared.infra.embedding_config import validate_embedding_configuration
from apps.api.shared.settings import get_settings

configure_logging()
logger = get_logger("postrec-api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    validate_embedding_configuration(settings.gemini_embedding_model)
    logger.info("app_start")
    init_db()
    yield
    logger.info("app_stop")


app = FastAPI(
    title="POST-Rec API",
    description="Paper-Oriented Scientific Topic Recommender",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)
app.include_router(auth_router)
app.include_router(users_router)
