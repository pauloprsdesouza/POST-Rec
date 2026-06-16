"""Add qualis_journal reference table for CAPES Sucupira classifications."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "011_qualis_journal"
down_revision: Union[str, None] = "010_status_mode_enums"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "qualis_journal",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("issn", sa.Text(), nullable=True),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("title_normalized", sa.Text(), nullable=False),
        sa.Column("area", sa.Text(), nullable=False),
        sa.Column("estrato", sa.Text(), nullable=False),
        sa.CheckConstraint(
            "estrato IN ('A1','A2','A3','A4','B1','B2','B3','B4','C')",
            name="ck_qualis_journal_estrato",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_qualis_journal_issn", "qualis_journal", ["issn"])
    op.create_index("ix_qualis_journal_title_normalized", "qualis_journal", ["title_normalized"])
    op.create_index(
        "ix_qualis_journal_title_issn",
        "qualis_journal",
        ["title_normalized", "issn"],
    )
    op.execute(
        sa.text(
            """
            CREATE UNIQUE INDEX uq_qualis_journal_issn_area
            ON qualis_journal (issn, area)
            WHERE issn IS NOT NULL
            """
        )
    )


def downgrade() -> None:
    op.execute(sa.text("DROP INDEX IF EXISTS uq_qualis_journal_issn_area"))
    op.drop_index("ix_qualis_journal_title_issn", table_name="qualis_journal")
    op.drop_index("ix_qualis_journal_title_normalized", table_name="qualis_journal")
    op.drop_index("ix_qualis_journal_issn", table_name="qualis_journal")
    op.drop_table("qualis_journal")
