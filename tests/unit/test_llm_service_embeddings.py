"""Ensure GeminiService never calls deprecated embedding models."""

from unittest.mock import MagicMock, patch

from apps.api.features.recommendations.llm import GeminiService
from apps.api.shared.settings import DEFAULT_GEMINI_EMBEDDING_MODEL, Settings


@patch("apps.api.features.recommendations.llm.get_settings")
@patch("apps.api.features.recommendations.llm.genai.Client")
def test_generate_embeddings_never_uses_text_embedding_004(mock_client_cls, mock_get_settings):
    mock_get_settings.return_value = Settings(
        gemini_embedding_model="text-embedding-004",
        gemini_api_key="test-key",
        gemini_embedding_dimensions=768,
    )

    mock_client = MagicMock()
    mock_result = MagicMock()
    mock_result.embeddings = [MagicMock(values=[0.0] * 768)]
    mock_client.models.embed_content.return_value = mock_result
    mock_client_cls.return_value = mock_client

    service = GeminiService()
    db = MagicMock()
    service.generate_embeddings(db, "00000000-0000-4000-8000-000000000001", ["paper about AI"])

    model_used = mock_client.models.embed_content.call_args.kwargs["model"]
    assert model_used == DEFAULT_GEMINI_EMBEDDING_MODEL
    assert model_used != "text-embedding-004"
