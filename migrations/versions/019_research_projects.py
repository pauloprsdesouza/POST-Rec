"""Research project roadmap tables."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "019_research_projects"
down_revision = "018_performance_indexes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "research_project",
        sa.Column("id", UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("app_user.id", ondelete="CASCADE"), nullable=False),
        sa.Column("run_id", UUID(as_uuid=True), sa.ForeignKey("recommendation_run.id", ondelete="CASCADE"), nullable=False),
        sa.Column(
            "recommendation_id",
            UUID(as_uuid=True),
            sa.ForeignKey("recommendation_candidate.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False, server_default="active"),
        sa.Column("progress_pct", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("current_phase_id", UUID(as_uuid=True), nullable=True),
        sa.Column("roadmap_version", sa.Text(), nullable=False, server_default="v1"),
        sa.Column("locale", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "recommendation_id", name="uq_research_project_user_recommendation"),
    )
    op.create_index("idx_research_project_user_id", "research_project", ["user_id"])
    op.create_index("idx_research_project_run_id", "research_project", ["run_id"])
    op.create_index("idx_research_project_recommendation_id", "research_project", ["recommendation_id"])

    op.create_table(
        "project_phase",
        sa.Column("id", UUID(as_uuid=True), nullable=False),
        sa.Column(
            "project_id",
            UUID(as_uuid=True),
            sa.ForeignKey("research_project.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("order_index", sa.Integer(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.Text(), nullable=False, server_default="todo"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_project_phase_project_id", "project_phase", ["project_id"])

    op.create_table(
        "project_task",
        sa.Column("id", UUID(as_uuid=True), nullable=False),
        sa.Column(
            "phase_id",
            UUID(as_uuid=True),
            sa.ForeignKey("project_phase.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("order_index", sa.Integer(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("guidance", sa.Text(), nullable=True),
        sa.Column("effort", sa.Text(), nullable=True),
        sa.Column("linked_fields", JSONB(), nullable=True),
        sa.Column("linked_paper_ids", JSONB(), nullable=True),
        sa.Column("checklist", JSONB(), nullable=True),
        sa.Column("status", sa.Text(), nullable=False, server_default="todo"),
        sa.Column("user_notes", sa.Text(), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_project_task_phase_id", "project_task", ["phase_id"])

    op.create_foreign_key(
        "fk_research_project_current_phase",
        "research_project",
        "project_phase",
        ["current_phase_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_research_project_current_phase", "research_project", type_="foreignkey")
    op.drop_index("idx_project_task_phase_id", table_name="project_task")
    op.drop_table("project_task")
    op.drop_index("idx_project_phase_project_id", table_name="project_phase")
    op.drop_table("project_phase")
    op.drop_index("idx_research_project_recommendation_id", table_name="research_project")
    op.drop_index("idx_research_project_run_id", table_name="research_project")
    op.drop_index("idx_research_project_user_id", table_name="research_project")
    op.drop_table("research_project")
