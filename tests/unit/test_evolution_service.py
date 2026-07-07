"""Unit tests for Evolution API client."""

from unittest.mock import MagicMock, patch

import httpx
import pytest

from apps.api.features.auth.evolution import EvolutionError, evolution_service


def _settings(app_env: str = "development"):
    settings = MagicMock()
    settings.evolution_api_url = "http://192.168.10.13:8080"
    settings.evolution_api_key = "test-key"
    settings.evolution_instance_name = "postrec"
    settings.app_env = app_env
    return settings


def _json_response(payload):
    response = MagicMock()
    response.raise_for_status = MagicMock()
    response.content = b"[]"
    response.json.return_value = payload
    return response


@patch("apps.api.features.auth.evolution.get_settings")
def test_send_text_resolves_jid_and_sends_to_canonical_number(mock_settings):
    """The first send to a BR mobile must target the resolved JID, not the raw 13-digit number."""
    mock_settings.return_value = _settings()

    # Number-check resolves the ninth-digit-stripped canonical JID.
    check_response = _json_response(
        [{"exists": True, "jid": "553498313925@s.whatsapp.net", "number": "5534998313925"}]
    )
    send_response = _json_response({"key": {"remoteJid": "553498313925@s.whatsapp.net"}})

    with patch("httpx.Client") as mock_client:
        post = mock_client.return_value.__enter__.return_value.post
        post.side_effect = [check_response, send_response]

        evolution_service.send_text("5534998313925", "hello")

        assert post.call_count == 2
        check_call, send_call = post.call_args_list
        assert check_call[0][0].endswith("/chat/whatsappNumbers/postrec")
        assert check_call[1]["json"] == {"numbers": ["5534998313925"]}
        assert send_call[0][0].endswith("/message/sendText/postrec")
        assert send_call[1]["json"]["number"] == "553498313925@s.whatsapp.net"


@patch("apps.api.features.auth.evolution.get_settings")
def test_send_text_falls_back_to_raw_number_when_check_fails(mock_settings):
    """If the number-check endpoint is unreachable, still attempt the send with the raw number."""
    mock_settings.return_value = _settings()

    send_response = _json_response({"key": {}})

    with patch("httpx.Client") as mock_client:
        post = mock_client.return_value.__enter__.return_value.post
        post.side_effect = [httpx.ConnectError("boom"), send_response]

        evolution_service.send_text("5582999999999", "hello")

        assert post.call_count == 2
        send_call = post.call_args_list[1]
        assert send_call[0][0].endswith("/message/sendText/postrec")
        assert send_call[1]["json"]["number"] == "5582999999999"


@patch("apps.api.features.auth.evolution.get_settings")
def test_send_text_raises_when_number_not_on_whatsapp(mock_settings):
    mock_settings.return_value = _settings("production")

    check_response = _json_response([{"exists": False, "jid": "5582999999999@s.whatsapp.net"}])

    with patch("httpx.Client") as mock_client:
        post = mock_client.return_value.__enter__.return_value.post
        post.return_value = check_response

        with pytest.raises(EvolutionError):
            evolution_service.send_text("5582999999999", "hello")

        # Should not attempt the actual send when the number does not exist.
        assert post.call_count == 1


@patch("apps.api.features.auth.evolution.get_settings")
def test_send_text_not_configured_in_production(mock_settings):
    settings = MagicMock()
    settings.evolution_api_url = ""
    settings.evolution_api_key = ""
    settings.evolution_instance_name = ""
    settings.app_env = "production"
    mock_settings.return_value = settings

    with pytest.raises(EvolutionError):
        evolution_service.send_text("5582999999999", "hello")


@patch("apps.api.features.auth.evolution.get_settings")
def test_send_text_http_error(mock_settings):
    mock_settings.return_value = _settings("production")

    request = httpx.Request("POST", "http://example.com")
    check_response = _json_response([{"exists": True, "jid": "5582999999999@s.whatsapp.net"}])
    error_response = httpx.Response(400, request=request, text="bad request")

    with patch("httpx.Client") as mock_client:
        post = mock_client.return_value.__enter__.return_value.post
        post.side_effect = [check_response, error_response]

        with pytest.raises(EvolutionError):
            evolution_service.send_text("5582999999999", "hello")
