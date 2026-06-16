"""Add PostgreSQL ENUM types for status and mode columns."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import ENUM

revision: str = "010_status_mode_enums"
down_revision: Union[str, None] = "009_schema_standardization"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

RUN_STATUS_VALUES = (
    "queued",
    "started",
    "searching_papers",
    "normalizing_documents",
    "deduplicating_documents",
    "generating_embeddings",
    "ranking_candidates",
    "generating_recommendations",
    "validating_output",
    "completed",
    "failed",
    "cancelled",
    "cost_limit_exceeded",
    "failed_schema_validation",
)

RUN_MODE_VALUES = ("quick", "sota", "exploratory", "fggv")

SESSION_STATUS_VALUES = ("started", "in_progress", "completed", "abandoned")

CANDIDATE_STATUS_VALUES = ("draft", "published", "needs_refinement")


def _create_enum(name: str, values: tuple[str, ...]) -> None:
    enum_type = ENUM(*values, name=name, create_type=False)
    enum_type.create(op.get_bind(), checkfirst=True)


def _case_cast(column: str, enum_name: str, values: tuple[str, ...], default: str) -> str:
    whens = "\n".join(
        f"WHEN {column}::text = '{value}' THEN '{value}'::{enum_name}" for value in values
    )
    return f"CASE {whens} ELSE '{default}'::{enum_name} END"


def _alter_to_enum(
    table: str,
    column: str,
    enum_name: str,
    values: tuple[str, ...],
    *,
    nullable: bool,
    default: str | None = None,
) -> None:
    op.execute(sa.text(f"ALTER TABLE {table} ALTER COLUMN {column} DROP DEFAULT"))
    using = _case_cast(column, enum_name, values, default or values[0])
    op.execute(sa.text(f"ALTER TABLE {table} ALTER COLUMN {column} TYPE {enum_name} USING ({using})"))
    if default is not None:
        op.alter_column(
            table,
            column,
            nullable=nullable,
            server_default=sa.text(f"'{default}'::{enum_name}"),
        )
    else:
        op.alter_column(table, column, nullable=nullable)


def upgrade() -> None:
    _create_enum("run_status", RUN_STATUS_VALUES)
    _create_enum("run_mode", RUN_MODE_VALUES)
    _create_enum("session_status", SESSION_STATUS_VALUES)
    _create_enum("candidate_status", CANDIDATE_STATUS_VALUES)

    _alter_to_enum(
        "recommendation_run",
        "status",
        "run_status",
        RUN_STATUS_VALUES,
        nullable=False,
        default="queued",
    )
    _alter_to_enum(
        "recommendation_run",
        "mode",
        "run_mode",
        RUN_MODE_VALUES,
        nullable=False,
        default="quick",
    )
    op.execute(
        sa.text(
            f"""
            ALTER TABLE recommendation_run
            ALTER COLUMN current_step
            TYPE run_status
            USING (
                CASE
                    WHEN current_step IS NULL THEN NULL
                    ELSE {_case_cast("current_step", "run_status", RUN_STATUS_VALUES, "queued")}
                END
            )
            """
        )
    )

    _alter_to_enum(
        "study_session",
        "status",
        "session_status",
        SESSION_STATUS_VALUES,
        nullable=False,
        default="started",
    )
    _alter_to_enum(
        "recommendation_candidate",
        "status",
        "candidate_status",
        CANDIDATE_STATUS_VALUES,
        nullable=False,
        default="draft",
    )


def downgrade() -> None:
    op.alter_column("recommendation_candidate", "status", type_=sa.Text(), postgresql_using="status::text")
    op.alter_column("study_session", "status", type_=sa.Text(), postgresql_using="status::text")
    op.alter_column("recommendation_run", "current_step", type_=sa.Text(), postgresql_using="current_step::text")
    op.alter_column("recommendation_run", "mode", type_=sa.Text(), postgresql_using="mode::text")
    op.alter_column("recommendation_run", "status", type_=sa.Text(), postgresql_using="status::text")

    for name in ("candidate_status", "session_status", "run_mode", "run_status"):
        op.execute(sa.text(f"DROP TYPE IF EXISTS {name}"))
