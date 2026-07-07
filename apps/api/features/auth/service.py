"""Passwordless OTP authentication (email) and JWT tokens."""

import hashlib
import re
import secrets
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from jose import JWTError, jwt
from sqlalchemy.orm import Session

from apps.api.features.auth.email import EmailError, email_service
from apps.api.features.auth.email_templates import render_otp_email
from apps.api.features.auth.evolution import EvolutionError, evolution_service
from apps.api.features.auth.roles import apply_bootstrap_admin_role, resolve_role_for_email
from apps.api.shared.models import AuthOtpChallenge, User, UserResearchProfile
from apps.api.shared.observability.logging import get_logger
from apps.api.shared.settings import get_settings

logger = get_logger("postrec-auth")

ALGORITHM = "HS256"
TOKEN_EXPIRE_HOURS = 72

OtpDeliveryTask = Callable[[], None]
OtpSendResult = tuple[int, str | None, str | None, str | None, OtpDeliveryTask | None]


@dataclass(frozen=True)
class OtpDeliveryRequest:
    email: str
    code: str
    purpose: str
    phone: str | None
    use_whatsapp: bool
    otp_ttl_minutes: int


class AuthError(Exception):
    pass


def normalize_phone(phone: str) -> str:
    """Normalize to E.164 digits (no +). Adds default country code for local BR numbers."""
    settings = get_settings()
    country = re.sub(r"\D", "", settings.phone_default_country_code or "55")
    digits = re.sub(r"\D", "", phone.strip())
    digits = digits.lstrip("0")

    if not digits:
        raise AuthError("Enter a valid phone number with country code (e.g. +557999733237)")

    if len(digits) in (10, 11) and country and not digits.startswith(country):
        digits = country + digits

    if len(digits) < 10 or len(digits) > 15:
        raise AuthError("Enter a valid phone number with country code (e.g. +557999733237)")
    return digits


def normalize_email(email: str) -> str:
    normalized = email.strip().lower()
    if not normalized or "@" not in normalized:
        raise AuthError("Enter a valid email address.")
    return normalized


def mask_email(email: str) -> str:
    local, _, domain = email.partition("@")
    if not domain:
        return email
    masked_local = local[0] + "***" if local else "***"
    return f"{masked_local}@{domain}"


def mask_phone(phone: str) -> str:
    if len(phone) < 4:
        return phone
    return f"***{phone[-4:]}"


class AuthService:
    def _otp_settings(self) -> tuple[int, int, int, int]:
        settings = get_settings()
        return (
            settings.otp_length,
            settings.otp_ttl_minutes,
            settings.otp_resend_seconds,
            settings.otp_max_attempts,
        )

    def _hash_otp(self, email: str, code: str) -> str:
        settings = get_settings()
        material = f"{email}:{code}:{settings.jwt_secret}".encode()
        return hashlib.sha256(material).hexdigest()

    def _generate_otp(self, length: int) -> str:
        upper = 10**length
        return f"{secrets.randbelow(upper):0{length}d}"

    def create_access_token(self, user_id: uuid.UUID) -> str:
        settings = get_settings()
        expire = datetime.now(UTC) + timedelta(hours=TOKEN_EXPIRE_HOURS)
        payload = {"sub": str(user_id), "exp": expire}
        return jwt.encode(payload, settings.jwt_secret, algorithm=ALGORITHM)

    def decode_token(self, token: str) -> uuid.UUID:
        settings = get_settings()
        try:
            payload = jwt.decode(token, settings.jwt_secret, algorithms=[ALGORITHM])
            user_id = payload.get("sub")
            if not user_id:
                raise AuthError("Invalid token")
            return uuid.UUID(str(user_id))
        except (JWTError, ValueError) as exc:
            raise AuthError("Invalid or expired token") from exc

    def _check_rate_limit(self, db: Session, email: str, now: datetime, resend_seconds: int) -> None:
        latest = db.query(AuthOtpChallenge).filter_by(email=email).order_by(AuthOtpChallenge.created_at.desc()).first()
        if latest and latest.created_at:
            created = latest.created_at
            if created.tzinfo is None:
                created = created.replace(tzinfo=UTC)
            if (now - created).total_seconds() < resend_seconds:
                raise AuthError(f"Wait {resend_seconds} seconds before requesting another code")

    def _uses_whatsapp(self, *, whatsapp_opt_in: bool, phone: str | None) -> bool:
        return whatsapp_opt_in and bool(phone and phone.strip())

    def _messaging_configured(self, *, use_whatsapp: bool) -> bool:
        if use_whatsapp:
            return evolution_service.is_configured()
        return email_service.is_configured()

    def _deliver_otp_notification(self, request: OtpDeliveryRequest) -> tuple[str | None, str | None, str | None]:
        settings = get_settings()
        if request.use_whatsapp:
            phone_normalized = normalize_phone(request.phone or "")
            message = (
                f"{settings.app_display_name} sign-in code: {request.code}. "
                f"Valid for {request.otp_ttl_minutes} minutes. Do not share this code."
            )
            try:
                evolution_service.send_text(phone_normalized, message)
            except EvolutionError as exc:
                whatsapp_error = str(exc).strip() or "Could not send WhatsApp message. Try again later."
                if settings.app_env == "development":
                    logger.warning(
                        "otp_whatsapp_fallback",
                        phone_number=phone_normalized,
                        code=request.code,
                        error=whatsapp_error,
                    )
                    return request.code, None, mask_phone(phone_normalized)
                raise AuthError(whatsapp_error) from exc
            return None, None, mask_phone(phone_normalized)

        subject = f"{settings.app_display_name} sign-in code"
        plain_body, html_body = render_otp_email(
            app_name=settings.app_display_name,
            code=request.code,
            ttl_minutes=request.otp_ttl_minutes,
            purpose=request.purpose,
        )
        try:
            email_service.send_text(request.email, subject, plain_body, html_body=html_body)
        except EmailError as exc:
            email_error = str(exc).strip() or "Could not send email. Try again later."
            if settings.app_env == "development":
                logger.warning("otp_email_fallback", email=request.email, code=request.code, error=email_error)
                return request.code, mask_email(request.email), None
            raise AuthError(email_error) from exc

        return None, mask_email(request.email), None

    def _create_otp_challenge(
        self,
        db: Session,
        *,
        email: str,
        purpose: str,
        phone: str | None = None,
        whatsapp_opt_in: bool = False,
    ) -> tuple[int, OtpDeliveryRequest]:
        otp_length, otp_ttl_minutes, resend_seconds, max_attempts = self._otp_settings()
        now = datetime.now(UTC)
        normalized_email = normalize_email(email)
        use_whatsapp = self._uses_whatsapp(whatsapp_opt_in=whatsapp_opt_in, phone=phone)

        self._check_rate_limit(db, normalized_email, now, resend_seconds)

        db.query(AuthOtpChallenge).filter(
            AuthOtpChallenge.email == normalized_email,
            AuthOtpChallenge.consumed_at.is_(None),
        ).update({"consumed_at": now}, synchronize_session=False)

        code = self._generate_otp(otp_length)
        challenge = AuthOtpChallenge(
            email=normalized_email,
            phone_number=normalize_phone(phone) if use_whatsapp else None,
            code_hash=self._hash_otp(normalized_email, code),
            purpose=purpose,
            expires_at=now + timedelta(minutes=otp_ttl_minutes),
            max_attempts=max_attempts,
        )
        db.add(challenge)
        db.commit()

        delivery = OtpDeliveryRequest(
            email=normalized_email,
            code=code,
            purpose=purpose,
            phone=normalize_phone(phone) if use_whatsapp else None,
            use_whatsapp=use_whatsapp,
            otp_ttl_minutes=otp_ttl_minutes,
        )
        return otp_ttl_minutes * 60, delivery

    def _send_otp(
        self,
        db: Session,
        *,
        email: str,
        purpose: str,
        phone: str | None = None,
        whatsapp_opt_in: bool = False,
    ) -> tuple[int, str | None, str | None, str | None]:
        expires_in, delivery = self._create_otp_challenge(
            db,
            email=email,
            purpose=purpose,
            phone=phone,
            whatsapp_opt_in=whatsapp_opt_in,
        )
        dev_code, email_hint, phone_hint = self._deliver_otp_notification(delivery)
        return expires_in, dev_code, email_hint, phone_hint

    def _send_otp_with_delivery(
        self,
        db: Session,
        *,
        email: str,
        purpose: str,
        phone: str | None = None,
        whatsapp_opt_in: bool = False,
    ) -> OtpSendResult:
        settings = get_settings()
        expires_in, delivery = self._create_otp_challenge(
            db,
            email=email,
            purpose=purpose,
            phone=phone,
            whatsapp_opt_in=whatsapp_opt_in,
        )

        if settings.app_env == "development":
            dev_code, email_hint, phone_hint = self._deliver_otp_notification(delivery)
            return expires_in, dev_code, email_hint, phone_hint, None

        if not self._messaging_configured(use_whatsapp=delivery.use_whatsapp):
            raise AuthError("Messaging is not configured. Contact support.")

        def deliver() -> None:
            try:
                self._deliver_otp_notification(delivery)
            except AuthError as exc:
                logger.error("otp_background_delivery_failed", email=delivery.email, error=str(exc))

        if delivery.use_whatsapp:
            return expires_in, None, None, mask_phone(delivery.phone or ""), deliver
        return expires_in, None, mask_email(delivery.email), None, deliver

    def register_and_request_otp(
        self,
        db: Session,
        *,
        full_name: str,
        email: str,
        phone_number: str | None = None,
        whatsapp_opt_in: bool = False,
    ) -> tuple[int, str | None, str | None, str | None]:
        expires_in, dev_code, email_hint, phone_hint, _delivery = self.register_and_request_otp_with_delivery(
            db,
            full_name=full_name,
            email=email,
            phone_number=phone_number,
            whatsapp_opt_in=whatsapp_opt_in,
        )
        return expires_in, dev_code, email_hint, phone_hint

    def register_and_request_otp_with_delivery(
        self,
        db: Session,
        *,
        full_name: str,
        email: str,
        phone_number: str | None = None,
        whatsapp_opt_in: bool = False,
    ) -> OtpSendResult:
        normalized_email = normalize_email(email)
        name = full_name.strip()
        phone: str | None = None

        if not name:
            raise AuthError("Full name is required.")
        if db.query(User).filter_by(email=normalized_email).first():
            raise AuthError("This email is already registered. Sign in instead.")

        if phone_number and phone_number.strip():
            phone = normalize_phone(phone_number)
            if db.query(User).filter_by(phone_number=phone).first():
                raise AuthError("This WhatsApp number is already registered.")

        if whatsapp_opt_in and not phone:
            raise AuthError("Add a WhatsApp number to receive codes and notifications via WhatsApp.")

        user = User(
            full_name=name,
            email=normalized_email,
            phone_number=phone,
            whatsapp_opt_in=whatsapp_opt_in and bool(phone),
            role=resolve_role_for_email(normalized_email),
        )
        db.add(user)
        db.flush()
        db.add(UserResearchProfile(user_id=user.id))
        db.commit()

        return self._send_otp_with_delivery(
            db,
            email=normalized_email,
            purpose="register",
            phone=phone,
            whatsapp_opt_in=user.whatsapp_opt_in,
        )

    def request_login_otp(self, db: Session, *, email: str) -> tuple[int, str | None, str | None, str | None]:
        expires_in, dev_code, email_hint, phone_hint, _delivery = self.request_login_otp_with_delivery(
            db,
            email=email,
        )
        return expires_in, dev_code, email_hint, phone_hint

    def request_login_otp_with_delivery(self, db: Session, *, email: str) -> OtpSendResult:
        normalized_email = normalize_email(email)
        user = db.query(User).filter_by(email=normalized_email).first()
        if not user:
            raise AuthError("No account found for this email. Create an account first.")
        if not user.is_active:
            raise AuthError("Account is disabled.")

        return self._send_otp_with_delivery(
            db,
            email=normalized_email,
            purpose="login",
            phone=user.phone_number,
            whatsapp_opt_in=user.whatsapp_opt_in,
        )

    def verify_otp(self, db: Session, *, email: str, code: str) -> tuple[User, str]:
        normalized_email = normalize_email(email)
        user = db.query(User).filter_by(email=normalized_email).first()
        if not user:
            raise AuthError("Account not found.")
        if not user.is_active:
            raise AuthError("Account is disabled.")

        normalized_code = code.strip()
        now = datetime.now(UTC)

        challenge = (
            db.query(AuthOtpChallenge)
            .filter_by(email=normalized_email)
            .filter(AuthOtpChallenge.consumed_at.is_(None))
            .order_by(AuthOtpChallenge.created_at.desc())
            .first()
        )
        if not challenge:
            raise AuthError("No active code. Request a new one.")

        expires_at = challenge.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=UTC)
        if expires_at < now:
            raise AuthError("Code expired. Request a new one.")
        if challenge.attempts >= challenge.max_attempts:
            raise AuthError("Too many attempts. Request a new code.")

        challenge.attempts += 1
        if self._hash_otp(normalized_email, normalized_code) != challenge.code_hash:
            db.commit()
            raise AuthError("Invalid code.")

        challenge.consumed_at = now
        apply_bootstrap_admin_role(user)
        db.commit()
        db.refresh(user)
        return user, self.create_access_token(user.id)

    def update_account(
        self,
        db: Session,
        user: User,
        *,
        full_name: str | None = None,
        email: str | None = None,
        phone_number: str | None = None,
        whatsapp_opt_in: bool | None = None,
    ) -> User:
        if full_name is not None:
            name = full_name.strip()
            if not name:
                raise AuthError("Full name cannot be empty.")
            user.full_name = name

        if email is not None:
            normalized_email = normalize_email(email)
            existing = db.query(User).filter(User.email == normalized_email, User.id != user.id).first()
            if existing:
                raise AuthError("This email is already used by another account.")
            user.email = normalized_email

        if phone_number is not None:
            stripped = phone_number.strip()
            if stripped:
                phone = normalize_phone(stripped)
                existing = db.query(User).filter(User.phone_number == phone, User.id != user.id).first()
                if existing:
                    raise AuthError("This WhatsApp number is already used by another account.")
                user.phone_number = phone
            else:
                user.phone_number = None
                user.whatsapp_opt_in = False

        if whatsapp_opt_in is not None:
            user.whatsapp_opt_in = whatsapp_opt_in

        if user.whatsapp_opt_in and not user.phone_number:
            raise AuthError("Add a WhatsApp number to receive codes and notifications via WhatsApp.")

        db.commit()
        db.refresh(user)
        return user

    def get_user(self, db: Session, user_id: uuid.UUID) -> User | None:
        user = db.get(User, user_id)
        if user and user.is_active:
            return user
        return None


auth_service = AuthService()
