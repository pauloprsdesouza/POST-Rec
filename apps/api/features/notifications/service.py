"""User notifications via WhatsApp (opt-in) or email (default)."""

from sqlalchemy.orm import Session

from apps.api.features.auth.email import EmailError, email_service
from apps.api.features.auth.evolution import EvolutionError, evolution_service
from apps.api.features.notifications.email_templates import render_run_completed_email, render_run_failed_email
from apps.api.shared.models import RecommendationRun, User
from apps.api.shared.observability.logging import get_logger
from apps.api.shared.settings import get_settings

logger = get_logger("postrec-notifications")


class NotificationService:
    def _load_user(self, db: Session, run: RecommendationRun) -> User | None:
        if not run.user_id:
            return None
        return db.query(User).filter_by(id=run.user_id).first()

    def _should_use_whatsapp(self, user: User) -> bool:
        settings = get_settings()
        return bool(
            settings.whatsapp_notifications_enabled
            and user.phone_number
            and user.whatsapp_opt_in
        )

    def _run_url(self, run_id: str) -> str:
        settings = get_settings()
        base = settings.frontend_app_url.rstrip("/")
        return f"{base}/runs/{run_id}"

    def _runs_url(self) -> str:
        settings = get_settings()
        base = settings.frontend_app_url.rstrip("/")
        return f"{base}/runs"

    def notify_run_completed(
        self,
        db: Session,
        run: RecommendationRun,
        *,
        recommendation_count: int,
    ) -> None:
        user = self._load_user(db, run)
        if not user:
            return

        settings = get_settings()
        topics = run.input.get("topics", []) if run.input else []
        topic_line = ", ".join(topics[:3]) if topics else "your topics"
        if len(topics) > 3:
            topic_line += f" (+{len(topics) - 3} more)"

        if self._should_use_whatsapp(user):
            text = (
                f"{settings.app_display_name}: Your recommendations are ready!\n\n"
                f"{recommendation_count} research ideas generated.\n"
                f"Topics: {topic_line}\n\n"
                f"Open the app to review: {self._run_url(str(run.id))}"
            )
            if self._send_whatsapp(user.phone_number, text, notification_type="run_completed", run_id=str(run.id)):
                return

        if not user.email:
            return

        subject, plain, html = render_run_completed_email(
            app_name=settings.app_display_name,
            recommendation_count=recommendation_count,
            topic_line=topic_line,
            app_url=settings.frontend_app_url.rstrip("/"),
            run_url=self._run_url(str(run.id)),
        )
        self._send_email(user.email, subject, plain, html, notification_type="run_completed", run_id=str(run.id))

    def notify_run_failed(
        self,
        db: Session,
        run: RecommendationRun,
        *,
        error_message: str,
    ) -> None:
        user = self._load_user(db, run)
        if not user:
            return

        settings = get_settings()
        short_error = error_message[:120].strip()

        if self._should_use_whatsapp(user):
            text = (
                f"{settings.app_display_name}: Your recommendation run could not be completed.\n\n"
                f"Reason: {short_error}\n\n"
                f"Open the app to try again: {self._runs_url()}"
            )
            if self._send_whatsapp(user.phone_number, text, notification_type="run_failed", run_id=str(run.id)):
                return

        if not user.email:
            return

        subject, plain, html = render_run_failed_email(
            app_name=settings.app_display_name,
            error_message=short_error,
            app_url=settings.frontend_app_url.rstrip("/"),
            runs_url=self._runs_url(),
        )
        self._send_email(user.email, subject, plain, html, notification_type="run_failed", run_id=str(run.id))

    def _send_whatsapp(self, phone_number: str, text: str, *, notification_type: str, run_id: str) -> bool:
        try:
            evolution_service.send_text(phone_number, text)
            logger.info(
                "whatsapp_notification_sent",
                notification_type=notification_type,
                run_id=run_id,
            )
            return True
        except EvolutionError as exc:
            logger.warning(
                "whatsapp_notification_failed",
                notification_type=notification_type,
                run_id=run_id,
                error=str(exc),
            )
            return False

    def _send_email(
        self,
        to_email: str,
        subject: str,
        plain: str,
        html: str,
        *,
        notification_type: str,
        run_id: str,
    ) -> None:
        settings = get_settings()
        try:
            email_service.send_text(to_email, subject, plain, html_body=html)
            logger.info(
                "email_notification_sent",
                notification_type=notification_type,
                run_id=run_id,
                to_email=to_email,
            )
        except EmailError as exc:
            if settings.app_env == "development" or not email_service.is_configured():
                logger.warning(
                    "email_notification_mock",
                    notification_type=notification_type,
                    run_id=run_id,
                    to_email=to_email,
                    subject=subject,
                    body=plain,
                    error=str(exc),
                )
                return
            logger.warning(
                "email_notification_failed",
                notification_type=notification_type,
                run_id=run_id,
                to_email=to_email,
                error=str(exc),
            )


notification_service = NotificationService()
