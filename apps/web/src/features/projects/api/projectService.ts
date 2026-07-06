import { env } from "@/shared/config/env";
import { HttpError } from "@/shared/api/httpClient";
import { parseHttpErrorDetail } from "@/shared/api/errors";
import type { IHttpClient } from "@/shared/api/httpClient";
import type { ProjectListItem, ProjectTaskStatus, ResearchProject } from "@/shared/types/api";

export interface IProjectService {
  listProjects(token: string, limit?: number): Promise<ProjectListItem[]>;
  getProject(token: string, projectId: string): Promise<ResearchProject>;
  getProjectByRecommendation(token: string, recommendationId: string): Promise<ResearchProject | null>;
  createProject(token: string, recommendationId: string, locale?: string): Promise<ResearchProject>;
  updateTask(
    token: string,
    projectId: string,
    taskId: string,
    payload: { status?: ProjectTaskStatus; user_notes?: string | null },
  ): Promise<{ id: string; status: string; user_notes?: string | null; completed_at?: string | null }>;
  exportMarkdown(token: string, projectId: string): Promise<string>;
}

export class ProjectService implements IProjectService {
  private client: IHttpClient;

  constructor(client: IHttpClient) {
    this.client = client;
  }

  listProjects(token: string, limit = 50): Promise<ProjectListItem[]> {
    return this.client.get(`/api/v1/projects?limit=${limit}`, { token });
  }

  getProject(token: string, projectId: string): Promise<ResearchProject> {
    return this.client.get(`/api/v1/projects/${projectId}`, { token });
  }

  getProjectByRecommendation(token: string, recommendationId: string): Promise<ResearchProject | null> {
    return this.client.get(`/api/v1/projects/by-recommendation/${recommendationId}`, { token });
  }

  createProject(token: string, recommendationId: string, locale = "en-US"): Promise<ResearchProject> {
    return this.client.post(
      `/api/v1/projects?locale=${encodeURIComponent(locale)}`,
      { recommendation_id: recommendationId },
      { token },
    );
  }

  updateTask(
    token: string,
    projectId: string,
    taskId: string,
    payload: { status?: ProjectTaskStatus; user_notes?: string | null },
  ): Promise<{ id: string; status: string; user_notes?: string | null; completed_at?: string | null }> {
    return this.client.patch(`/api/v1/projects/${projectId}/tasks/${taskId}`, payload, { token });
  }

  async exportMarkdown(token: string, projectId: string): Promise<string> {
    const response = await fetch(
      `${env.apiBaseUrl}/api/v1/projects/${projectId}/export?format=markdown`,
      {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      },
    );
    if (!response.ok) {
      let detail = response.statusText;
      try {
        const payload = await response.json();
        detail = parseHttpErrorDetail(payload, detail);
      } catch {
        // ignore
      }
      throw new HttpError(detail, response.status);
    }
    return response.text();
  }
}

import { httpClient } from "@/shared/api/httpClient";

export const projectService = new ProjectService(httpClient);
