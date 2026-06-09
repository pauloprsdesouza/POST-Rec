"""Add evaluation period column to qualis_journal."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "012_qualis_journal_period"
down_revision: Union[str, None] = "011_qualis_journal"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

DEFAULT_PERIOD = "2021-2024"


def upgrade() -> None:
    op.add_column(
        "qualis_journal",
        sa.Column("period", sa.Text(), nullable=False, server_default=DEFAULT_PERIOD),
    )
    op.alter_column("qualis_journal", "period", server_default=None)

    op.execute(sa.text("DROP INDEX IF EXISTS uq_qualis_journal_issn_area"))
    op.execute(
        sa.text(
            """
            CREATE UNIQUE INDEX uq_qualis_journal_issn_area_period
            ON qualis_journal (issn, area, period)
            WHERE issn IS NOT NULL
            """
        )
    )
    op.create_index("ix_qualis_journal_period", "qualis_journal", ["period"])


def downgrade() -> None:
    op.drop_index("ix_qualis_journal_period", table_name="qualis_journal")
    op.execute(sa.text("DROP INDEX IF EXISTS uq_qualis_journal_issn_area_period"))
    op.execute(
        sa.text(
            """
            CREATE UNIQUE INDEX uq_qualis_journal_issn_area
            ON qualis_journal (issn, area)
            WHERE issn IS NOT NULL
            """
        )
    )
    op.drop_column("qualis_journal", "period")
