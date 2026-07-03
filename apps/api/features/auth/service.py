"""Passwordless WhatsApp OTP authentication and JWT tokens."""

import hashlib
import re
import secrets
import uuid
from datetime import UTC, datetime, timedelta

from jose import JWTError, jwt
from sqlalchemy.orm import Session

from apps.api.features.auth.evolution import EvolutionError, evolution_service
from apps.api.features.auth.roles import apply_bootstrap_admin_role, resolve_role_for_email
from apps.api.shared.models import AuthOtpChallenge, User, UserResearchProfile
from apps.api.shared.observability.logging import get_logger
from apps.api.shared.settings import get_settings

logger = get_logger("postrec-auth")

ALGORITHM = "HS256"
TOKEN_EXPIRE_HOURS = 72


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

    # Local numbers without country code (common BR: 10–11 digits).
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

    def _hash_otp(self, phone: str, code: str) -> str:
        settings = get_settings()
        material = f"{phone}:{code}:{settings.jwt_secret}".encode()
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

    def _check_rate_limit(self, db: Session, phone: str, now: datetime, resend_seconds: int) -> None:
        latest = (
            db.query(AuthOtpChallenge)
            .filter_by(phone_number=phone)
            .order_by(AuthOtpChallenge.created_at.desc())
            .first()
        )
        if latest and latest.created_at:
            created = latest.created_at
            if created.tzinfo is None:
                created = created.replace(tzinfo=UTC)
            if (now - created).total_seconds() < resend_seconds:
                raise AuthError(f"Wait {resend_seconds} seconds before requesting another code")

    def _send_otp_to_phone(
        self,
        db: Session,
        *,
        phone: str,
        purpose: str,
    ) -> tuple[int, str | None, str]:
        settings = get_settings()
        otp_length, otp_ttl_minutes, resend_seconds, max_attempts = self._otp_settings()
        now = datetime.now(UTC)

        self._check_rate_limit(db, phone, now, resend_seconds)

        db.query(AuthOtpChallenge).filter(
            AuthOtpChallenge.phone_number == phone,
            AuthOtpChallenge.consumed_at.is_(None),
        ).update({"consumed_at": now}, synchronize_session=False)

        code = self._generate_otp(otp_length)
        challenge = AuthOtpChallenge(
            phone_number=phone,
            code_hash=self._hash_otp(phone, code),
            purpose=purpose,
            expires_at=now + timedelta(minutes=otp_ttl_minutes),
            max_attempts=max_attempts,
        )
        db.add(challenge)
        db.commit()

        message = (
            f"{settings.app_display_name} sign-in code: {code}. "
            f"Valid for {otp_ttl_minutes} minutes. Do not share this code."
        )
        dev_code: str | None = None
        try:
            evolution_service.send_text(phone, message)
        except EvolutionError as exc:
            if settings.app_env == "development" or not evolution_service.is_configured():
                dev_code = code
                logger.warning("otp_whatsapp_fallback", phone_number=phone, code=code, error=str(exc))
            else:
                message = str(exc).strip() or "Could not send WhatsApp message. Try again later."
                raise AuthError(message) from exc

        return otp_ttl_minutes * 60, dev_code, mask_phone(phone)

    def register_and_request_otp(
        self,
        db: Session,
        *,
        full_name: str,
        email: str,
        phone_number: str,
        whatsapp_opt_in: bool = True,
    ) -> tuple[int, str | None, str]:
        normalized_email = normalize_email(email)
        phone = normalize_phone(phone_number)
        name = full_name.strip()

        if not name:
            raise AuthError("Full name is required.")
        if db.query(User).filter_by(email=normalized_email).first():
            raise AuthError("This email is already registered. Sign in instead.")
        if db.query(User).filter_by(phone_number=phone).first():
            raise AuthError("This WhatsApp number is already registered.")

        user = User(
            full_name=name,
            email=normalized_email,
            phone_number=phone,
            whatsapp_opt_in=whatsapp_opt_in,
            role=resolve_role_for_email(normalized_email),
        )
        db.add(user)
        db.flush()
        db.add(UserResearchProfile(user_id=user.id))
        db.commit()

        if not whatsapp_opt_in:
            raise AuthError("WhatsApp is required to receive your verification code.")

        expires_in, dev_code, phone_hint = self._send_otp_to_phone(db, phone=phone, purpose="register")
        return expires_in, dev_code, phone_hint

    def request_login_otp(self, db: Session, *, email: str) -> tuple[int, str | None, str]:
        normalized_email = normalize_email(email)
        user = db.query(User).filter_by(email=normalized_email).first()
        if not user:
            raise AuthError("No account found for this email. Create an account first.")
        if not user.is_active:
            raise AuthError("Account is disabled.")
        if not user.phone_number:
            raise AuthError("Add a WhatsApp number in your profile to receive sign-in codes.")
        if not user.whatsapp_opt_in:
            raise AuthError("WhatsApp notifications are disabled. Enable them in your profile to sign in.")

        return self._send_otp_to_phone(db, phone=normalize_phone(user.phone_number), purpose="login")

    def verify_otp(self, db: Session, *, email: str, code: str) -> tuple[User, str]:
        normalized_email = normalize_email(email)
        user = db.query(User).filter_by(email=normalized_email).first()
        if not user or not user.phone_number:
            raise AuthError("Account not found.")
        if not user.is_active:
            raise AuthError("Account is disabled.")

        phone = normalize_phone(user.phone_number)
        normalized_code = code.strip()
        now = datetime.now(UTC)

        challenge = (
            db.query(AuthOtpChallenge)
            .filter_by(phone_number=phone)
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
        if self._hash_otp(phone, normalized_code) != challenge.code_hash:
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
            phone = normalize_phone(phone_number)
            existing = db.query(User).filter(User.phone_number == phone, User.id != user.id).first()
            if existing:
                raise AuthError("This WhatsApp number is already used by another account.")
            user.phone_number = phone

        if whatsapp_opt_in is not None:
            user.whatsapp_opt_in = whatsapp_opt_in

        db.commit()
        db.refresh(user)
        return user

    def get_user(self, db: Session, user_id: uuid.UUID) -> User | None:
        return db.query(User).filter_by(id=user_id, is_active=True).first()


auth_service = AuthService()
