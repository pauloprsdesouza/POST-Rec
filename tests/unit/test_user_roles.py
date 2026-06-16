"""Tests for application role resolution."""

from apps.api.features.auth.roles import (
    apply_bootstrap_admin_role,
    parse_bootstrap_admin_emails,
    resolve_role_for_email,
)
from apps.api.shared.settings import Settings
from packages.postrec_core.domain.enums import UserRole


class _UserStub:
    def __init__(self, *, email: str, role: str = UserRole.RESEARCHER):
        self.email = email
        self.role = role


def test_resolve_role_defaults_to_researcher():
    assert (
        resolve_role_for_email("user@example.com", settings=Settings(admin_bootstrap_emails="")) == UserRole.RESEARCHER
    )


def test_has_researcher_access_includes_admin():
    from apps.api.features.auth.roles import has_researcher_access

    assert has_researcher_access(_UserStub(email="a@b.com", role=UserRole.RESEARCHER)) is True
    assert has_researcher_access(_UserStub(email="ops@postrec.dev", role=UserRole.ADMIN)) is True


def test_resolve_role_promotes_paulo_bootstrap_email():
    settings = Settings(admin_bootstrap_emails="paulo.prsdesouza@gmail.com")
    assert resolve_role_for_email("paulo.prsdesouza@gmail.com", settings=settings) == UserRole.ADMIN


def test_apply_bootstrap_admin_role_updates_user():
    user = _UserStub(email="ops@postrec.dev")
    settings = Settings(admin_bootstrap_emails="ops@postrec.dev")
    assert apply_bootstrap_admin_role(user, settings=settings) is True
    assert user.role == UserRole.ADMIN


def test_parse_bootstrap_admin_emails_normalizes():
    settings = Settings(admin_bootstrap_emails=" A@x.com , b@x.com, ")
    assert parse_bootstrap_admin_emails(settings) == {"a@x.com", "b@x.com"}
