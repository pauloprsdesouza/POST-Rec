"""Pydantic schemas for API requests and responses."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class SessionCreate(BaseModel):
    user_agent: str | None = None


class SessionResponse(BaseModel):
    session_id: UUID
    status: str


class ConsentCreate(BaseModel):
    session_id: UUID
    consent_version: str = "v1.0"
    accepted: bool
    user_id: str | None = None  # ignored; derived from auth token


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
    user_id: UUID | None = None
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
    presentation_profile: str = "standard"
    error_message: str | None
    estimated_cost_usd: float
    created_at: datetime
    started_at: datetime | None
    finished_at: datetime | None
    recommendation_count: int = 0
    feedback_count: int = 0
    feedback_complete: bool = False
    topics: list[str] = Field(default_factory=list)
    usage: RunUsageSummaryResponse | None = None


class RunEventResponse(BaseModel):
    id: UUID
    event_type: str
    message: str
    created_at: datetime
    level: str = "info"


class RecommendationUserFeedbackResponse(BaseModel):
    relevance_score: int | None = None
    decision: str | None = None


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
    user_feedback: RecommendationUserFeedbackResponse | None = None


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
    qualis_estrato: str | None = None
    paper_id: str | None = None


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
    user_id: UUID | None = None
    expectation_met_score: int = Field(ge=1, le=5)
    would_use_again: bool | None = None
    would_recommend: bool | None = None
    would_use_any_recommendation_in_real_paper: str | None = None
    most_useful_recommendation_id: UUID | None = None
    what_helped_most: str | None = None
    what_hurt_most: str | None = None
    free_comment: str | None = None


class ExperimentVariantMetrics(BaseModel):
    variant: str
    run_count: int
    completed_count: int
    feedback_count: int
    average_eas: float
    average_originality: float
    approval_rate: float
    would_use_rate: float


class ExperimentDashboardSection(BaseModel):
    experiment_id: str
    active: bool
    presentation_profile: str
    variants: list[ExperimentVariantMetrics] = Field(default_factory=list)


class SurveyMetricsSection(BaseModel):
    count: int = 0
    expectation_met_mean: float = 0.0
    would_use_again_rate: float = 0.0
    would_recommend_rate: float = 0.0


class RatingDistribution(BaseModel):
    dimension: str
    mean: float
    std: float
    min: float
    max: float
    count: int
    distribution: dict[str, int] = Field(default_factory=dict)


class WeeklyTrendPoint(BaseModel):
    week: str
    feedback_count: int = 0
    runs: int = 0
    surveys: int = 0
    average_eas: float | None = None


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
    experiment: ExperimentDashboardSection | None = None
    survey_metrics: SurveyMetricsSection = Field(default_factory=SurveyMetricsSection)
    rating_distributions: list[RatingDistribution] = Field(default_factory=list)
    weekly_trends: list[WeeklyTrendPoint] = Field(default_factory=list)
    ranking_summary: dict = Field(default_factory=dict)


class HypothesisTestResultResponse(BaseModel):
    test_name: str
    statistic: float
    p_value: float | None = None
    effect_size: float | None = None
    effect_size_name: str | None = None
    group_a_mean: float
    group_b_mean: float
    group_a_n: int
    group_b_n: int
    significant_at_005: bool
    interpretation: str


class GroupComparisonResponse(BaseModel):
    label_a: str
    label_b: str
    mann_whitney: HypothesisTestResultResponse
    welch_t_test: HypothesisTestResultResponse
    recommended_test: str


class ResearchReportResponse(BaseModel):
    generated_at: str
    schema_version: str
    sample: dict
    primary_outcomes: dict
    descriptive_statistics: list[dict]
    survey_outcomes: dict
    sota_quality: dict
    ranking_metrics: dict
    experiment_analysis: dict | None = None
    mode_comparison: list[dict]
    score_correlations: list[dict]
    rejection_summary: dict
    weekly_trends: list[dict]
    expert_label_analysis: dict | None = None
    methodology_notes: dict


class HealthResponse(BaseModel):
    status: str


class RegisterRequest(BaseModel):
    full_name: str = Field(min_length=2)
    email: str
    phone_number: str | None = None
    whatsapp_opt_in: bool = False


class LoginOtpRequest(BaseModel):
    email: str


class OtpRequestResponse(BaseModel):
    message: str
    expires_in_seconds: int
    dev_code: str | None = None
    email_hint: str | None = None
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
    role: str = "researcher"


class UserMeResponse(BaseModel):
    id: UUID
    phone_number: str
    email: str | None = None
    full_name: str | None = None
    whatsapp_opt_in: bool = True
    role: str = "researcher"
    is_admin: bool = False
    can_access_admin: bool = False
    can_use_research_features: bool = True


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
    presentation_profile: str = "standard"
    created_at: datetime
    finished_at: datetime | None
    topics: list[str] = Field(default_factory=list)
    recommendation_count: int = 0
    feedback_count: int = 0
    feedback_complete: bool = False
    search_match_count: int | None = None
    search_snippet: str | None = None


class RunCleanupRequest(BaseModel):
    remove_learned_topics: list[str] = Field(default_factory=list)


class RunCleanupPreviewResponse(BaseModel):
    learned_topics: list[str] = Field(default_factory=list)


class RunActionResponse(BaseModel):
    status: str
    message: str


class ExperimentEnrollmentResponse(BaseModel):
    experiment_active: bool
    experiment_id: str | None = None
    enrolled: bool
    presentation_profile: str = "standard"
    control_mode: str = "sota"
    treatment_mode: str = "fggv"


class AdminUserCounts(BaseModel):
    total: int
    active: int
    admins: int
    researchers: int


class AdminRunCounts(BaseModel):
    total: int
    completed: int
    failed: int
    completion_rate: float
    failure_rate: float


class AdminOverviewResponse(BaseModel):
    generated_at: str
    users: AdminUserCounts
    runs: AdminRunCounts
    feedback_total: int
    llm_cost_usd_total: float
    system_status: str
    health_checks: dict[str, str]
    app_env: str


class AdminSystemConfigResponse(BaseModel):
    generated_at: str
    environment: dict


class AdminModelAggregate(BaseModel):
    call_count: int
    total_tokens: int
    estimated_cost_usd: float


class AdminConfiguredModels(BaseModel):
    generation: str
    embedding: str
    embedding_dimensions: int


class AdminModelSummary(BaseModel):
    provider: str
    model: str
    call_count: int
    input_tokens: int
    output_tokens: int
    total_tokens: int
    estimated_cost_usd: float


class AdminModelOperation(BaseModel):
    provider: str
    model: str
    operation: str
    call_count: int
    input_tokens: int
    output_tokens: int
    total_tokens: int
    estimated_cost_usd: float


class AdminModelEvaluationResponse(BaseModel):
    generated_at: str
    configured_models: AdminConfiguredModels
    aggregate: AdminModelAggregate
    models: list[AdminModelSummary]
    operations: list[AdminModelOperation]


class AdminUserResponse(BaseModel):
    id: UUID
    email: str | None = None
    full_name: str | None = None
    phone_number: str | None = None
    role: str
    is_active: bool
    is_admin: bool
    created_at: str | None = None


class AdminUserListResponse(BaseModel):
    total: int
    items: list[AdminUserResponse]


class AdminUserRoleUpdate(BaseModel):
    role: str = Field(pattern="^(researcher|admin)$")


class ReadyResponse(BaseModel):
    status: str
    checks: dict[str, str]


class ProjectCreate(BaseModel):
    recommendation_id: UUID


class ProjectTaskResponse(BaseModel):
    id: UUID
    status: str
    user_notes: str | None = None
    completed_at: datetime | None = None


class ProjectTaskUpdate(BaseModel):
    status: str | None = Field(default=None, pattern="^(todo|in_progress|done|skipped)$")
    user_notes: str | None = None


class ProjectTaskItem(BaseModel):
    id: UUID
    order_index: int
    title: str
    description: str | None = None
    guidance: str | None = None
    effort: str | None = None
    linked_fields: list[str] = Field(default_factory=list)
    linked_paper_ids: list[str] = Field(default_factory=list)
    checklist: list[str] = Field(default_factory=list)
    status: str
    user_notes: str | None = None
    completed_at: datetime | None = None


class ProjectPhaseItem(BaseModel):
    id: UUID
    order_index: int
    title: str
    description: str | None = None
    status: str
    tasks: list[ProjectTaskItem] = Field(default_factory=list)


class ProjectResponse(BaseModel):
    id: UUID
    run_id: UUID
    recommendation_id: UUID
    title: str
    status: str
    progress_pct: int
    current_phase_id: UUID | None = None
    locale: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    phases: list[ProjectPhaseItem] = Field(default_factory=list)


class ProjectListItem(BaseModel):
    id: UUID
    run_id: UUID
    recommendation_id: UUID
    title: str
    status: str
    progress_pct: int
    current_phase_title: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ProjectExportResponse(BaseModel):
    content: str
    format: str = "markdown"
