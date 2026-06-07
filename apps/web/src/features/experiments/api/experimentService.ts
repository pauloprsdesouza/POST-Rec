import type { IHttpClient } from "@/shared/api/httpClient";

export interface ExperimentEnrollment {
  experiment_active: boolean;
  experiment_id?: string | null;
  enrolled: boolean;
  presentation_profile: "standard" | "blind";
  control_mode: string;
  treatment_mode: string;
}

export interface IExperimentService {
  getEnrollment(token: string): Promise<ExperimentEnrollment>;
}

export class ExperimentService implements IExperimentService {
  private client: IHttpClient;

  constructor(client: IHttpClient) {
    this.client = client;
  }

  getEnrollment(token: string): Promise<ExperimentEnrollment> {
    return this.client.get<ExperimentEnrollment>("/api/v1/experiments/enrollment", { token });
  }
}
