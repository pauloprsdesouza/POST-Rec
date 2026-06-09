import type { UserProfile } from "@/shared/types/api";
import type { IHttpClient } from "@/shared/api/httpClient";

export interface IProfileService {
  getProfile(token: string): Promise<UserProfile>;
  updateProfile(token: string, profile: UserProfile): Promise<UserProfile>;
  createSessionProfile(
    token: string,
    payload: UserProfile & { user_id: string; session_id: string },
  ): Promise<unknown>;
}

export class ProfileService implements IProfileService {
  private client: IHttpClient;

  constructor(client: IHttpClient) {
    this.client = client;
  }

  getProfile(token: string): Promise<UserProfile> {
    return this.client.get("/api/v1/users/me/profile", { token });
  }

  updateProfile(token: string, profile: UserProfile): Promise<UserProfile> {
    return this.client.put("/api/v1/users/me/profile", profile, { token });
  }

  createSessionProfile(
    token: string,
    payload: UserProfile & { user_id: string; session_id: string },
  ): Promise<unknown> {
    return this.client.post("/api/v1/profiles", payload, { token });
  }
}
