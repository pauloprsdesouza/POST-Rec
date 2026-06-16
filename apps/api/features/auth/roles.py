"""Role resolution helpers."""

from apps.api.shared.models import User
from apps.api.shared.settings import Settings, get_settings
from packages.postrec_core.domain.enums import UserRole


def parse_bootstrap_admin_emails(settings: Settings | None = None) -> set[str]:
    settings = settings or get_settings()
    raw = settings.admin_bootstrap_emails or ""
    return {email.strip().lower() for email in raw.split(",") if email.strip()}


def resolve_role_for_email(email: str | None, *, settings: Settings | None = None) -> str:
    normalized = (email or "").strip().lower()
    if normalized and normalized in parse_bootstrap_admin_emails(settings):
        return UserRole.ADMIN
    return UserRole.RESEARCHER


def apply_bootstrap_admin_role(user: User, *, settings: Settings | None = None) -> bool:
    """Promote user to admin when email is in bootstrap list. Returns True if role changed."""
    if user.role == UserRole.ADMIN:
        return False
    if (user.email or "").strip().lower() not in parse_bootstrap_admin_emails(settings):
        return False
    user.role = UserRole.ADMIN
    return True


def is_admin(user: User) -> bool:
    return user.role == UserRole.ADMIN


def has_researcher_access(user: User) -> bool:
    """Admins inherit all researcher capabilities (runs, profile, feedback)."""
    return user.role in (UserRole.RESEARCHER, UserRole.ADMIN)
