"""WhatsApp messaging via Evolution API."""

import httpx

from apps.api.shared.observability.logging import get_logger
from apps.api.shared.settings import get_settings

logger = get_logger("postrec-evolution")


class EvolutionError(Exception):
    pass


class EvolutionService:
    def is_configured(self) -> bool:
        settings = get_settings()
        return bool(settings.evolution_api_url and settings.evolution_api_key and settings.evolution_instance_name)

    def resolve_jid(self, phone_number: str) -> str | None:
        """Resolve the canonical WhatsApp JID for a phone number.

        Evolution's own number sanitization is unreliable for Brazilian mobiles
        (the "nono dígito" problem): on first contact with a raw 13-digit number
        it may target a non-existent JID and the message is accepted (PENDING)
        but never delivered. Asking Evolution to validate the number first and
        sending to the exact JID it returns bypasses that faulty sanitization.

        Returns the JID when the number exists on WhatsApp, or ``None`` when the
        check itself could not be completed (network/endpoint error) so callers
        can fall back to sending the raw number. Raises :class:`EvolutionError`
        when Evolution confirms the number is not a WhatsApp account.
        """
        settings = get_settings()
        url = f"{settings.evolution_api_url.rstrip('/')}/chat/whatsappNumbers/{settings.evolution_instance_name}"
        headers = {
            "apikey": settings.evolution_api_key,
            "Content-Type": "application/json",
        }
        try:
            with httpx.Client(timeout=15.0) as client:
                response = client.post(url, json={"numbers": [phone_number]}, headers=headers)
                response.raise_for_status()
                data = response.json() if response.content else []
        except (httpx.HTTPError, ValueError) as exc:
            logger.warning("evolution_number_check_failed", phone_number=phone_number, error=str(exc))
            return None

        entry = data[0] if isinstance(data, list) and data and isinstance(data[0], dict) else None
        if entry is None:
            return None
        if entry.get("exists") is False:
            raise EvolutionError(
                "WhatsApp number not found. Include country code (e.g. +55 79 99973-3237)."
            )
        jid = entry.get("jid")
        return str(jid) if jid else None

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

        recipient = self.resolve_jid(phone_number) or phone_number

        url = f"{settings.evolution_api_url.rstrip('/')}/message/sendText/{settings.evolution_instance_name}"
        headers = {
            "apikey": settings.evolution_api_key,
            "Content-Type": "application/json",
        }
        payload = {"number": recipient, "text": text}

        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                body = response.json() if response.content else {}
                if isinstance(body, dict) and body.get("status") is False:
                    message = body.get("message") or body.get("error") or "send rejected"
                    raise EvolutionError(str(message))
        except httpx.HTTPStatusError as exc:
            detail = exc.response.text[:300]
            logger.error(
                "evolution_send_failed",
                phone_number=phone_number,
                status_code=exc.response.status_code,
                detail=detail,
            )
            if exc.response.status_code == 400 and "exists" in detail.lower():
                raise EvolutionError(
                    "WhatsApp number not found. Include country code (e.g. +55 79 99973-3237)."
                ) from exc
            raise EvolutionError(f"Evolution API error: {exc.response.status_code}") from exc
        except httpx.RequestError as exc:
            logger.error("evolution_send_unreachable", phone_number=phone_number, error=str(exc))
            raise EvolutionError("Could not reach Evolution API") from exc

        logger.info("evolution_message_sent", phone_number=phone_number, recipient=recipient)


evolution_service = EvolutionService()
