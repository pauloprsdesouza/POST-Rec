"""Unit tests for Evolution API client."""

from unittest.mock import MagicMock, patch

import httpx
import pytest

from apps.api.services.evolution_service import EvolutionError, evolution_service


@patch("apps.api.services.evolution_service.get_settings")
def test_send_text_success(mock_settings):
    settings = MagicMock()
    settings.evolution_api_url = "http://192.168.10.13:8080"
    settings.evolution_api_key = "test-key"
    settings.evolution_instance_name = "postrec"
    settings.app_env = "development"
    mock_settings.return_value = settings

    response = MagicMock()
    response.raise_for_status = MagicMock()

    with patch("httpx.Client") as mock_client:
        mock_client.return_value.__enter__.return_value.post.return_value = response
        evolution_service.send_text("5582999999999", "hello")

        mock_client.return_value.__enter__.return_value.post.assert_called_once()
        call_kwargs = mock_client.return_value.__enter__.return_value.post.call_args
        assert call_kwargs[0][0].endswith("/message/sendText/postrec")
        assert call_kwargs[1]["headers"]["apikey"] == "test-key"


@patch("apps.api.services.evolution_service.get_settings")
def test_send_text_not_configured_in_production(mock_settings):
    settings = MagicMock()
    settings.evolution_api_url = ""
    settings.evolution_api_key = ""
    settings.evolution_instance_name = ""
    settings.app_env = "production"
    mock_settings.return_value = settings

    with pytest.raises(EvolutionError):
        evolution_service.send_text("5582999999999", "hello")


@patch("apps.api.services.evolution_service.get_settings")
def test_send_text_http_error(mock_settings):
    settings = MagicMock()
    settings.evolution_api_url = "http://192.168.10.13:8080"
    settings.evolution_api_key = "test-key"
    settings.evolution_instance_name = "postrec"
    settings.app_env = "production"
    mock_settings.return_value = settings

    request = httpx.Request("POST", "http://example.com")
    response = httpx.Response(400, request=request, text="bad request")

    with patch("httpx.Client") as mock_client:
        mock_client.return_value.__enter__.return_value.post.return_value = response
        with pytest.raises(EvolutionError):
            evolution_service.send_text("5582999999999", "hello")
