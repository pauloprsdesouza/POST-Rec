"""Transactional email via SMTP."""

import smtplib
from email.message import EmailMessage

from apps.api.shared.observability.logging import get_logger
from apps.api.shared.settings import get_settings

logger = get_logger("postrec-email")


class EmailError(Exception):
    pass


class EmailService:
    def is_configured(self) -> bool:
        settings = get_settings()
        return bool(settings.smtp_host.strip() and settings.email_from.strip())

    def send_text(self, to_email: str, subject: str, body: str, *, html_body: str | None = None) -> None:
        settings = get_settings()
        if not self.is_configured():
            if settings.app_env == "development":
                logger.warning(
                    "email_not_configured_mock_send",
                    to_email=to_email,
                    subject=subject,
                    body=body,
                    has_html=bool(html_body),
                )
                return
            raise EmailError("Email is not configured")

        from_name = settings.email_from_name.strip() or settings.app_display_name
        from_addr = settings.email_from.strip()

        message = EmailMessage()
        message["Subject"] = subject
        message["From"] = f"{from_name} <{from_addr}>"
        message["To"] = to_email
        message.set_content(body)
        if html_body:
            message.add_alternative(html_body, subtype="html")

        self._deliver(message, to_email=to_email, subject=subject)

    def _deliver(self, message: EmailMessage, *, to_email: str, subject: str) -> None:
        settings = get_settings()
        try:
            if settings.smtp_port == 465:
                with smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port, timeout=30) as server:
                    if settings.smtp_user:
                        server.login(settings.smtp_user, settings.smtp_password)
                    server.send_message(message)
            else:
                with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=30) as server:
                    if settings.smtp_use_tls:
                        server.starttls()
                    if settings.smtp_user:
                        server.login(settings.smtp_user, settings.smtp_password)
                    server.send_message(message)
        except smtplib.SMTPException as exc:
            logger.error("email_send_failed", to_email=to_email, error=str(exc))
            raise EmailError("Could not send email. Try again later.") from exc
        except OSError as exc:
            logger.error("email_send_unreachable", to_email=to_email, error=str(exc))
            raise EmailError("Could not reach mail server") from exc

        logger.info("email_sent", to_email=to_email, subject=subject)


email_service = EmailService()
