"""Add archived_at to recommendation_run for soft-dismissed runs."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "014_run_archived_at"
down_revision: Union[str, None] = "013_qualis_normalize_period"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "recommendation_run",
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("idx_recommendation_run_archived_at", "recommendation_run", ["archived_at"])


def downgrade() -> None:
    op.drop_index("idx_recommendation_run_archived_at", table_name="recommendation_run")
    op.drop_column("recommendation_run", "archived_at")
