"""Application settings composed from domain-specific groups."""

from functools import lru_cache
from urllib.parse import quote_plus

from pydantic import model_validator
from pydantic_settings import BaseSettings

from apps.api.shared.settings._common import (
    DEFAULT_GEMINI_EMBEDDING_DIMENSIONS,
    DEFAULT_GEMINI_EMBEDDING_MODEL,
    SHARED_SETTINGS_CONFIG,
    normalize_embedding_model,
)
from apps.api.shared.settings.gemini import GeminiSettings
from apps.api.shared.settings.infrastructure import InfrastructureSettings
from apps.api.shared.settings.pipeline import PipelineSettings
from apps.api.shared.settings.platform import PlatformSettings
from apps.api.shared.settings.retrieval import RetrievalSettings

__all__ = [
    "DEFAULT_GEMINI_EMBEDDING_DIMENSIONS",
    "DEFAULT_GEMINI_EMBEDDING_MODEL",
    "Settings",
    "get_settings",
    "normalize_embedding_model",
]


class Settings(
    InfrastructureSettings,
    GeminiSettings,
    RetrievalSettings,
    PipelineSettings,
    PlatformSettings,
    BaseSettings,
):
    """Flat settings surface backed by domain-specific setting groups."""

    model_config = SHARED_SETTINGS_CONFIG

    @property
    def cors_origins(self) -> list[str]:
        raw = self.cors_allowed_origins.strip()
        if raw:
            if raw == "*":
                return ["*"]
            return [origin.strip() for origin in raw.split(",") if origin.strip()]

        origins = {self.frontend_app_url.rstrip("/")}
        if self.app_env == "development":
            for host in ("localhost", "127.0.0.1"):
                for port in range(5173, 5181):
                    origins.add(f"http://{host}:{port}")
        return sorted(origins)

    @model_validator(mode="after")
    def resolve_connection_urls(self) -> "Settings":
        pwd = quote_plus(self.rabbitmq_password)
        user = quote_plus(self.rabbitmq_user)

        if not self.celery_broker_url and self.rabbitmq_password:
            self.celery_broker_url = f"pyamqp://{user}:{pwd}@{self.rabbitmq_host}:{self.rabbitmq_port}//"
        if not self.redis_url and self.rabbitmq_password:
            self.redis_url = f"redis://:{pwd}@{self.rabbitmq_host}:6379/0"
        if not self.celery_result_backend and self.rabbitmq_password:
            self.celery_result_backend = f"redis://:{pwd}@{self.rabbitmq_host}:6379/1"
        return self

    @model_validator(mode="after")
    def validate_production_secrets(self) -> "Settings":
        if self.app_env != "production":
            return self
        if self.auth_enabled and not self.jwt_secret.strip():
            raise ValueError("JWT_SECRET is required when APP_ENV=production and AUTH_ENABLED=true")
        if self.jwt_secret == "dev-jwt-secret-change-in-production":
            raise ValueError("JWT_SECRET must be changed from the development default in production")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
