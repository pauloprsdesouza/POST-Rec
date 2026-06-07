"""User notifications (WhatsApp via Evolution API)."""

import uuid

from sqlalchemy.orm import Session

from apps.api.shared.models import RecommendationRun, User
from apps.api.shared.observability.logging import get_logger
from apps.api.features.auth.evolution import EvolutionError, evolution_service
from apps.api.shared.settings import get_settings

logger = get_logger("postrec-notifications")


class NotificationService:
    def notify_run_completed(
        self,
        db: Session,
        run: RecommendationRun,
        *,
        recommendation_count: int,
    ) -> None:
        settings = get_settings()
        if not settings.whatsapp_notifications_enabled:
            return
        if not run.user_id:
            return

        user = db.query(User).filter_by(id=run.user_id).first()
        if not user or not user.phone_number or not user.whatsapp_opt_in:
            return

        topics = run.input.get("topics", []) if run.input else []
        topic_line = ", ".join(topics[:3]) if topics else "your topics"
        if len(topics) > 3:
            topic_line += f" (+{len(topics) - 3} more)"

        text = (
            "POST-Rec: Your recommendations are ready!\n\n"
            f"{recommendation_count} research ideas generated.\n"
            f"Topics: {topic_line}\n\n"
            f"Open the app to review: {settings.frontend_app_url}"
        )
        self._send(user.phone_number, text, notification_type="run_completed", run_id=str(run.id))

    def notify_run_failed(
        self,
        db: Session,
        run: RecommendationRun,
        *,
        error_message: str,
    ) -> None:
        settings = get_settings()
        if not settings.whatsapp_notifications_enabled:
            return
        if not run.user_id:
            return

        user = db.query(User).filter_by(id=run.user_id).first()
        if not user or not user.phone_number or not user.whatsapp_opt_in:
            return

        short_error = error_message[:120].strip()
        text = (
            "POST-Rec: Your recommendation run could not be completed.\n\n"
            f"Reason: {short_error}\n\n"
            f"Open the app to try again: {settings.frontend_app_url}"
        )
        self._send(user.phone_number, text, notification_type="run_failed", run_id=str(run.id))

    def _send(self, phone_number: str, text: str, *, notification_type: str, run_id: str) -> None:
        try:
            evolution_service.send_text(phone_number, text)
            logger.info(
                "whatsapp_notification_sent",
                notification_type=notification_type,
                run_id=run_id,
            )
        except EvolutionError as exc:
            logger.warning(
                "whatsapp_notification_failed",
                notification_type=notification_type,
                run_id=run_id,
                error=str(exc),
            )


notification_service = NotificationService()
