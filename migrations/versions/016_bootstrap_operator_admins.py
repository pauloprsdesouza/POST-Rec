"""Promote bootstrap operator accounts (admin role retains researcher access)."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "016_bootstrap_operator_admins"
down_revision: Union[str, None] = "015_user_role"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

BOOTSTRAP_ADMIN_EMAILS = ("paulo.prsdesouza@gmail.com",)


def upgrade() -> None:
    connection = op.get_bind()
    for email in BOOTSTRAP_ADMIN_EMAILS:
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
    connection = op.get_bind()
    for email in BOOTSTRAP_ADMIN_EMAILS:
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
