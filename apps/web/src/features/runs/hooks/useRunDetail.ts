import { useEffect, useState } from "react";

import i18n from "@/shared/i18n";
import { runService } from "@/shared/api";
import { openRunStream } from "@/features/runs/api/runStream";
import type { Recommendation, RecommendationRun, RunEvent, SourceDocument } from "@/shared/types/api";
import { sortRecommendationsByScore } from "@/features/runs/utils/recommendations";
import { getRunOutcome, type RunOutcome } from "@/features/runs/utils/runs";

const FALLBACK_POLL_MS = 5000;

interface UseRunDetailOptions {
  token: string;
  runId: string;
  onRunUpdate?: (run: RecommendationRun) => void;
}

export function useRunDetail({ token, runId, onRunUpdate }: UseRunDetailOptions) {
  const [run, setRun] = useState<RecommendationRun | null>(null);
  const [events, setEvents] = useState<RunEvent[]>([]);
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [refinementRecommendations, setRefinementRecommendations] = useState<Recommendation[]>([]);
  const [sources, setSources] = useState<SourceDocument[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loadingRun, setLoadingRun] = useState(true);
  const [loadingIdeas, setLoadingIdeas] = useState(false);
  const [activeIndex, setActiveIndex] = useState(0);
  const [usingFallbackPoll, setUsingFallbackPoll] = useState(false);

  useEffect(() => {
    if (!token || !runId) {
      return;
    }

    let active = true;
    let pollTimer: number | undefined;

    setRun(null);
    setEvents([]);
    setRecommendations([]);
    setRefinementRecommendations([]);
    setSources([]);
    setError(null);
    setLoadingRun(true);
    setLoadingIdeas(false);
    setActiveIndex(0);
    setUsingFallbackPoll(false);

    let latestRun: RecommendationRun | null = null;

    const applyRun = (data: RecommendationRun) => {
      if (!active) {
        return;
      }
      latestRun = data;
      setRun(data);
      onRunUpdate?.(data);
    };

    const loadRecommendations = async () => {
      setLoadingIdeas(true);
      try {
        const [recs, docs] = await Promise.all([
          runService.getRecommendations(token, runId),
          runService.getSourceDocuments(token, runId),
        ]);
        if (!active) {
          return;
        }
        setRecommendations(sortRecommendationsByScore(recs.filter((r) => r.status !== "needs_refinement")));
        setRefinementRecommendations(recs.filter((r) => r.status === "needs_refinement"));
        setSources(docs);
        setError(null);
      } catch (err) {
        if (active) {
          setError(
            err instanceof Error ? err.message : i18n.t("common.couldNotLoadRecommendations"),
          );
        }
      } finally {
        if (active) {
          setLoadingIdeas(false);
        }
      }
    };

    const stopPolling = () => {
      if (pollTimer) {
        window.clearInterval(pollTimer);
        pollTimer = undefined;
      }
    };

    const handleTerminalTransition = async (outcome: RunOutcome) => {
      if (outcome === "ready") {
        stopPolling();
        stream?.close();
        await loadRecommendations();
      } else if (outcome !== "in_progress") {
        stopPolling();
        stream?.close();
      }
    };

    const applyStreamPayload = (payload: { run: RecommendationRun; events: RunEvent[] }) => {
      applyRun(payload.run);
      setEvents(payload.events);
      setLoadingRun(false);
      setError(null);
    };

    const refreshFromApi = async () => {
      const [data, eventList] = await Promise.all([
        runService.getRun(token, runId),
        runService.getRunEvents(token, runId),
      ]);
      if (!active) {
        return null;
      }
      applyRun(data);
      setEvents(eventList);
      setLoadingRun(false);
      return data;
    };

    const startFallbackPolling = () => {
      if (!active || pollTimer) {
        return;
      }
      setUsingFallbackPoll(true);
      const poll = async () => {
        try {
          const data = await refreshFromApi();
          if (data) {
            await handleTerminalTransition(getRunOutcome(data));
          }
        } catch {
          // keep polling quietly
        }
      };
      void poll();
      pollTimer = window.setInterval(() => {
        void poll();
      }, FALLBACK_POLL_MS);
    };

    const stream = openRunStream(token, runId, {
      onUpdate: (payload) => {
        if (!active) {
          return;
        }
        applyStreamPayload(payload);
        void handleTerminalTransition(getRunOutcome(payload.run));
      },
      onComplete: () => {
        if (!active) {
          return;
        }
        void (async () => {
          try {
            const streamedRun = latestRun;
            if (streamedRun && getRunOutcome(streamedRun) === "ready") {
              await handleTerminalTransition("ready");
              return;
            }
            const refreshedRun = await refreshFromApi();
            if (refreshedRun) {
              await handleTerminalTransition(getRunOutcome(refreshedRun));
            }
          } catch {
            startFallbackPolling();
          }
        })();
      },
      onError: () => {
        if (active) {
          startFallbackPolling();
        }
      },
    });

    return () => {
      active = false;
      stream?.close();
      stopPolling();
    };
  }, [token, runId, onRunUpdate]);

  const outcome = run ? getRunOutcome(run) : null;
  const loading =
    loadingRun || (outcome === "ready" && loadingIdeas && recommendations.length === 0);

  return {
    run,
    events,
    recommendations,
    refinementRecommendations,
    sources,
    error,
    loading,
    outcome,
    activeIndex,
    setActiveIndex,
    usingFallbackPoll,
  };
};
