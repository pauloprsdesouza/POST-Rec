import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  type ReactNode,
} from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";

import { runService } from "@/features/runs/api/runService";
import i18n from "@/shared/i18n";
import { queryKeys } from "@/shared/query/keys";
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
  const queryClient = useQueryClient();

  const { data, isLoading, isFetched, error, refetch } = useQuery({
    queryKey: queryKeys.runs(accessToken),
    queryFn: () => runService.listMyRuns(accessToken!),
    enabled: Boolean(accessToken),
    staleTime: 30_000,
  });

  const runs = data ?? [];

  const refreshRuns = useCallback(async () => {
    if (!accessToken) {
      return;
    }
    await refetch();
  }, [accessToken, refetch]);

  const invalidateRuns = useCallback(() => {
    if (!accessToken) {
      return;
    }
    void queryClient.invalidateQueries({ queryKey: queryKeys.runs(accessToken) });
  }, [accessToken, queryClient]);

  const updateRun = useCallback(
    (run: RecommendationRun) => {
      if (!accessToken) {
        return;
      }
      const runId = String(run.id);
      queryClient.setQueryData<RecommendationRun[]>(queryKeys.runs(accessToken), (current) => {
        if (!current) {
          return current;
        }
        const index = current.findIndex((item) => String(item.id) === runId);
        if (index < 0) {
          return current;
        }
        const next = [...current];
        next[index] = { ...next[index], ...run };
        return next;
      });
    },
    [accessToken, queryClient],
  );

  const value = useMemo(
    () => ({
      runs,
      loaded: isFetched,
      loading: isLoading,
      error: error instanceof Error ? error.message : error ? i18n.t("common.couldNotLoadRuns") : null,
      refreshRuns,
      invalidateRuns,
      updateRun,
    }),
    [runs, isFetched, isLoading, error, refreshRuns, invalidateRuns, updateRun],
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
