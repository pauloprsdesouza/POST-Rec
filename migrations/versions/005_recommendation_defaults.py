"""Add recommendation defaults to user research profile."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "005_recommendation_defaults"
down_revision = "004_legacy_embedding_models"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "user_research_profile",
        sa.Column("recommendation_defaults", postgresql.JSONB(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("user_research_profile", "recommendation_defaults")
