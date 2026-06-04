"""SQLAlchemy database models."""

import uuid
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "app_user"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    phone_number: Mapped[str | None] = mapped_column(Text, nullable=True)
    email: Mapped[str | None] = mapped_column(Text, unique=True, nullable=True)
    password_hash: Mapped[str | None] = mapped_column(Text, nullable=True)
    full_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    whatsapp_opt_in: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    research_profile: Mapped["UserResearchProfile | None"] = relationship(
        back_populates="user", uselist=False
    )


class AuthOtpChallenge(Base):
    __tablename__ = "auth_otp_challenge"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    phone_number: Mapped[str] = mapped_column(Text, nullable=False)
    code_hash: Mapped[str] = mapped_column(Text, nullable=False)
    purpose: Mapped[str] = mapped_column(Text, nullable=False, default="login")
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class UserResearchProfile(Base):
    __tablename__ = "user_research_profile"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("app_user.id"), unique=True, nullable=False
    )
    research_area: Mapped[str | None] = mapped_column(Text, nullable=True)
    academic_level: Mapped[str | None] = mapped_column(Text, nullable=True)
    professional_role: Mapped[str | None] = mapped_column(Text, nullable=True)
    experience_with_ai: Mapped[str | None] = mapped_column(Text, nullable=True)
    experience_with_recommender_systems: Mapped[str | None] = mapped_column(Text, nullable=True)
    experience_with_scientific_writing: Mapped[str | None] = mapped_column(Text, nullable=True)
    goal_with_postrec: Mapped[str | None] = mapped_column(Text, nullable=True)
    learned_topics: Mapped[list | None] = mapped_column(JSONB, nullable=True, default=list)
    avoided_topics: Mapped[list | None] = mapped_column(JSONB, nullable=True, default=list)
    preferred_techniques: Mapped[list | None] = mapped_column(JSONB, nullable=True, default=list)
    feedback_notes: Mapped[list | None] = mapped_column(JSONB, nullable=True, default=list)
    recommendation_defaults: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="research_profile")


class VolunteerSession(Base):
    __tablename__ = "volunteer_session"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(Text, nullable=False, default="started")
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    ip_hash: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)

    consents: Mapped[list["ParticipantConsent"]] = relationship(back_populates="session")
    profiles: Mapped[list["ParticipantProfile"]] = relationship(back_populates="session")
    expectations: Mapped[list["UserExpectation"]] = relationship(back_populates="session")
    runs: Mapped[list["RecommendationRun"]] = relationship(back_populates="session")


class ParticipantConsent(Base):
    __tablename__ = "participant_consent"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[str] = mapped_column(Text, nullable=False)
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("volunteer_session.id"), nullable=False
    )
    consent_version: Mapped[str] = mapped_column(Text, nullable=False)
    accepted: Mapped[bool] = mapped_column(Boolean, nullable=False)
    accepted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)

    session: Mapped["VolunteerSession"] = relationship(back_populates="consents")


class ParticipantProfile(Base):
    __tablename__ = "participant_profile"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[str] = mapped_column(Text, nullable=False)
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("volunteer_session.id"), nullable=False
    )
    research_area: Mapped[str | None] = mapped_column(Text, nullable=True)
    academic_level: Mapped[str | None] = mapped_column(Text, nullable=True)
    professional_role: Mapped[str | None] = mapped_column(Text, nullable=True)
    experience_with_ai: Mapped[str | None] = mapped_column(Text, nullable=True)
    experience_with_recommender_systems: Mapped[str | None] = mapped_column(Text, nullable=True)
    experience_with_scientific_writing: Mapped[str | None] = mapped_column(Text, nullable=True)
    goal_with_postrec: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    session: Mapped["VolunteerSession"] = relationship(back_populates="profiles")


class UserExpectation(Base):
    __tablename__ = "user_expectation"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("volunteer_session.id"), nullable=False
    )
    research_area: Mapped[str | None] = mapped_column(Text, nullable=True)
    seed_topics: Mapped[list] = mapped_column(JSONB, nullable=False)
    expected_output: Mapped[str | None] = mapped_column(Text, nullable=True)
    desired_depth: Mapped[str | None] = mapped_column(Text, nullable=True)
    preferred_validation: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    avoid_real_user_experiments: Mapped[bool] = mapped_column(Boolean, default=True)
    publication_goal: Mapped[str | None] = mapped_column(Text, nullable=True)
    expects_original_ideas: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    expects_datasets: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    expects_experimental_plan: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    expects_references: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    session: Mapped["VolunteerSession"] = relationship(back_populates="expectations")
    runs: Mapped[list["RecommendationRun"]] = relationship(back_populates="expectation")


class RecommendationRun(Base):
    __tablename__ = "recommendation_run"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    request_id: Mapped[str | None] = mapped_column(Text, unique=True, nullable=True)
    user_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    session_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("volunteer_session.id"), nullable=True
    )
    expectation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user_expectation.id"), nullable=True
    )
    input: Mapped[dict] = mapped_column(JSONB, nullable=False)
    mode: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False)
    progress: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    current_step: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    max_papers: Mapped[int] = mapped_column(Integer, nullable=False)
    max_recommendations: Mapped[int] = mapped_column(Integer, nullable=False)
    trace_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    estimated_cost_usd: Mapped[float] = mapped_column(Numeric, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    session: Mapped["VolunteerSession | None"] = relationship(back_populates="runs")
    expectation: Mapped["UserExpectation | None"] = relationship(back_populates="runs")
    events: Mapped[list["RecommendationRunEvent"]] = relationship(back_populates="run")
    candidates: Mapped[list["RecommendationCandidate"]] = relationship(back_populates="run")


class RecommendationRunEvent(Base):
    __tablename__ = "recommendation_run_event"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("recommendation_run.id"), nullable=False
    )
    session_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("volunteer_session.id"), nullable=True
    )
    event_type: Mapped[str] = mapped_column(Text, nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    trace_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    span_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    run: Mapped["RecommendationRun"] = relationship(back_populates="events")


class SourceDocument(Base):
    __tablename__ = "source_document"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    external_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    source: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    abstract: Mapped[str | None] = mapped_column(Text, nullable=True)
    authors: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    venue: Mapped[str | None] = mapped_column(Text, nullable=True)
    doi: Mapped[str | None] = mapped_column(Text, nullable=True)
    url: Mapped[str | None] = mapped_column(Text, nullable=True)
    citation_count: Mapped[int] = mapped_column(Integer, default=0)
    keywords: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)
    content_hash: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    embeddings: Mapped[list["DocumentEmbedding"]] = relationship(back_populates="document")


class DocumentEmbedding(Base):
    __tablename__ = "document_embedding"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("source_document.id"), nullable=False
    )
    embedding = mapped_column(Vector(768), nullable=False)  # must match GEMINI_EMBEDDING_DIMENSIONS
    embedding_model: Mapped[str] = mapped_column(Text, nullable=False)
    content_hash: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    document: Mapped["SourceDocument"] = relationship(back_populates="embeddings")


class RecommendationCandidate(Base):
    __tablename__ = "recommendation_candidate"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("recommendation_run.id"), nullable=False
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    technique_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    research_gap: Mapped[str | None] = mapped_column(Text, nullable=True)
    research_question: Mapped[str | None] = mapped_column(Text, nullable=True)
    hypothesis: Mapped[str | None] = mapped_column(Text, nullable=True)
    proposed_method: Mapped[str | None] = mapped_column(Text, nullable=True)
    related_work_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidence_papers: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    datasets: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    evaluation_metrics: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    experimental_plan: Mapped[str | None] = mapped_column(Text, nullable=True)
    risks: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    expected_contribution: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence_level: Mapped[str | None] = mapped_column(Text, nullable=True)
    scores: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    final_score: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    status: Mapped[str] = mapped_column(Text, nullable=False, default="draft")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    run: Mapped["RecommendationRun"] = relationship(back_populates="candidates")
    feedback: Mapped[list["RecommendationFeedback"]] = relationship(back_populates="recommendation")


class RecommendationFeedback(Base):
    __tablename__ = "recommendation_feedback"
    __table_args__ = (
        CheckConstraint("relevance_score BETWEEN 1 AND 5", name="ck_relevance_score"),
        CheckConstraint("originality_score BETWEEN 1 AND 5", name="ck_originality_score"),
        CheckConstraint("clarity_score BETWEEN 1 AND 5", name="ck_clarity_score"),
        CheckConstraint("feasibility_score BETWEEN 1 AND 5", name="ck_feasibility_score"),
        CheckConstraint("trust_score BETWEEN 1 AND 5", name="ck_trust_score"),
        CheckConstraint("usefulness_score BETWEEN 1 AND 5", name="ck_usefulness_score"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("volunteer_session.id"), nullable=False
    )
    run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("recommendation_run.id"), nullable=False
    )
    recommendation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("recommendation_candidate.id"), nullable=False
    )
    relevance_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    originality_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    clarity_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    feasibility_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    trust_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    usefulness_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    would_use_in_real_paper: Mapped[str | None] = mapped_column(Text, nullable=True)
    decision: Mapped[str | None] = mapped_column(Text, nullable=True)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    expectation_alignment_score: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    recommendation: Mapped["RecommendationCandidate"] = relationship(back_populates="feedback")


class UserInteractionEvent(Base):
    __tablename__ = "user_interaction_event"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("volunteer_session.id"), nullable=False
    )
    run_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("recommendation_run.id"), nullable=True
    )
    recommendation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("recommendation_candidate.id"), nullable=True
    )
    event_type: Mapped[str] = mapped_column(Text, nullable=False)
    event_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class SessionFinalSurvey(Base):
    __tablename__ = "session_final_survey"
    __table_args__ = (
        CheckConstraint(
            "expectation_met_score BETWEEN 1 AND 5", name="ck_expectation_met_score"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("volunteer_session.id"), nullable=False
    )
    run_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("recommendation_run.id"), nullable=True
    )
    expectation_met_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    would_use_again: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    would_recommend: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    would_use_any_recommendation_in_real_paper: Mapped[str | None] = mapped_column(Text, nullable=True)
    most_useful_recommendation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("recommendation_candidate.id"), nullable=True
    )
    what_helped_most: Mapped[str | None] = mapped_column(Text, nullable=True)
    what_hurt_most: Mapped[str | None] = mapped_column(Text, nullable=True)
    free_comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class LLMUsage(Base):
    __tablename__ = "llm_usage"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("recommendation_run.id"), nullable=True
    )
    recommendation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("recommendation_candidate.id"), nullable=True
    )
    provider: Mapped[str] = mapped_column(Text, nullable=False)
    model: Mapped[str] = mapped_column(Text, nullable=False)
    operation: Mapped[str] = mapped_column(Text, nullable=False)
    input_tokens: Mapped[int] = mapped_column(Integer, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0)
    total_tokens: Mapped[int] = mapped_column(Integer, default=0)
    estimated_cost_usd: Mapped[float] = mapped_column(Numeric, default=0)
    request_metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ExportedArtifact(Base):
    __tablename__ = "exported_artifact"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    recommendation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("recommendation_candidate.id"), nullable=False
    )
    artifact_type: Mapped[str] = mapped_column(Text, nullable=False)
    file_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    actor_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    action: Mapped[str] = mapped_column(Text, nullable=False)
    entity_type: Mapped[str] = mapped_column(Text, nullable=False)
    entity_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


Index("idx_app_user_phone_number", User.phone_number, unique=True)
Index("idx_app_user_email", User.email, unique=True)
Index("idx_auth_otp_phone_created", AuthOtpChallenge.phone_number, AuthOtpChallenge.created_at)
Index("idx_user_research_profile_user_id", UserResearchProfile.user_id, unique=True)
Index("idx_recommendation_run_user_id", RecommendationRun.user_id)
Index("idx_volunteer_session_user_id", VolunteerSession.user_id)
Index("idx_recommendation_run_session_id", RecommendationRun.session_id)
Index("idx_recommendation_run_status", RecommendationRun.status)
Index("idx_recommendation_run_created_at", RecommendationRun.created_at)
Index("idx_recommendation_feedback_recommendation_id", RecommendationFeedback.recommendation_id)
Index("idx_recommendation_feedback_session_id", RecommendationFeedback.session_id)
Index("idx_user_interaction_event_session_id", UserInteractionEvent.session_id)
Index("idx_user_interaction_event_event_type", UserInteractionEvent.event_type)
Index("idx_source_document_doi", SourceDocument.doi)
Index("idx_source_document_content_hash", SourceDocument.content_hash)
Index("idx_llm_usage_run_id", LLMUsage.run_id)
Index("idx_audit_log_actor_id", AuditLog.actor_id)
