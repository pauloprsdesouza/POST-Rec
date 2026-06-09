"""Standardize schema: rename session tables, UUID user FKs, drop unused columns/tables."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector
from sqlalchemy import inspect
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "009_schema_standardization"
down_revision: Union[str, None] = "008_experiment_assignment"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_UUID_RE = r"^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"


def _tables() -> set[str]:
    return set(inspect(op.get_bind()).get_table_names())


def _columns(table: str) -> set[str]:
    if table not in _tables():
        return set()
    return {col["name"] for col in inspect(op.get_bind()).get_columns(table)}


def _rename_table(old: str, new: str) -> None:
    tables = _tables()
    if old in tables and new not in tables:
        op.rename_table(old, new)


def _drop_table_if_exists(name: str) -> None:
    if name in _tables():
        op.drop_table(name)


def _drop_column_if_exists(table: str, column: str) -> None:
    if column in _columns(table):
        op.drop_column(table, column)


def _drop_index_if_exists(name: str, table: str) -> None:
    indexes = {idx["name"] for idx in inspect(op.get_bind()).get_indexes(table)} if table in _tables() else set()
    if name in indexes:
        op.drop_index(name, table_name=table)


def _migrate_text_user_id_to_uuid(table: str, *, nullable: bool = True) -> None:
    if table not in _tables() or "user_id" not in _columns(table):
        return

    col_type = next(
        col["type"] for col in inspect(op.get_bind()).get_columns(table) if col["name"] == "user_id"
    )
    if isinstance(col_type, UUID):
        return

    temp = f"{table}_user_id_uuid"
    op.add_column(table, sa.Column(temp, UUID(as_uuid=True), nullable=True))
    op.execute(
        sa.text(
            f"""
            UPDATE {table}
            SET {temp} = user_id::uuid
            WHERE user_id IS NOT NULL
              AND user_id ~ :pattern
            """
        ).bindparams(pattern=_UUID_RE)
    )
    op.drop_column(table, "user_id")
    op.alter_column(table, temp, new_column_name="user_id", nullable=nullable)
    op.create_foreign_key(
        f"fk_{table}_user_id",
        table,
        "app_user",
        ["user_id"],
        ["id"],
        ondelete="SET NULL",
    )


def upgrade() -> None:
    for dead in ("user_interaction_event", "exported_artifact", "audit_log"):
        _drop_table_if_exists(dead)

    _rename_table("volunteer_session", "study_session")
    _rename_table("participant_consent", "session_consent")
    _rename_table("participant_profile", "session_profile")
    _rename_table("user_expectation", "session_expectation")

    _drop_index_if_exists("idx_volunteer_session_user_id", "study_session")
    _drop_index_if_exists("idx_user_interaction_event_session_id", "user_interaction_event")
    _drop_index_if_exists("idx_user_interaction_event_event_type", "user_interaction_event")
    _drop_index_if_exists("idx_audit_log_actor_id", "audit_log")

    if "study_session" in _tables():
        _drop_column_if_exists("study_session", "ip_hash")
        _drop_column_if_exists("study_session", "metadata")
        _migrate_text_user_id_to_uuid("study_session", nullable=True)
        op.create_index("idx_study_session_user_id", "study_session", ["user_id"], unique=False)

    if "session_consent" in _tables():
        _drop_column_if_exists("session_consent", "metadata")
        _migrate_text_user_id_to_uuid("session_consent", nullable=True)

    for table in ("session_profile", "session_expectation", "recommendation_run", "recommendation_feedback", "session_final_survey"):
        if table in _tables():
            _migrate_text_user_id_to_uuid(table, nullable=True)

    if "app_user" in _tables():
        _drop_column_if_exists("app_user", "password_hash")

    if "recommendation_run" in _tables():
        _drop_column_if_exists("recommendation_run", "trace_id")

    if "recommendation_run_event" in _tables():
        _drop_column_if_exists("recommendation_run_event", "session_id")
        _drop_column_if_exists("recommendation_run_event", "trace_id")
        _drop_column_if_exists("recommendation_run_event", "span_id")

    if "source_document" in _tables():
        _drop_column_if_exists("source_document", "keywords")

    if "llm_usage" in _tables():
        _drop_column_if_exists("llm_usage", "recommendation_id")
        _drop_column_if_exists("llm_usage", "request_metadata")

    # Recreate FKs that pointed at renamed tables.
    if "recommendation_run" in _tables() and "session_id" in _columns("recommendation_run"):
        op.execute(
            sa.text(
                """
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM pg_constraint WHERE conname = 'fk_recommendation_run_session_id'
                    ) THEN
                        ALTER TABLE recommendation_run
                        ADD CONSTRAINT fk_recommendation_run_session_id
                        FOREIGN KEY (session_id) REFERENCES study_session(id);
                    END IF;
                END $$;
                """
            )
        )

    if "recommendation_run" in _tables() and "expectation_id" in _columns("recommendation_run"):
        op.execute(
            sa.text(
                """
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM pg_constraint WHERE conname = 'fk_recommendation_run_expectation_id'
                    ) THEN
                        ALTER TABLE recommendation_run
                        ADD CONSTRAINT fk_recommendation_run_expectation_id
                        FOREIGN KEY (expectation_id) REFERENCES session_expectation(id);
                    END IF;
                END $$;
                """
            )
        )

    # Unique constraints (skip if duplicates would violate).
    if "recommendation_feedback" in _tables():
        op.execute(
            sa.text(
                """
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM pg_constraint WHERE conname = 'uq_feedback_recommendation_session'
                    ) THEN
                        ALTER TABLE recommendation_feedback
                        ADD CONSTRAINT uq_feedback_recommendation_session
                        UNIQUE (recommendation_id, session_id);
                    END IF;
                EXCEPTION WHEN unique_violation THEN
                    NULL;
                END $$;
                """
            )
        )

    if "session_final_survey" in _tables():
        op.execute(
            sa.text(
                """
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM pg_constraint WHERE conname = 'uq_session_final_survey_session'
                    ) THEN
                        ALTER TABLE session_final_survey
                        ADD CONSTRAINT uq_session_final_survey_session
                        UNIQUE (session_id);
                    END IF;
                EXCEPTION WHEN unique_violation THEN
                    NULL;
                END $$;
                """
            )
        )

    # Ensure tables created only via create_all backfill exist with the new names.
    bind = op.get_bind()
    metadata = sa.MetaData()
    if "session_profile" not in _tables():
        op.create_table(
            "session_profile",
            sa.Column("id", UUID(as_uuid=True), primary_key=True),
            sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("app_user.id", ondelete="SET NULL"), nullable=True),
            sa.Column("session_id", UUID(as_uuid=True), sa.ForeignKey("study_session.id"), nullable=False),
            sa.Column("research_area", sa.Text(), nullable=True),
            sa.Column("academic_level", sa.Text(), nullable=True),
            sa.Column("professional_role", sa.Text(), nullable=True),
            sa.Column("experience_with_ai", sa.Text(), nullable=True),
            sa.Column("experience_with_recommender_systems", sa.Text(), nullable=True),
            sa.Column("experience_with_scientific_writing", sa.Text(), nullable=True),
            sa.Column("goal_with_postrec", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        )

    if "session_expectation" not in _tables():
        op.create_table(
            "session_expectation",
            sa.Column("id", UUID(as_uuid=True), primary_key=True),
            sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("app_user.id", ondelete="SET NULL"), nullable=True),
            sa.Column("session_id", UUID(as_uuid=True), sa.ForeignKey("study_session.id"), nullable=False),
            sa.Column("research_area", sa.Text(), nullable=True),
            sa.Column("seed_topics", JSONB(), nullable=False),
            sa.Column("expected_output", sa.Text(), nullable=True),
            sa.Column("desired_depth", sa.Text(), nullable=True),
            sa.Column("preferred_validation", JSONB(), nullable=True),
            sa.Column("avoid_real_user_experiments", sa.Boolean(), server_default=sa.text("true"), nullable=False),
            sa.Column("publication_goal", sa.Text(), nullable=True),
            sa.Column("expects_original_ideas", sa.Boolean(), nullable=True),
            sa.Column("expects_datasets", sa.Boolean(), nullable=True),
            sa.Column("expects_experimental_plan", sa.Boolean(), nullable=True),
            sa.Column("expects_references", sa.Boolean(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        )

    _ensure_pipeline_tables(bind)


def _ensure_pipeline_tables(bind) -> None:
    tables = set(inspect(bind).get_table_names())

    if "recommendation_run_event" not in tables:
        op.create_table(
            "recommendation_run_event",
            sa.Column("id", UUID(as_uuid=True), primary_key=True),
            sa.Column("run_id", UUID(as_uuid=True), sa.ForeignKey("recommendation_run.id"), nullable=False),
            sa.Column("event_type", sa.Text(), nullable=False),
            sa.Column("message", sa.Text(), nullable=False),
            sa.Column("payload", JSONB(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        )

    if "source_document" not in tables:
        op.create_table(
            "source_document",
            sa.Column("id", UUID(as_uuid=True), primary_key=True),
            sa.Column("external_id", sa.Text(), nullable=True),
            sa.Column("source", sa.Text(), nullable=False),
            sa.Column("title", sa.Text(), nullable=False),
            sa.Column("abstract", sa.Text(), nullable=True),
            sa.Column("authors", JSONB(), nullable=True),
            sa.Column("year", sa.Integer(), nullable=True),
            sa.Column("venue", sa.Text(), nullable=True),
            sa.Column("doi", sa.Text(), nullable=True),
            sa.Column("url", sa.Text(), nullable=True),
            sa.Column("citation_count", sa.Integer(), server_default="0"),
            sa.Column("metadata", JSONB(), nullable=True),
            sa.Column("content_hash", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        )
        op.create_index("idx_source_document_doi", "source_document", ["doi"])
        op.create_index("idx_source_document_content_hash", "source_document", ["content_hash"])

    if "document_embedding" not in tables:
        op.execute("CREATE EXTENSION IF NOT EXISTS vector")
        op.create_table(
            "document_embedding",
            sa.Column("id", UUID(as_uuid=True), primary_key=True),
            sa.Column("document_id", UUID(as_uuid=True), sa.ForeignKey("source_document.id"), nullable=False),
            sa.Column("embedding", Vector(768), nullable=False),
            sa.Column("embedding_model", sa.Text(), nullable=False),
            sa.Column("content_hash", sa.Text(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        )

    if "recommendation_candidate" not in tables:
        op.create_table(
            "recommendation_candidate",
            sa.Column("id", UUID(as_uuid=True), primary_key=True),
            sa.Column("run_id", UUID(as_uuid=True), sa.ForeignKey("recommendation_run.id"), nullable=False),
            sa.Column("title", sa.Text(), nullable=False),
            sa.Column("technique_name", sa.Text(), nullable=True),
            sa.Column("research_gap", sa.Text(), nullable=True),
            sa.Column("research_question", sa.Text(), nullable=True),
            sa.Column("hypothesis", sa.Text(), nullable=True),
            sa.Column("proposed_method", sa.Text(), nullable=True),
            sa.Column("related_work_summary", sa.Text(), nullable=True),
            sa.Column("evidence_papers", JSONB(), nullable=True),
            sa.Column("datasets", JSONB(), nullable=True),
            sa.Column("evaluation_metrics", JSONB(), nullable=True),
            sa.Column("experimental_plan", sa.Text(), nullable=True),
            sa.Column("risks", JSONB(), nullable=True),
            sa.Column("expected_contribution", sa.Text(), nullable=True),
            sa.Column("confidence_level", sa.Text(), nullable=True),
            sa.Column("scores", JSONB(), nullable=True),
            sa.Column("final_score", sa.Numeric(), nullable=True),
            sa.Column("status", sa.Text(), server_default="draft", nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        )

    if "recommendation_feedback" not in tables:
        op.create_table(
            "recommendation_feedback",
            sa.Column("id", UUID(as_uuid=True), primary_key=True),
            sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("app_user.id", ondelete="SET NULL"), nullable=True),
            sa.Column("session_id", UUID(as_uuid=True), sa.ForeignKey("study_session.id"), nullable=False),
            sa.Column("run_id", UUID(as_uuid=True), sa.ForeignKey("recommendation_run.id"), nullable=False),
            sa.Column("recommendation_id", UUID(as_uuid=True), sa.ForeignKey("recommendation_candidate.id"), nullable=False),
            sa.Column("relevance_score", sa.Integer(), nullable=True),
            sa.Column("originality_score", sa.Integer(), nullable=True),
            sa.Column("clarity_score", sa.Integer(), nullable=True),
            sa.Column("feasibility_score", sa.Integer(), nullable=True),
            sa.Column("trust_score", sa.Integer(), nullable=True),
            sa.Column("usefulness_score", sa.Integer(), nullable=True),
            sa.Column("would_use_in_real_paper", sa.Text(), nullable=True),
            sa.Column("decision", sa.Text(), nullable=True),
            sa.Column("comment", sa.Text(), nullable=True),
            sa.Column("expectation_alignment_score", sa.Numeric(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.CheckConstraint("relevance_score BETWEEN 1 AND 5", name="ck_relevance_score"),
            sa.CheckConstraint("originality_score BETWEEN 1 AND 5", name="ck_originality_score"),
            sa.CheckConstraint("clarity_score BETWEEN 1 AND 5", name="ck_clarity_score"),
            sa.CheckConstraint("feasibility_score BETWEEN 1 AND 5", name="ck_feasibility_score"),
            sa.CheckConstraint("trust_score BETWEEN 1 AND 5", name="ck_trust_score"),
            sa.CheckConstraint("usefulness_score BETWEEN 1 AND 5", name="ck_usefulness_score"),
            sa.UniqueConstraint("recommendation_id", "session_id", name="uq_feedback_recommendation_session"),
        )
        op.create_index("idx_recommendation_feedback_recommendation_id", "recommendation_feedback", ["recommendation_id"])
        op.create_index("idx_recommendation_feedback_session_id", "recommendation_feedback", ["session_id"])

    if "session_final_survey" not in tables:
        op.create_table(
            "session_final_survey",
            sa.Column("id", UUID(as_uuid=True), primary_key=True),
            sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("app_user.id", ondelete="SET NULL"), nullable=True),
            sa.Column("session_id", UUID(as_uuid=True), sa.ForeignKey("study_session.id"), nullable=False),
            sa.Column("run_id", UUID(as_uuid=True), sa.ForeignKey("recommendation_run.id"), nullable=True),
            sa.Column("expectation_met_score", sa.Integer(), nullable=True),
            sa.Column("would_use_again", sa.Boolean(), nullable=True),
            sa.Column("would_recommend", sa.Boolean(), nullable=True),
            sa.Column("would_use_any_recommendation_in_real_paper", sa.Text(), nullable=True),
            sa.Column("most_useful_recommendation_id", UUID(as_uuid=True), sa.ForeignKey("recommendation_candidate.id"), nullable=True),
            sa.Column("what_helped_most", sa.Text(), nullable=True),
            sa.Column("what_hurt_most", sa.Text(), nullable=True),
            sa.Column("free_comment", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.CheckConstraint("expectation_met_score BETWEEN 1 AND 5", name="ck_expectation_met_score"),
            sa.UniqueConstraint("session_id", name="uq_session_final_survey_session"),
        )

    if "llm_usage" not in tables:
        op.create_table(
            "llm_usage",
            sa.Column("id", UUID(as_uuid=True), primary_key=True),
            sa.Column("run_id", UUID(as_uuid=True), sa.ForeignKey("recommendation_run.id"), nullable=True),
            sa.Column("provider", sa.Text(), nullable=False),
            sa.Column("model", sa.Text(), nullable=False),
            sa.Column("operation", sa.Text(), nullable=False),
            sa.Column("input_tokens", sa.Integer(), server_default="0"),
            sa.Column("output_tokens", sa.Integer(), server_default="0"),
            sa.Column("total_tokens", sa.Integer(), server_default="0"),
            sa.Column("estimated_cost_usd", sa.Numeric(), server_default="0"),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        )
        op.create_index("idx_llm_usage_run_id", "llm_usage", ["run_id"])


def downgrade() -> None:
    raise NotImplementedError("009_schema_standardization downgrade is not supported")
