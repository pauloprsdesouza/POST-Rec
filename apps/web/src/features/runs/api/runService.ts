import type {
  FeedbackResult,
  Recommendation,
  RecommendationRun,
  RunEvent,
  SourceDocument,
} from "@/shared/types/api";
import type { IHttpClient } from "@/shared/api/httpClient";

export interface RunCleanupPreview {
  learned_topics: string[];
}

export interface RunActionResult {
  status: string;
  message: string;
}

export interface RunCleanupPayload {
  remove_learned_topics?: string[];
}

export interface IRunService {
  listMyRuns(token: string, limit?: number, query?: string): Promise<RecommendationRun[]>;
  getRun(token: string, runId: string): Promise<RecommendationRun>;
  getRunEvents(token: string, runId: string): Promise<RunEvent[]>;
  getRecommendations(token: string, runId: string, includeRefinement?: boolean): Promise<Recommendation[]>;
  getSourceDocuments(token: string, runId: string): Promise<SourceDocument[]>;
  createExpectation(token: string, payload: Record<string, unknown>): Promise<{ id: string }>;
  createRun(token: string, payload: Record<string, unknown>): Promise<{ run_id: string }>;
  submitFeedback(token: string, recommendationId: string, payload: Record<string, unknown>): Promise<FeedbackResult>;
  cancelRun(token: string, runId: string): Promise<RunActionResult>;
  retryRun(token: string, runId: string): Promise<RunActionResult>;
  getRunCleanupPreview(token: string, runId: string): Promise<RunCleanupPreview>;
  archiveRun(token: string, runId: string, payload?: RunCleanupPayload): Promise<RunActionResult>;
  removeRun(token: string, runId: string, payload?: RunCleanupPayload): Promise<RunActionResult>;
}

export class RunService implements IRunService {
  private client: IHttpClient;

  constructor(client: IHttpClient) {
    this.client = client;
  }

  listMyRuns(token: string, limit = 50, query?: string): Promise<RecommendationRun[]> {
    const params = new URLSearchParams({ limit: String(limit) });
    const trimmed = query?.trim();
    if (trimmed) {
      params.set("q", trimmed);
    }
    return this.client.get(`/api/v1/users/me/recommendation-runs?${params.toString()}`, { token });
  }

  getRun(token: string, runId: string): Promise<RecommendationRun> {
    return this.client.get(`/api/v1/recommendation-runs/${runId}`, { token });
  }

  getRunEvents(token: string, runId: string): Promise<RunEvent[]> {
    return this.client.get(`/api/v1/recommendation-runs/${runId}/events`, { token });
  }

  getRecommendations(token: string, runId: string, includeRefinement = true): Promise<Recommendation[]> {
    const query = includeRefinement ? "?include_refinement=true" : "";
    return this.client.get(`/api/v1/recommendation-runs/${runId}/recommendations${query}`, { token });
  }

  getSourceDocuments(token: string, runId: string): Promise<SourceDocument[]> {
    return this.client.get(`/api/v1/recommendation-runs/${runId}/source-documents`, { token });
  }

  createExpectation(token: string, payload: Record<string, unknown>): Promise<{ id: string }> {
    return this.client.post("/api/v1/expectations", payload, { token });
  }

  createRun(token: string, payload: Record<string, unknown>): Promise<{ run_id: string }> {
    return this.client.post("/api/v1/recommendation-runs", payload, { token });
  }

  submitFeedback(
    token: string,
    recommendationId: string,
    payload: Record<string, unknown>,
  ): Promise<FeedbackResult> {
    return this.client.post(`/api/v1/recommendations/${recommendationId}/feedback`, payload, { token });
  }

  cancelRun(token: string, runId: string): Promise<RunActionResult> {
    return this.client.post(`/api/v1/recommendation-runs/${runId}/cancel`, {}, { token });
  }

  retryRun(token: string, runId: string): Promise<RunActionResult> {
    return this.client.post(`/api/v1/recommendation-runs/${runId}/retry`, {}, { token });
  }

  getRunCleanupPreview(token: string, runId: string): Promise<RunCleanupPreview> {
    return this.client.get(`/api/v1/recommendation-runs/${runId}/cleanup-preview`, { token });
  }

  archiveRun(token: string, runId: string, payload: RunCleanupPayload = {}): Promise<RunActionResult> {
    return this.client.post(`/api/v1/recommendation-runs/${runId}/archive`, payload, { token });
  }

  removeRun(token: string, runId: string, payload: RunCleanupPayload = {}): Promise<RunActionResult> {
    return this.client.post(`/api/v1/recommendation-runs/${runId}/remove`, payload, { token });
  }
}
