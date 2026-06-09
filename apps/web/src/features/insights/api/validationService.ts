import type { ResearchReport, ValidationDashboard } from "@/shared/types/api";
import type { IHttpClient } from "@/shared/api/httpClient";

export interface IValidationService {
  getDashboard(token: string): Promise<ValidationDashboard>;
  getResearchReport(token: string): Promise<ResearchReport>;
}

export class ValidationService implements IValidationService {
  private client: IHttpClient;

  constructor(client: IHttpClient) {
    this.client = client;
  }

  getDashboard(token: string): Promise<ValidationDashboard> {
    return this.client.get("/api/v1/validation/dashboard", { token });
  }

  getResearchReport(token: string): Promise<ResearchReport> {
    return this.client.get("/api/v1/validation/research-report", { token });
  }
}
