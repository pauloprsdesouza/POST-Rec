"""Gemini / LLM provider settings."""

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings

from apps.api.shared.settings._common import (
    DEFAULT_GEMINI_EMBEDDING_DIMENSIONS,
    DEFAULT_GEMINI_EMBEDDING_MODEL,
    SHARED_SETTINGS_CONFIG,
    normalize_embedding_model,
)


class GeminiSettings(BaseSettings):
    model_config = SHARED_SETTINGS_CONFIG

    gemini_api_key: str = ""
    gemini_embedding_model: str = DEFAULT_GEMINI_EMBEDDING_MODEL
    gemini_generation_model: str = "gemini-2.5-flash"
    gemini_embedding_dimensions: int = DEFAULT_GEMINI_EMBEDDING_DIMENSIONS

    @field_validator("gemini_embedding_model", mode="before")
    @classmethod
    def coerce_embedding_model(cls, value: object) -> str:
        if value is None:
            return DEFAULT_GEMINI_EMBEDDING_MODEL
        return normalize_embedding_model(str(value))

    @model_validator(mode="after")
    def normalize_gemini_models(self) -> "GeminiSettings":
        self.gemini_embedding_model = normalize_embedding_model(self.gemini_embedding_model)
        return self
