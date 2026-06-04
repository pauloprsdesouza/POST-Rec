"""Repair indexes/constraints missing despite alembic_version at head."""

from alembic import op

revision = "006_repair_missing_indexes"
down_revision = "005_recommendation_defaults"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "idx_recommendation_run_user_id",
        "recommendation_run",
        ["user_id"],
        unique=False,
        if_not_exists=True,
    )


def downgrade() -> None:
    op.drop_index(
        "idx_recommendation_run_user_id",
        table_name="recommendation_run",
        if_exists=True,
    )
