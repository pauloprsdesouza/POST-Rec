import { env } from "../../config/env";
import type { RecommendationRun, RunEvent } from "../../types/api";

export interface RunStreamPayload {
  run: RecommendationRun;
  events: RunEvent[];
}

export interface RunStreamHandlers {
  onUpdate: (payload: RunStreamPayload) => void;
  onComplete: () => void;
  onError: () => void;
}

export function openRunStream(
  token: string,
  runId: string,
  handlers: RunStreamHandlers,
): EventSource {
  const url = `${env.apiBaseUrl}/api/v1/recommendation-runs/${runId}/stream?token=${encodeURIComponent(token)}`;
  const source = new EventSource(url);

  source.addEventListener("run_update", (event) => {
    try {
      const payload = JSON.parse((event as MessageEvent<string>).data) as RunStreamPayload;
      handlers.onUpdate(payload);
    } catch {
      handlers.onError();
    }
  });

  source.addEventListener("complete", () => {
    source.close();
    handlers.onComplete();
  });

  source.onerror = () => {
    source.close();
    handlers.onError();
  };

  return source;
}
