"""Add user accounts and persistent research profiles."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "002_user_auth"
down_revision = "001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "app_user",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.Text(), nullable=False, unique=True),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("full_name", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "user_research_profile",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("app_user.id"), unique=True),
        sa.Column("research_area", sa.Text(), nullable=True),
        sa.Column("academic_level", sa.Text(), nullable=True),
        sa.Column("professional_role", sa.Text(), nullable=True),
        sa.Column("experience_with_ai", sa.Text(), nullable=True),
        sa.Column("experience_with_recommender_systems", sa.Text(), nullable=True),
        sa.Column("experience_with_scientific_writing", sa.Text(), nullable=True),
        sa.Column("goal_with_postrec", sa.Text(), nullable=True),
        sa.Column("learned_topics", postgresql.JSONB(), nullable=True),
        sa.Column("avoided_topics", postgresql.JSONB(), nullable=True),
        sa.Column("preferred_techniques", postgresql.JSONB(), nullable=True),
        sa.Column("feedback_notes", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_recommendation_run_user_id", "recommendation_run", ["user_id"])


def downgrade() -> None:
    op.drop_index("idx_recommendation_run_user_id", table_name="recommendation_run")
    op.drop_table("user_research_profile")
    op.drop_table("app_user")
