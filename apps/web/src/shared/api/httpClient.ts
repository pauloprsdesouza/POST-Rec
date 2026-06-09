import { env } from "@/shared/config/env";
import { parseHttpErrorDetail } from "./errors";

export interface RequestOptions {
  token?: string | null;
}

export class HttpError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "HttpError";
    this.status = status;
  }
}

export interface IHttpClient {
  get<T>(path: string, options?: RequestOptions): Promise<T>;
  post<T>(path: string, body: unknown, options?: RequestOptions): Promise<T>;
  put<T>(path: string, body: unknown, options?: RequestOptions): Promise<T>;
}

export class HttpClient implements IHttpClient {
  private baseUrl: string;

  constructor(baseUrl: string = env.apiBaseUrl) {
    this.baseUrl = baseUrl;
  }

  private headers(token?: string | null): HeadersInit {
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
    };
    if (token) {
      headers.Authorization = `Bearer ${token}`;
    }
    return headers;
  }

  private async parse<T>(response: Response): Promise<T> {
    if (!response.ok) {
      let detail = response.statusText;
      try {
        const payload = await response.json();
        detail = parseHttpErrorDetail(payload, detail);
      } catch {
        // ignore JSON parse errors
      }
      throw new HttpError(detail, response.status);
    }
    if (response.status === 204) {
      return undefined as T;
    }
    return response.json() as Promise<T>;
  }

  async get<T>(path: string, options: RequestOptions = {}): Promise<T> {
    const response = await fetch(`${this.baseUrl}${path}`, {
      headers: this.headers(options.token),
    });
    return this.parse<T>(response);
  }

  async post<T>(path: string, body: unknown, options: RequestOptions = {}): Promise<T> {
    const response = await fetch(`${this.baseUrl}${path}`, {
      method: "POST",
      headers: this.headers(options.token),
      body: JSON.stringify(body),
    });
    return this.parse<T>(response);
  }

  async put<T>(path: string, body: unknown, options: RequestOptions = {}): Promise<T> {
    const response = await fetch(`${this.baseUrl}${path}`, {
      method: "PUT",
      headers: this.headers(options.token),
      body: JSON.stringify(body),
    });
    return this.parse<T>(response);
  }
}

export const httpClient = new HttpClient();
