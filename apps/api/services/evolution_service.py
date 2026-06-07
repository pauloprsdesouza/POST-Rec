"""WhatsApp messaging via Evolution API."""

import httpx

from apps.api.observability.logging import get_logger
from apps.api.settings import get_settings

logger = get_logger("postrec-evolution")


class EvolutionError(Exception):
    pass


class EvolutionService:
    def is_configured(self) -> bool:
        settings = get_settings()
        return bool(settings.evolution_api_url and settings.evolution_api_key and settings.evolution_instance_name)

    def send_text(self, phone_number: str, text: str) -> None:
        settings = get_settings()
        if not self.is_configured():
            if settings.app_env == "development":
                logger.warning(
                    "evolution_not_configured_mock_send",
                    phone_number=phone_number,
                    text=text,
                )
                return
            raise EvolutionError("WhatsApp messaging is not configured")

        url = f"{settings.evolution_api_url.rstrip('/')}/message/sendText/{settings.evolution_instance_name}"
        headers = {
            "apikey": settings.evolution_api_key,
            "Content-Type": "application/json",
        }
        payload = {"number": phone_number, "text": text}

        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(url, json=payload, headers=headers)
                response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            detail = exc.response.text[:300]
            logger.error(
                "evolution_send_failed",
                phone_number=phone_number,
                status_code=exc.response.status_code,
                detail=detail,
            )
            raise EvolutionError(f"Evolution API error: {exc.response.status_code}") from exc
        except httpx.RequestError as exc:
            logger.error("evolution_send_unreachable", phone_number=phone_number, error=str(exc))
            raise EvolutionError("Could not reach Evolution API") from exc

        logger.info("evolution_message_sent", phone_number=phone_number)


evolution_service = EvolutionService()
