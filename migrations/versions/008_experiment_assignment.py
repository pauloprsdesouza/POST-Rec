"""Add blind A/B experiment assignment fields to recommendation_run."""

from alembic import op
import sqlalchemy as sa

revision = "008_experiment_assignment"
down_revision = "007_drop_phone_uq"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("recommendation_run", sa.Column("experiment_id", sa.Text(), nullable=True))
    op.add_column("recommendation_run", sa.Column("experiment_variant", sa.Text(), nullable=True))
    op.add_column("recommendation_run", sa.Column("assigned_mode", sa.Text(), nullable=True))
    op.add_column(
        "recommendation_run",
        sa.Column("presentation_profile", sa.Text(), nullable=False, server_default="standard"),
    )
    op.create_index(
        "idx_recommendation_run_experiment",
        "recommendation_run",
        ["experiment_id", "experiment_variant"],
    )


def downgrade() -> None:
    op.drop_index("idx_recommendation_run_experiment", table_name="recommendation_run")
    op.drop_column("recommendation_run", "presentation_profile")
    op.drop_column("recommendation_run", "assigned_mode")
    op.drop_column("recommendation_run", "experiment_variant")
    op.drop_column("recommendation_run", "experiment_id")
