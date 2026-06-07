export interface AuthResponse {
  access_token: string;
  token_type: string;
  user_id: string;
  phone_number: string;
  email?: string | null;
  full_name?: string | null;
  whatsapp_opt_in?: boolean;
}

export interface OtpRequestResponse {
  message: string;
  expires_in_seconds: number;
  dev_code?: string | null;
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

export interface RecommendationDefaults {
  seed_topics?: string[];
  expected_output?: string | null;
  desired_depth?: string;
  avoid_real_user_experiments?: boolean;
  preferred_run_mode?: RunMode;
  max_article_age_years?: number;
}

export type RunMode = "quick" | "sota" | "exploratory" | "fggv";

export interface SotaAnchor {
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
  current_step?: string | null;
  topics?: string[];
  created_at?: string;
  finished_at?: string | null;
  estimated_cost_usd?: number;
  error_message?: string | null;
  recommendation_count?: number;
  usage?: RunUsageSummary | null;
}

export interface RunEvent {
  event_type: string;
  message: string;
  created_at?: string;
  level?: "info" | "warning" | "error";
}

export interface EvidencePaper {
  title?: string;
  year?: number;
  doi?: string;
  url?: string;
  why_relevant?: string;
  retrieval_source?: string;
  citation_count?: number;
  venue?: string;
  abstract?: string;
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
}

export interface SourceDocument {
  title?: string;
  year?: number;
  source?: string;
  url?: string;
  doi?: string;
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
}

export interface FeedbackResult {
  expectation_alignment_score: number;
}
