"""Add indexes for hot query patterns."""

from alembic import op

revision = "018_performance_indexes"
down_revision = "017_otp_email_challenges"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "idx_recommendation_run_event_run_type",
        "recommendation_run_event",
        ["run_id", "event_type"],
        unique=False,
        if_not_exists=True,
    )
    op.create_index(
        "idx_recommendation_run_event_run_id",
        "recommendation_run_event",
        ["run_id"],
        unique=False,
        if_not_exists=True,
    )
    op.create_index(
        "idx_recommendation_candidate_run_status",
        "recommendation_candidate",
        ["run_id", "status"],
        unique=False,
        if_not_exists=True,
    )
    op.create_index(
        "idx_recommendation_feedback_user_run",
        "recommendation_feedback",
        ["user_id", "run_id"],
        unique=False,
        if_not_exists=True,
    )
    op.create_index(
        "idx_session_consent_user_accepted",
        "session_consent",
        ["user_id", "accepted", "accepted_at"],
        unique=False,
        if_not_exists=True,
    )
    op.create_index(
        "idx_recommendation_run_user_active",
        "recommendation_run",
        ["user_id", "archived_at", "created_at"],
        unique=False,
        if_not_exists=True,
    )
    op.create_index(
        "idx_document_embedding_document_id",
        "document_embedding",
        ["document_id"],
        unique=False,
        if_not_exists=True,
    )


def downgrade() -> None:
    op.drop_index("idx_document_embedding_document_id", table_name="document_embedding", if_exists=True)
    op.drop_index("idx_recommendation_run_user_active", table_name="recommendation_run", if_exists=True)
    op.drop_index("idx_session_consent_user_accepted", table_name="session_consent", if_exists=True)
    op.drop_index("idx_recommendation_feedback_user_run", table_name="recommendation_feedback", if_exists=True)
    op.drop_index("idx_recommendation_candidate_run_status", table_name="recommendation_candidate", if_exists=True)
    op.drop_index("idx_recommendation_run_event_run_id", table_name="recommendation_run_event", if_exists=True)
    op.drop_index("idx_recommendation_run_event_run_type", table_name="recommendation_run_event", if_exists=True)
