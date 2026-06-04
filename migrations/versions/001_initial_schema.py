"""Initial schema migration."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector

revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "volunteer_session",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("ip_hash", sa.Text(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "participant_consent",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.Text(), nullable=False),
        sa.Column("session_id", sa.UUID(), nullable=False),
        sa.Column("consent_version", sa.Text(), nullable=False),
        sa.Column("accepted", sa.Boolean(), nullable=False),
        sa.Column("accepted_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(["session_id"], ["volunteer_session.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "recommendation_run",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("request_id", sa.Text(), nullable=True),
        sa.Column("user_id", sa.Text(), nullable=True),
        sa.Column("session_id", sa.UUID(), nullable=True),
        sa.Column("expectation_id", sa.UUID(), nullable=True),
        sa.Column("input", sa.JSON(), nullable=False),
        sa.Column("mode", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("progress", sa.Integer(), nullable=False),
        sa.Column("current_step", sa.Text(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("max_papers", sa.Integer(), nullable=False),
        sa.Column("max_recommendations", sa.Integer(), nullable=False),
        sa.Column("trace_id", sa.Text(), nullable=True),
        sa.Column("estimated_cost_usd", sa.Numeric(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("request_id"),
    )


def downgrade() -> None:
    op.drop_table("recommendation_run")
    op.drop_table("participant_consent")
    op.drop_table("volunteer_session")
