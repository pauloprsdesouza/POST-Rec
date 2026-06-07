"""Gemini settings and embedding model normalization tests."""

from apps.api.shared.settings import (
    DEFAULT_GEMINI_EMBEDDING_DIMENSIONS,
    DEFAULT_GEMINI_EMBEDDING_MODEL,
    Settings,
    get_settings,
    normalize_embedding_model,
)


def test_normalize_embedding_model_maps_legacy_name():
    assert normalize_embedding_model("text-embedding-004") == DEFAULT_GEMINI_EMBEDDING_MODEL


def test_normalize_embedding_model_strips_models_prefix():
    assert normalize_embedding_model("models/gemini-embedding-001") == DEFAULT_GEMINI_EMBEDDING_MODEL


def test_settings_use_default_embedding_model():
    settings = Settings()
    assert settings.gemini_embedding_model == DEFAULT_GEMINI_EMBEDDING_MODEL
    assert settings.gemini_embedding_dimensions == DEFAULT_GEMINI_EMBEDDING_DIMENSIONS


def test_settings_normalize_legacy_env_value():
    settings = Settings(gemini_embedding_model="text-embedding-004")
    assert settings.gemini_embedding_model == DEFAULT_GEMINI_EMBEDDING_MODEL


def test_settings_read_embedding_model_from_env(monkeypatch):
    monkeypatch.setenv("GEMINI_EMBEDDING_MODEL", "gemini-embedding-001")
    monkeypatch.setenv("GEMINI_EMBEDDING_DIMENSIONS", "768")
    get_settings.cache_clear()
    settings = get_settings()
    assert settings.gemini_embedding_model == "gemini-embedding-001"
    assert settings.gemini_embedding_dimensions == 768
    get_settings.cache_clear()
    monkeypatch.delenv("GEMINI_EMBEDDING_MODEL", raising=False)
    monkeypatch.delenv("GEMINI_EMBEDDING_DIMENSIONS", raising=False)
