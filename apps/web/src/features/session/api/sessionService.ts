import type { IHttpClient } from "@/shared/api/httpClient";

export interface ISessionService {
  createSession(token: string, userId: string): Promise<{ session_id: string }>;
  createConsent(token: string, userId: string, sessionId: string, accepted: boolean): Promise<unknown>;
  getConsentStatus(token: string): Promise<import("@/shared/types/api").UserConsentStatus>;
  submitSurvey(token: string, payload: Record<string, unknown>): Promise<unknown>;
}

export class SessionService implements ISessionService {
  private client: IHttpClient;

  constructor(client: IHttpClient) {
    this.client = client;
  }

  createSession(token: string, userId: string): Promise<{ session_id: string }> {
    return this.client.post("/api/v1/sessions", { user_id: userId }, { token });
  }

  createConsent(token: string, userId: string, sessionId: string, accepted: boolean): Promise<unknown> {
    return this.client.post(
      "/api/v1/consents",
      {
        user_id: userId,
        session_id: sessionId,
        consent_version: "v1.0",
        accepted,
      },
      { token },
    );
  }

  getConsentStatus(token: string): Promise<import("@/shared/types/api").UserConsentStatus> {
    return this.client.get("/api/v1/users/me/consent", { token });
  }

  submitSurvey(token: string, payload: Record<string, unknown>): Promise<unknown> {
    return this.client.post("/api/v1/session-final-surveys", payload, { token });
  }
}
