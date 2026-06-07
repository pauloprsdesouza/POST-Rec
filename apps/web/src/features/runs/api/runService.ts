import type {
  FeedbackResult,
  Recommendation,
  RecommendationRun,
  RunEvent,
  SourceDocument,
} from "@/shared/types/api";
import type { IHttpClient } from "@/shared/api/httpClient";

export interface IRunService {
  listMyRuns(token: string, limit?: number): Promise<RecommendationRun[]>;
  getRun(token: string, runId: string): Promise<RecommendationRun>;
  getRunEvents(token: string, runId: string): Promise<RunEvent[]>;
  getRecommendations(token: string, runId: string, includeRefinement?: boolean): Promise<Recommendation[]>;
  getSourceDocuments(token: string, runId: string): Promise<SourceDocument[]>;
  createExpectation(token: string, payload: Record<string, unknown>): Promise<{ id: string }>;
  createRun(token: string, payload: Record<string, unknown>): Promise<{ run_id: string }>;
  submitFeedback(token: string, recommendationId: string, payload: Record<string, unknown>): Promise<FeedbackResult>;
}

export class RunService implements IRunService {
  private client: IHttpClient;

  constructor(client: IHttpClient) {
    this.client = client;
  }

  listMyRuns(token: string, limit = 50): Promise<RecommendationRun[]> {
    return this.client.get(`/api/v1/users/me/recommendation-runs?limit=${limit}`, { token });
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
}
