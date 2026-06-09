"""Normalize qualis_journal period to qualis_evaluation_period FK."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "013_qualis_normalize_period"
down_revision: Union[str, None] = "012_qualis_journal_period"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

PERIODS = (
    (1, 2017, 2020, "2017-2020"),
    (2, 2021, 2024, "2021-2024"),
)


def upgrade() -> None:
    op.create_table(
        "qualis_evaluation_period",
        sa.Column("id", sa.SmallInteger(), nullable=False),
        sa.Column("start_year", sa.Integer(), nullable=False),
        sa.Column("end_year", sa.Integer(), nullable=False),
        sa.Column("label", sa.Text(), nullable=False),
        sa.CheckConstraint("start_year < end_year", name="ck_qualis_evaluation_period_years"),
        sa.CheckConstraint(
            "start_year >= 1990 AND end_year <= 2100",
            name="ck_qualis_evaluation_period_range",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("start_year", "end_year", name="uq_qualis_evaluation_period_years"),
        sa.UniqueConstraint("label", name="uq_qualis_evaluation_period_label"),
    )

    period_table = sa.table(
        "qualis_evaluation_period",
        sa.column("id", sa.SmallInteger()),
        sa.column("start_year", sa.Integer()),
        sa.column("end_year", sa.Integer()),
        sa.column("label", sa.Text()),
    )
    op.bulk_insert(
        period_table,
        [
            {"id": period_id, "start_year": start, "end_year": end, "label": label}
            for period_id, start, end, label in PERIODS
        ],
    )

    op.add_column(
        "qualis_journal",
        sa.Column("period_id", sa.SmallInteger(), nullable=True),
    )

    op.execute(
        sa.text(
            """
            UPDATE qualis_journal AS qj
            SET period_id = qep.id
            FROM qualis_evaluation_period AS qep
            WHERE qj.period = qep.label
            """
        )
    )

    # Rows with unknown period labels fall back to the most recent known period.
    op.execute(
        sa.text(
            """
            UPDATE qualis_journal
            SET period_id = (SELECT id FROM qualis_evaluation_period ORDER BY start_year DESC LIMIT 1)
            WHERE period_id IS NULL
            """
        )
    )

    op.alter_column("qualis_journal", "period_id", nullable=False)

    op.drop_index("ix_qualis_journal_period", table_name="qualis_journal")
    op.execute(sa.text("DROP INDEX IF EXISTS uq_qualis_journal_issn_area_period"))

    op.create_foreign_key(
        "fk_qualis_journal_period_id",
        "qualis_journal",
        "qualis_evaluation_period",
        ["period_id"],
        ["id"],
        ondelete="RESTRICT",
    )

    op.execute(
        sa.text(
            """
            CREATE UNIQUE INDEX uq_qualis_journal_issn_area_period
            ON qualis_journal (issn, area, period_id)
            WHERE issn IS NOT NULL
            """
        )
    )
    op.create_index("ix_qualis_journal_period_id", "qualis_journal", ["period_id"])
    op.create_index("ix_qualis_journal_issn_period_id", "qualis_journal", ["issn", "period_id"])

    op.drop_column("qualis_journal", "period")


def downgrade() -> None:
    op.add_column(
        "qualis_journal",
        sa.Column("period", sa.Text(), nullable=True),
    )

    op.execute(
        sa.text(
            """
            UPDATE qualis_journal AS qj
            SET period = qep.label
            FROM qualis_evaluation_period AS qep
            WHERE qj.period_id = qep.id
            """
        )
    )

    op.alter_column("qualis_journal", "period", nullable=False)

    op.drop_index("ix_qualis_journal_issn_period_id", table_name="qualis_journal")
    op.drop_index("ix_qualis_journal_period_id", table_name="qualis_journal")
    op.execute(sa.text("DROP INDEX IF EXISTS uq_qualis_journal_issn_area_period"))
    op.drop_constraint("fk_qualis_journal_period_id", "qualis_journal", type_="foreignkey")

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

    op.drop_column("qualis_journal", "period_id")
    op.drop_table("qualis_evaluation_period")
