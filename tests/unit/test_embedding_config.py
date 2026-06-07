"""Embedding model resolution guards."""

from apps.api.services.embedding_config import resolve_embedding_model, validate_embedding_configuration
from apps.api.settings import DEFAULT_GEMINI_EMBEDDING_MODEL, Settings, get_settings


def test_resolve_embedding_model_normalizes_legacy_name():
    assert resolve_embedding_model("text-embedding-004") == DEFAULT_GEMINI_EMBEDDING_MODEL


def test_resolve_embedding_model_keeps_current_name():
    assert resolve_embedding_model("gemini-embedding-001") == DEFAULT_GEMINI_EMBEDDING_MODEL


def test_settings_field_validator_normalizes_legacy_env_value():
    settings = Settings(gemini_embedding_model="text-embedding-004")
    assert settings.gemini_embedding_model == DEFAULT_GEMINI_EMBEDDING_MODEL


def test_validate_embedding_configuration_accepts_current_model():
    assert validate_embedding_configuration(DEFAULT_GEMINI_EMBEDDING_MODEL) == DEFAULT_GEMINI_EMBEDDING_MODEL


def test_legacy_env_value_is_safe_at_runtime(monkeypatch):
    monkeypatch.setenv("GEMINI_EMBEDDING_MODEL", "text-embedding-004")
    get_settings.cache_clear()
    settings = get_settings()
    assert settings.gemini_embedding_model == DEFAULT_GEMINI_EMBEDDING_MODEL
    assert resolve_embedding_model(settings.gemini_embedding_model) == DEFAULT_GEMINI_EMBEDDING_MODEL
    get_settings.cache_clear()
    monkeypatch.delenv("GEMINI_EMBEDDING_MODEL", raising=False)


def test_resolve_embedding_model_handles_models_prefix():
    assert resolve_embedding_model("models/text-embedding-004") == DEFAULT_GEMINI_EMBEDDING_MODEL
