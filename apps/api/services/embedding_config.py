"""Single source of truth for Gemini embedding model resolution."""

from apps.api.observability.logging import get_logger
from apps.api.settings import (
    DEFAULT_GEMINI_EMBEDDING_MODEL,
    normalize_embedding_model,
)

logger = get_logger("postrec-embedding-config")

DEPRECATED_EMBEDDING_MODELS = frozenset(
    {
        "text-embedding-004",
        "text-embedding-005",
        "text-embedding-003",
        "text-embedding-002",
        "text-embedding-001",
    }
)


def resolve_embedding_model(configured: str | None = None) -> str:
    """Return a Gemini embedding model safe for embedContent.

    Always normalizes legacy OpenAI-style names and rejects deprecated models
    before any API call is made.
    """
    raw = (configured or DEFAULT_GEMINI_EMBEDDING_MODEL).strip()
    resolved = normalize_embedding_model(raw)

    if raw.removeprefix("models/") != resolved:
        logger.warning(
            "embedding_model_auto_corrected",
            configured=raw,
            resolved=resolved,
        )

    if resolved in DEPRECATED_EMBEDDING_MODELS or resolved.startswith("text-embedding-"):
        raise ValueError(
            f"Deprecated embedding model '{raw}' cannot be used. "
            f"Set GEMINI_EMBEDDING_MODEL={DEFAULT_GEMINI_EMBEDDING_MODEL} in your environment."
        )

    return resolved


def validate_embedding_configuration(configured: str) -> str:
    """Validate embedding config at process startup."""
    resolved = resolve_embedding_model(configured)
    logger.info(
        "embedding_model_ready",
        configured=configured,
        resolved=resolved,
    )
    return resolved
