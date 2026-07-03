"""Promote bootstrap operator accounts (admin role retains researcher access)."""

import os
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "016_bootstrap_operator_admins"
down_revision: Union[str, None] = "015_user_role"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _bootstrap_admin_emails() -> tuple[str, ...]:
    raw = os.environ.get("ADMIN_BOOTSTRAP_EMAILS", "").strip()
    if not raw:
        return ()
    return tuple(email.strip() for email in raw.split(",") if email.strip())


def upgrade() -> None:
    emails = _bootstrap_admin_emails()
    if not emails:
        return

    connection = op.get_bind()
    for email in emails:
        connection.execute(
            sa.text(
                """
                UPDATE app_user
                SET role = 'admin'
                WHERE lower(email) = lower(:email)
                """
            ),
            {"email": email},
        )


def downgrade() -> None:
    emails = _bootstrap_admin_emails()
    if not emails:
        return

    connection = op.get_bind()
    for email in emails:
        connection.execute(
            sa.text(
                """
                UPDATE app_user
                SET role = 'researcher'
                WHERE lower(email) = lower(:email)
                  AND role = 'admin'
                """
            ),
            {"email": email},
        )
