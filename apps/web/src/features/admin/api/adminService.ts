import type {
  AdminModelEvaluation,
  AdminOverview,
  AdminSystemConfig,
  AdminUserList,
  AdminUserRecord,
  UserRole,
  ValidationDashboard,
  ResearchReport,
} from "@/shared/types/api";
import type { IHttpClient } from "@/shared/api/httpClient";

export interface IAdminService {
  getOverview(token: string): Promise<AdminOverview>;
  getSystemConfig(token: string): Promise<AdminSystemConfig>;
  getModelEvaluation(token: string): Promise<AdminModelEvaluation>;
  getEvaluationDashboard(token: string): Promise<ValidationDashboard>;
  getResearchReport(token: string): Promise<ResearchReport>;
  listUsers(token: string, params?: { limit?: number; offset?: number }): Promise<AdminUserList>;
  updateUserRole(token: string, userId: string, role: UserRole): Promise<AdminUserRecord>;
}

export class AdminService implements IAdminService {
  private client: IHttpClient;

  constructor(client: IHttpClient) {
    this.client = client;
  }

  getOverview(token: string): Promise<AdminOverview> {
    return this.client.get("/api/v1/admin/overview", { token });
  }

  getSystemConfig(token: string): Promise<AdminSystemConfig> {
    return this.client.get("/api/v1/admin/system", { token });
  }

  getModelEvaluation(token: string): Promise<AdminModelEvaluation> {
    return this.client.get("/api/v1/admin/models", { token });
  }

  getEvaluationDashboard(token: string): Promise<ValidationDashboard> {
    return this.client.get("/api/v1/admin/evaluation/dashboard", { token });
  }

  getResearchReport(token: string): Promise<ResearchReport> {
    return this.client.get("/api/v1/admin/evaluation/research-report", { token });
  }

  listUsers(token: string, params?: { limit?: number; offset?: number }): Promise<AdminUserList> {
    const search = new URLSearchParams();
    if (params?.limit != null) {
      search.set("limit", String(params.limit));
    }
    if (params?.offset != null) {
      search.set("offset", String(params.offset));
    }
    const query = search.toString();
    const path = query ? `/api/v1/admin/users?${query}` : "/api/v1/admin/users";
    return this.client.get(path, { token });
  }

  updateUserRole(token: string, userId: string, role: UserRole): Promise<AdminUserRecord> {
    return this.client.patch(`/api/v1/admin/users/${userId}/role`, { role }, { token });
  }
}
