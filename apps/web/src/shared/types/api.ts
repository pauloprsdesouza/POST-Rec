export interface AuthResponse {
  access_token: string;
  token_type: string;
  user_id: string;
  phone_number: string;
  email?: string | null;
  full_name?: string | null;
  whatsapp_opt_in?: boolean;
  role?: UserRole;
}

export type UserRole = "researcher" | "admin";

export interface UserMe {
  id: string;
  phone_number: string;
  email?: string | null;
  full_name?: string | null;
  whatsapp_opt_in?: boolean;
  role: UserRole;
  is_admin?: boolean;
  can_access_admin?: boolean;
  can_use_research_features?: boolean;
}

export interface OtpRequestResponse {
  message: string;
  expires_in_seconds: number;
  dev_code?: string | null;
  email_hint?: string | null;
  phone_hint?: string | null;
}

export interface UserAccount {
  full_name?: string | null;
  email?: string | null;
  phone_number?: string | null;
  whatsapp_opt_in?: boolean;
}

export interface UserProfile {
  research_area?: string | null;
  academic_level?: string | null;
  professional_role?: string | null;
  experience_with_ai?: string | null;
  experience_with_recommender_systems?: string | null;
  experience_with_scientific_writing?: string | null;
  goal_with_postrec?: string | null;
  learned_topics?: string[] | null;
  avoided_topics?: string[] | null;
  preferred_techniques?: string[] | null;
  recommendation_defaults?: RecommendationDefaults | null;
  updated_at?: string | null;
}

export type RunMode = "quick" | "sota" | "exploratory" | "fggv";
export type RunModeSelection = "auto" | RunMode;

export interface RecommendationDefaults {
  seed_topics?: string[];
  expected_output?: string | null;
  desired_depth?: string;
  preferred_run_mode?: RunModeSelection;
  max_article_age_years?: number;
}

export interface SotaAnchor {
  paper_id?: string;
  title?: string;
  year?: number;
  doi?: string | null;
  url?: string;
  role?: string;
}

export interface UserConsentStatus {
  accepted: boolean;
  consent_version?: string | null;
  accepted_at?: string | null;
}

export interface RunUsageLine {
  operation: string;
  model: string;
  input_tokens: number;
  output_tokens: number;
  total_tokens: number;
  estimated_cost_usd: number;
}

export interface RunUsageSummary {
  estimated_cost_usd: number;
  input_tokens: number;
  output_tokens: number;
  total_tokens: number;
  estimated_cost_per_recommendation_usd?: number | null;
  lines: RunUsageLine[];
}

export interface RecommendationRun {
  id: string;
  status: string;
  progress: number;
  mode?: string;
  presentation_profile?: "standard" | "blind";
  current_step?: string | null;
  topics?: string[];
  created_at?: string;
  started_at?: string | null;
  finished_at?: string | null;
  estimated_cost_usd?: number;
  error_message?: string | null;
  recommendation_count?: number;
  feedback_count?: number;
  feedback_complete?: boolean;
  search_match_count?: number | null;
  search_snippet?: string | null;
  usage?: RunUsageSummary | null;
}

export interface RecommendationUserFeedback {
  relevance_score?: number | null;
  decision?: string | null;
}

export interface RunEvent {
  event_type: string;
  message: string;
  created_at?: string;
  level?: "info" | "warning" | "error";
}

export interface EvidencePaper {
  paper_id?: string;
  title?: string;
  year?: number;
  doi?: string;
  url?: string;
  authors?: string[];
  why_relevant?: string;
  retrieval_source?: string;
  citation_count?: number;
  venue?: string;
  abstract?: string;
  qualis_estrato?: string;
  qualis_period?: string;
  qualis_boost?: number;
  relevance_score?: number;
  matched_in_catalog?: boolean;
}

export interface Recommendation {
  id: string;
  title: string;
  technique_name?: string;
  research_gap?: string;
  research_question?: string;
  hypothesis?: string;
  related_work_summary?: string;
  expected_contribution?: string;
  sota_summary?: string;
  novelty_delta?: string;
  closest_prior_work?: string;
  differentiation_score_rationale?: string;
  sota_anchors?: SotaAnchor[];
  sota_fit?: number;
  novelty_verified?: number;
  facet_novelty_index?: number;
  gap_alignment_score?: number;
  fggv_score?: number;
  facet_deltas?: Record<string, string>;
  aligned_gaps?: string[];
  recency_gap?: number;
  embedding_distance?: number;
  critic_accepted?: boolean;
  validation_issues?: string[];
  status?: string;
  proposed_method?: string;
  experimental_plan?: string;
  datasets?: string[];
  evaluation_metrics?: string[];
  risks?: string[];
  evidence_papers?: EvidencePaper[];
  scores?: Record<string, number>;
  final_score?: number;
  confidence_level?: string;
  user_feedback?: RecommendationUserFeedback | null;
}

export interface SourceDocument {
  id?: string;
  paper_id?: string;
  title?: string;
  year?: number;
  source?: string;
  url?: string;
  doi?: string;
  authors?: string[];
  venue?: string;
  citation_count?: number;
  qualis_estrato?: string;
}

export interface ValidationDashboard {
  average_eas: number;
  approval_rate: number;
  would_use_rate: number;
  run_failure_rate: number;
  run_completion_rate: number;
  average_trust_score: number;
  average_feasibility_score: number;
  average_usefulness_score: number;
  total_runs: number;
  total_feedback: number;
  rejection_reasons: string[];
  sota_anchor_rate?: number;
  refinement_rate?: number;
  avg_novelty_verified?: number;
  avg_sota_fit?: number;
  experiment?: ExperimentDashboard | null;
  survey_metrics?: SurveyMetrics;
  rating_distributions?: RatingDistribution[];
  weekly_trends?: WeeklyTrendPoint[];
  ranking_summary?: RankingSummary;
}

export interface SurveyMetrics {
  count: number;
  expectation_met_mean: number;
  would_use_again_rate: number;
  would_recommend_rate: number;
}

export interface RatingDistribution {
  dimension: string;
  mean: number;
  std: number;
  min: number;
  max: number;
  count: number;
  distribution: Record<string, number>;
}

export interface WeeklyTrendPoint {
  week: string;
  feedback_count: number;
  runs: number;
  surveys: number;
  average_eas: number | null;
  [key: string]: string | number | null;
}

export interface RankingSummary {
  run_count?: number;
  "ndcg@1"?: number;
  "ndcg@3"?: number;
  "ndcg@5"?: number;
  "ndcg@10"?: number;
  "err@3"?: number;
  "err@5"?: number;
  "err@10"?: number;
  map?: number;
  mrr?: number;
  "precision@1"?: number;
  "precision@3"?: number;
  "precision@5"?: number;
  "precision@10"?: number;
  "recall@1"?: number;
  "recall@3"?: number;
  "recall@5"?: number;
  "recall@10"?: number;
  "hit@1"?: number;
  "hit@3"?: number;
  "hit@5"?: number;
  "hit@10"?: number;
  "success@1"?: number;
  "success@5"?: number;
  "success@10"?: number;
  mean_spearman_rho?: number | null;
  mean_kendall_tau?: number | null;
}

export interface AlgorithmHumanRates {
  feedback_count: number;
  average_eas: number;
  approval_rate: number;
  would_use_rate: number;
  maybe_use_rate?: number;
  average_relevance?: number;
  average_originality?: number;
  average_clarity?: number;
  average_feasibility?: number;
  average_trust?: number;
  average_usefulness?: number;
}

export interface AlgorithmAnalysisItem {
  algorithm: string;
  human_rates: AlgorithmHumanRates;
  ranking_metrics: RankingSummary;
  sota_quality: Record<string, number>;
  observability: Record<string, number | null>;
}

export interface LiteratureReference {
  metric: string;
  citation: string;
  use: string;
}

export interface AlgorithmAnalysis {
  algorithms: AlgorithmAnalysisItem[];
  literature_suite: {
    overall: RankingSummary;
    by_algorithm: Record<string, RankingSummary>;
    references: LiteratureReference[];
  };
  engagement_funnel: { stage: string; count: number }[];
}

export interface InsightAnalysis {
  decision_distribution: Record<string, number>;
  would_use_distribution: Record<string, number>;
  cost_vs_quality: {
    algorithm: string;
    average_eas: number;
    avg_cost_per_run_usd: number;
    feedback_count: number;
  }[];
  survey_hit_at_1: { count: number; hit_at_1: number | null };
}

export interface ObservabilitySummary {
  overall: Record<string, number | null>;
  by_algorithm: Record<string, Record<string, number | null>>;
}

export interface HypothesisTestResult {
  test_name: string;
  statistic: number;
  p_value: number | null;
  effect_size: number | null;
  effect_size_name: string | null;
  group_a_mean: number;
  group_b_mean: number;
  group_a_n: number;
  group_b_n: number;
  significant_at_005: boolean;
  interpretation: string;
}

export interface GroupComparison {
  label_a: string;
  label_b: string;
  mann_whitney: HypothesisTestResult;
  welch_t_test: HypothesisTestResult;
  recommended_test: string;
}

export interface ResearchReport {
  generated_at: string;
  schema_version: string;
  sample: Record<string, number>;
  primary_outcomes: Record<string, number | null>;
  descriptive_statistics: RatingDistribution[];
  survey_outcomes: Record<string, number>;
  sota_quality: Record<string, number>;
  ranking_metrics: {
    overall: RankingSummary;
    by_algorithm?: Record<string, RankingSummary>;
    by_mode: Record<string, RankingSummary>;
    per_run: Record<string, unknown>[];
  };
  algorithm_analysis?: AlgorithmAnalysis | null;
  observability?: ObservabilitySummary | null;
  insight_analysis?: InsightAnalysis | null;
  experiment_analysis: {
    variants: Record<string, unknown>[];
    hypothesis_tests: Record<string, GroupComparison | HypothesisTestResult> | null;
  } | null;
  mode_comparison: Record<string, unknown>[];
  score_correlations: Record<string, unknown>[];
  rejection_summary: {
    rejection_count: number;
    rejection_rate: number;
    comments: string[];
    comment_count: number;
  };
  weekly_trends: WeeklyTrendPoint[];
  expert_label_analysis: Record<string, unknown> | null;
  methodology_notes: Record<string, unknown>;
}

export interface ExperimentVariantMetrics {
  variant: string;
  run_count: number;
  completed_count: number;
  feedback_count: number;
  average_eas: number;
  average_originality: number;
  approval_rate: number;
  would_use_rate: number;
}

export interface ExperimentDashboard {
  experiment_id: string;
  active: boolean;
  presentation_profile: string;
  variants: ExperimentVariantMetrics[];
}

export interface FeedbackResult {
  expectation_alignment_score: number;
}

export interface AdminOverview {
  generated_at: string;
  users: {
    total: number;
    active: number;
    admins: number;
    researchers: number;
  };
  runs: {
    total: number;
    completed: number;
    failed: number;
    completion_rate: number;
    failure_rate: number;
  };
  feedback_total: number;
  llm_cost_usd_total: number;
  system_status: string;
  health_checks: Record<string, string>;
  app_env: string;
}

export interface AdminSystemConfig {
  generated_at: string;
  environment: Record<string, string | number | boolean>;
}

export interface AdminModelSummary {
  provider: string;
  model: string;
  call_count: number;
  input_tokens: number;
  output_tokens: number;
  total_tokens: number;
  estimated_cost_usd: number;
}

export interface AdminModelEvaluation {
  generated_at: string;
  configured_models: {
    generation: string;
    embedding: string;
    embedding_dimensions: number;
  };
  aggregate: {
    call_count: number;
    total_tokens: number;
    estimated_cost_usd: number;
  };
  models: AdminModelSummary[];
  operations: Array<AdminModelSummary & { operation: string }>;
}

export interface AdminUserRecord {
  id: string;
  email?: string | null;
  full_name?: string | null;
  phone_number?: string | null;
  role: UserRole;
  is_active: boolean;
  is_admin: boolean;
  created_at?: string | null;
}

export interface AdminUserList {
  total: number;
  items: AdminUserRecord[];
}
