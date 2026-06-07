import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import i18n from "@/shared/i18n";
import { runService } from "@/shared/api";
import type { RecommendationRun } from "@/shared/types/api";
import { useAuth } from "@/features/auth/context/AuthContext";

interface RunsContextValue {
  runs: RecommendationRun[];
  loaded: boolean;
  loading: boolean;
  error: string | null;
  refreshRuns: () => Promise<void>;
  invalidateRuns: () => void;
  updateRun: (run: RecommendationRun) => void;
}

const RunsContext = createContext<RunsContextValue | undefined>(undefined);

export function RunsProvider({ children }: { children: ReactNode }) {
  const { accessToken } = useAuth();
  const [runs, setRuns] = useState<RecommendationRun[]>([]);
  const [loaded, setLoaded] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refreshRuns = useCallback(async () => {
    if (!accessToken) {
      return;
    }

    setLoading(true);
    try {
      const data = await runService.listMyRuns(accessToken);
      setRuns(data);
      setLoaded(true);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : i18n.t("common.couldNotLoadRuns"));
    } finally {
      setLoading(false);
    }
  }, [accessToken]);

  const invalidateRuns = useCallback(() => {
    setLoaded(false);
  }, []);

  const updateRun = useCallback((run: RecommendationRun) => {
    const runId = String(run.id);
    setRuns((current) => {
      const index = current.findIndex((item) => String(item.id) === runId);
      if (index < 0) {
        return current;
      }
      const next = [...current];
      next[index] = { ...next[index], ...run };
      return next;
    });
  }, []);

  useEffect(() => {
    setRuns([]);
    setLoaded(false);
    setError(null);
  }, [accessToken]);

  useEffect(() => {
    if (!accessToken) {
      return;
    }

    if (!loaded && !loading) {
      void refreshRuns();
    }
  }, [accessToken, loaded, loading, refreshRuns]);

  const value = useMemo(
    () => ({
      runs,
      loaded,
      loading,
      error,
      refreshRuns,
      invalidateRuns,
      updateRun,
    }),
    [runs, loaded, loading, error, refreshRuns, invalidateRuns, updateRun],
  );

  return <RunsContext.Provider value={value}>{children}</RunsContext.Provider>;
}

export function useRuns(): RunsContextValue {
  const context = useContext(RunsContext);
  if (!context) {
    throw new Error("useRuns must be used within RunsProvider");
  }
  return context;
}
