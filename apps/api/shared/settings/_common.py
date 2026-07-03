"""Shared settings constants and helpers."""

from pathlib import Path

from pydantic_settings import SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[4]
ENV_FILE = PROJECT_ROOT / ".env"

DEFAULT_GEMINI_EMBEDDING_MODEL = "gemini-embedding-001"
DEFAULT_GEMINI_EMBEDDING_DIMENSIONS = 768
DEPRECATED_EMBEDDING_MODEL_PREFIX = "text-embedding-"

SHARED_SETTINGS_CONFIG = SettingsConfigDict(
    env_file=str(ENV_FILE) if ENV_FILE.exists() else None,
    env_file_encoding="utf-8",
    extra="ignore",
)


def normalize_embedding_model(model: str, *, default: str = DEFAULT_GEMINI_EMBEDDING_MODEL) -> str:
    """Normalize GEMINI_EMBEDDING_MODEL values, including legacy names."""
    cleaned = model.strip().removeprefix("models/")
    if not cleaned or cleaned.startswith(DEPRECATED_EMBEDDING_MODEL_PREFIX):
        return default
    return cleaned
