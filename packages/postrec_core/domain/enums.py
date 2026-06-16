"""POST-Rec core domain enums."""

from enum import StrEnum


class RunStatus(StrEnum):
    QUEUED = "queued"
    STARTED = "started"
    SEARCHING_PAPERS = "searching_papers"
    NORMALIZING_DOCUMENTS = "normalizing_documents"
    DEDUPLICATING_DOCUMENTS = "deduplicating_documents"
    GENERATING_EMBEDDINGS = "generating_embeddings"
    RANKING_CANDIDATES = "ranking_candidates"
    GENERATING_RECOMMENDATIONS = "generating_recommendations"
    VALIDATING_OUTPUT = "validating_output"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    COST_LIMIT_EXCEEDED = "cost_limit_exceeded"
    FAILED_SCHEMA_VALIDATION = "failed_schema_validation"


class SessionStatus(StrEnum):
    STARTED = "started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class FeedbackDecision(StrEnum):
    APPROVED = "approved"
    REJECTED = "rejected"
    SAVE = "save"
    NEEDS_REVISION = "needs_revision"
    NOT_UNDERSTOOD = "not_understood"
    SEEN_BEFORE = "seen_before"


class WouldUseInPaper(StrEnum):
    YES = "yes"
    MAYBE = "maybe"
    NO = "no"


class CandidateStatus(StrEnum):
    DRAFT = "draft"
    PUBLISHED = "published"
    NEEDS_REFINEMENT = "needs_refinement"


class UserRole(StrEnum):
    """Application access role (distinct from research profile professional_role)."""

    RESEARCHER = "researcher"
    ADMIN = "admin"
