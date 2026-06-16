"""Add application role to app_user (researcher default, admin for operators)."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "015_user_role"
down_revision: Union[str, None] = "014_run_archived_at"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "app_user",
        sa.Column("role", sa.Text(), nullable=False, server_default="researcher"),
    )
    op.create_check_constraint(
        "ck_app_user_role",
        "app_user",
        "role IN ('researcher', 'admin')",
    )
    op.create_index("idx_app_user_role", "app_user", ["role"])
    op.alter_column("app_user", "role", server_default=None)


def downgrade() -> None:
    op.drop_index("idx_app_user_role", table_name="app_user")
    op.drop_constraint("ck_app_user_role", "app_user", type_="check")
    op.drop_column("app_user", "role")
