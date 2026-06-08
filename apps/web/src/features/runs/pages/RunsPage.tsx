import { useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link, Navigate } from "react-router-dom";

import { RunListCard } from "@/features/runs/components/RunListCard";
import { RunSection } from "@/features/runs/components/RunSection";
import { RunsEmptyHero } from "@/features/runs/components/RunsEmptyHero";
import { RunsListSkeleton } from "@/features/runs/components/RunsListSkeleton";
import { RunsSearchBar } from "@/features/runs/components/RunsSearchBar";
import { RunsStatsStrip, type RunsFilter } from "@/features/runs/components/RunsStatsStrip";
import { PageHeader } from "@/shared/ui/PageHeader";
import { InlineAlert } from "@/shared/ui/InlineAlert";
import { useAuth } from "@/features/auth/context/AuthContext";
import { useRuns } from "@/features/runs/context/RunsContext";
import { runService } from "@/shared/api";
import type { RecommendationRun } from "@/shared/types/api";
import { groupRuns } from "@/features/runs/utils/runs";

const SEARCH_DEBOUNCE_MS = 300;
const MIN_SEARCH_LENGTH = 2;

function filterRuns(
  filter: RunsFilter,
  groups: ReturnType<typeof groupRuns>,
): { completed: RecommendationRun[]; active: RecommendationRun[]; other: RecommendationRun[] } {
  if (filter === "ready") {
    return { completed: groups.completed, active: [], other: [] };
  }
  if (filter === "active") {
    return { completed: [], active: groups.active, other: [] };
  }
  return groups;
}

export function RunsPage() {
  const { t } = useTranslation();
  const { accessToken } = useAuth();
  const { runs, loaded, loading, error } = useRuns();
  const [filter, setFilter] = useState<RunsFilter>("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [debouncedQuery, setDebouncedQuery] = useState("");
  const [searchResults, setSearchResults] = useState<RecommendationRun[] | null>(null);
  const [searchLoading, setSearchLoading] = useState(false);
  const [searchError, setSearchError] = useState<string | null>(null);

  useEffect(() => {
    const timer = window.setTimeout(() => setDebouncedQuery(searchQuery.trim()), SEARCH_DEBOUNCE_MS);
    return () => window.clearTimeout(timer);
  }, [searchQuery]);

  useEffect(() => {
    if (!accessToken || debouncedQuery.length < MIN_SEARCH_LENGTH) {
      setSearchResults(null);
      setSearchLoading(false);
      setSearchError(null);
      return;
    }

    let cancelled = false;
    setSearchLoading(true);
    setSearchError(null);

    void runService
      .listMyRuns(accessToken, 100, debouncedQuery)
      .then((results) => {
        if (!cancelled) {
          setSearchResults(results);
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setSearchError(err instanceof Error ? err.message : t("runs.searchError"));
          setSearchResults([]);
        }
      })
      .finally(() => {
        if (!cancelled) {
          setSearchLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [accessToken, debouncedQuery, t]);

  const isSearching = debouncedQuery.length >= MIN_SEARCH_LENGTH;
  const groups = useMemo(() => groupRuns(runs), [runs]);
  const { active, completed, other } = useMemo(() => filterRuns(filter, groups), [filter, groups]);
  const searchCount = searchResults?.length ?? 0;

  const clearSearch = () => {
    setSearchQuery("");
    setDebouncedQuery("");
    setSearchResults(null);
    setSearchError(null);
  };

  if (!accessToken) {
    return null;
  }

  if (!loaded && loading) {
    return (
      <div className="page-shell page-shell--list runs-page">
        <RunsListSkeleton />
      </div>
    );
  }

  if (error && !runs.length) {
    return (
      <div className="page-shell page-shell--list runs-page">
        <InlineAlert variant="danger">{error}</InlineAlert>
      </div>
    );
  }

  if (!runs.length) {
    return (
      <div className="page-shell page-shell--list runs-page">
        <RunsEmptyHero />
      </div>
    );
  }

  return (
    <div className="page-shell page-shell--list runs-page">
      <div className="page-stack">
        <header className="page-stack__block">
          <PageHeader
            title={t("runs.title")}
            subtitle={t("runs.subtitleStats", {
              total: runs.length,
              active: groups.active.length,
              completed: groups.completed.length,
            })}
            action={
              <Link to="/runs/new" className="btn btn-primary" data-coach="coach-runs-new-run">
                {t("common.newRun")}
              </Link>
            }
          />
          <RunsSearchBar
            value={searchQuery}
            loading={searchLoading}
            onChange={setSearchQuery}
            onClear={clearSearch}
          />
          {!isSearching ? (
            <div data-coach="coach-runs-filters">
              <RunsStatsStrip
                total={runs.length}
                active={groups.active.length}
                ready={groups.completed.length}
                filter={filter}
                onFilterChange={setFilter}
              />
            </div>
          ) : null}
        </header>

        {error ? <InlineAlert variant="danger">{error}</InlineAlert> : null}
        {searchError ? <InlineAlert variant="danger">{searchError}</InlineAlert> : null}

        {isSearching ? (
          <div className="page-stack page-stack--tight">
            <p className="runs-page__search-meta">
              {searchLoading
                ? t("runs.searching")
                : t("runs.searchResults", { count: searchCount, query: debouncedQuery })}
            </p>
            {!searchLoading && searchCount === 0 ? (
              <p className="inline-meta runs-page__empty-filter">{t("runs.searchEmpty")}</p>
            ) : null}
            <div className="run-section__list">
              {(searchResults ?? []).map((run) => (
                <RunListCard key={run.id} run={run} recommendationCount={run.recommendation_count} showSearchMeta />
              ))}
            </div>
          </div>
        ) : (
          <>
            {filter === "ready" && completed.length === 0 ? (
              <p className="inline-meta runs-page__empty-filter">{t("runs.filterEmptyReady")}</p>
            ) : null}
            {filter === "active" && active.length === 0 ? (
              <p className="inline-meta runs-page__empty-filter">{t("runs.filterEmptyActive")}</p>
            ) : null}

            <div className="page-stack page-stack--tight">
              <RunSection
                title={t("runs.sectionReady")}
                description={t("runs.sectionReadyDesc")}
                count={completed.length}
                variant="ready"
                dataCoach="coach-runs-ready"
              >
                {completed.map((run) => (
                  <RunListCard key={run.id} run={run} recommendationCount={run.recommendation_count} />
                ))}
              </RunSection>

              <RunSection
                title={t("runs.sectionInProgress")}
                description={t("runs.sectionInProgressDesc")}
                count={active.length}
                variant="in_progress"
              >
                {active.map((run) => (
                  <RunListCard key={run.id} run={run} recommendationCount={run.recommendation_count} />
                ))}
              </RunSection>

              <RunSection
                title={t("runs.sectionOtherCount", { count: other.length })}
                description={t("runs.sectionOtherDesc")}
                count={other.length}
                variant="other"
              >
                {other.map((run) => (
                  <RunListCard key={run.id} run={run} recommendationCount={run.recommendation_count} />
                ))}
              </RunSection>
            </div>
          </>
        )}
      </div>

      <div className="runs-page__mobile-cta d-lg-none">
        <Link to="/runs/new" className="btn btn-primary btn-lg w-100">
          {t("common.newRun")}
        </Link>
      </div>
    </div>
  );
}

export function RecommendationsRedirect() {
  const { selectedRunId } = useAuth();

  if (selectedRunId) {
    return <Navigate to={`/runs/${selectedRunId}`} replace />;
  }
  return <Navigate to="/runs" replace />;
}
