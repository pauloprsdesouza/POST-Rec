"""Pydantic schemas for API requests and responses."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class SessionCreate(BaseModel):
    user_id: str | None = None
    user_agent: str | None = None


class SessionResponse(BaseModel):
    session_id: UUID
    status: str


class ConsentCreate(BaseModel):
    user_id: str
    session_id: UUID
    consent_version: str = "v1.0"
    accepted: bool


class ConsentResponse(BaseModel):
    id: UUID
    accepted: bool


class UserConsentStatusResponse(BaseModel):
    accepted: bool
    consent_version: str | None = None
    accepted_at: datetime | None = None


class RecommendationDefaults(BaseModel):
    seed_topics: list[str] = Field(default_factory=list)
    expected_output: str | None = None
    desired_depth: str = "medium"
    avoid_real_user_experiments: bool = True
    max_article_age_years: int = Field(default=5, ge=1, le=30)


class ProfileCreate(BaseModel):
    user_id: str
    session_id: UUID
    research_area: str | None = None
    academic_level: str | None = None
    professional_role: str | None = None
    experience_with_ai: str | None = None
    experience_with_recommender_systems: str | None = None
    experience_with_scientific_writing: str | None = None
    goal_with_postrec: str | None = None


class ProfileResponse(BaseModel):
    id: UUID


class ExpectationCreate(BaseModel):
    session_id: UUID
    user_id: str | None = None
    research_area: str | None = None
    seed_topics: list[str]
    expected_output: str | None = None
    desired_depth: str | None = "medium"
    preferred_validation: list[str] | None = None
    avoid_real_user_experiments: bool = True
    publication_goal: str | None = None
    expects_original_ideas: bool | None = True
    expects_datasets: bool | None = True
    expects_experimental_plan: bool | None = True
    expects_references: bool | None = True


class ExpectationResponse(BaseModel):
    id: UUID


class RunConstraints(BaseModel):
    avoid_real_user_experiments: bool = True
    prefer_public_datasets: bool = True
    prefer_reproducibility: bool = True
    max_article_age_years: int | None = Field(default=None, ge=1, le=30)


class RecommendationRunCreate(BaseModel):
    session_id: UUID
    expectation_id: UUID | None = None
    request_id: str | None = None
    topics: list[str]
    mode: str = "quick"
    max_papers: int = Field(default=50, le=200)
    max_recommendations: int = Field(default=5, le=10)
    constraints: RunConstraints = Field(default_factory=RunConstraints)


class RecommendationRunResponse(BaseModel):
    run_id: UUID
    status: str
    progress: int
    message: str


class RunUsageLineResponse(BaseModel):
    operation: str
    model: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    estimated_cost_usd: float


class RunUsageSummaryResponse(BaseModel):
    estimated_cost_usd: float
    input_tokens: int
    output_tokens: int
    total_tokens: int
    estimated_cost_per_recommendation_usd: float | None = None
    lines: list[RunUsageLineResponse] = Field(default_factory=list)


class RunDetailResponse(BaseModel):
    id: UUID
    status: str
    progress: int
    current_step: str | None
    mode: str | None = None
    error_message: str | None
    estimated_cost_usd: float
    created_at: datetime
    started_at: datetime | None
    finished_at: datetime | None
    recommendation_count: int = 0
    topics: list[str] = Field(default_factory=list)
    usage: RunUsageSummaryResponse | None = None


class RunEventResponse(BaseModel):
    id: UUID
    event_type: str
    message: str
    created_at: datetime
    level: str = "info"


class RecommendationResponse(BaseModel):
    id: UUID
    title: str
    technique_name: str | None
    research_gap: str | None
    research_question: str | None
    hypothesis: str | None
    proposed_method: str | None
    related_work_summary: str | None = None
    expected_contribution: str | None = None
    sota_summary: str | None = None
    novelty_delta: str | None = None
    closest_prior_work: str | None = None
    differentiation_score_rationale: str | None = None
    sota_anchors: list | None = None
    sota_fit: float | None = None
    novelty_verified: float | None = None
    facet_novelty_index: float | None = None
    gap_alignment_score: float | None = None
    fggv_score: float | None = None
    facet_deltas: dict | None = None
    aligned_gaps: list | None = None
    recency_gap: float | None = None
    embedding_distance: float | None = None
    critic_accepted: bool | None = None
    validation_issues: list[str] | None = None
    status: str = "published"
    evidence_papers: list | None
    datasets: list | None
    evaluation_metrics: list | None
    experimental_plan: str | None
    risks: list | None
    confidence_level: str | None
    scores: dict | None = None
    final_score: float | None


class SourceDocumentResponse(BaseModel):
    id: UUID
    source: str
    title: str
    abstract: str | None
    authors: list | None
    year: int | None
    venue: str | None
    doi: str | None
    url: str | None
    citation_count: int


class FeedbackCreate(BaseModel):
    session_id: UUID
    run_id: UUID
    relevance_score: int = Field(ge=1, le=5)
    originality_score: int = Field(ge=1, le=5)
    clarity_score: int = Field(ge=1, le=5)
    feasibility_score: int = Field(ge=1, le=5)
    trust_score: int = Field(ge=1, le=5)
    usefulness_score: int = Field(ge=1, le=5)
    would_use_in_real_paper: str
    decision: str
    comment: str | None = None


class FeedbackResponse(BaseModel):
    id: UUID
    expectation_alignment_score: float


class FinalSurveyCreate(BaseModel):
    session_id: UUID
    run_id: UUID | None = None
    user_id: str | None = None
    expectation_met_score: int = Field(ge=1, le=5)
    would_use_again: bool
    would_recommend: bool
    would_use_any_recommendation_in_real_paper: str
    most_useful_recommendation_id: UUID | None = None
    what_helped_most: str | None = None
    what_hurt_most: str | None = None
    free_comment: str | None = None


class ValidationDashboardResponse(BaseModel):
    average_eas: float
    approval_rate: float
    would_use_rate: float
    average_trust_score: float
    average_feasibility_score: float
    average_usefulness_score: float
    run_completion_rate: float
    run_failure_rate: float
    total_runs: int
    total_feedback: int
    rejection_reasons: list[str]
    sota_anchor_rate: float = 0.0
    refinement_rate: float = 0.0
    avg_novelty_verified: float = 0.0
    avg_sota_fit: float = 0.0


class HealthResponse(BaseModel):
    status: str


class RegisterRequest(BaseModel):
    full_name: str = Field(min_length=2)
    email: str
    phone_number: str
    whatsapp_opt_in: bool = True


class LoginOtpRequest(BaseModel):
    email: str


class OtpRequestResponse(BaseModel):
    message: str
    expires_in_seconds: int
    dev_code: str | None = None
    phone_hint: str | None = None


class OtpVerify(BaseModel):
    email: str
    code: str = Field(min_length=4, max_length=8)


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: UUID
    phone_number: str
    email: str | None = None
    full_name: str | None = None
    whatsapp_opt_in: bool = True


class UserMeResponse(BaseModel):
    id: UUID
    phone_number: str
    email: str | None = None
    full_name: str | None = None
    whatsapp_opt_in: bool = True


class UserAccountResponse(BaseModel):
    full_name: str | None = None
    email: str | None = None
    phone_number: str | None = None
    whatsapp_opt_in: bool = True


class UserAccountUpdate(BaseModel):
    full_name: str | None = None
    email: str | None = None
    phone_number: str | None = None
    whatsapp_opt_in: bool | None = None


class UserProfileResponse(BaseModel):
    research_area: str | None = None
    academic_level: str | None = None
    professional_role: str | None = None
    experience_with_ai: str | None = None
    experience_with_recommender_systems: str | None = None
    experience_with_scientific_writing: str | None = None
    goal_with_postrec: str | None = None
    learned_topics: list[str] = Field(default_factory=list)
    avoided_topics: list[str] = Field(default_factory=list)
    preferred_techniques: list[str] = Field(default_factory=list)
    recommendation_defaults: RecommendationDefaults | None = None
    updated_at: datetime | None = None


class UserProfileUpdate(BaseModel):
    research_area: str | None = None
    academic_level: str | None = None
    professional_role: str | None = None
    experience_with_ai: str | None = None
    experience_with_recommender_systems: str | None = None
    experience_with_scientific_writing: str | None = None
    goal_with_postrec: str | None = None
    recommendation_defaults: RecommendationDefaults | None = None


class RunSummaryResponse(BaseModel):
    id: UUID
    status: str
    progress: int
    mode: str | None = None
    created_at: datetime
    finished_at: datetime | None
    topics: list[str] = Field(default_factory=list)
    recommendation_count: int = 0


class ReadyResponse(BaseModel):
    status: str
    checks: dict[str, str]
