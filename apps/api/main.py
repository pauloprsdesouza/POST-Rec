"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from apps.api.database import init_db
from apps.api.observability.logging import configure_logging, get_logger
from apps.api.routers.api import router
from apps.api.routers.auth import router as auth_router
from apps.api.routers.users import router as users_router
from apps.api.services.embedding_config import validate_embedding_configuration
from apps.api.settings import get_settings

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

app.include_router(router)
app.include_router(auth_router)
app.include_router(users_router)
