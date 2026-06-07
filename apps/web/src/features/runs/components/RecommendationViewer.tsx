import { useCallback, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

import type { Recommendation, RecommendationRun, SourceDocument } from "@/shared/types/api";
import { isBlindRun } from "@/features/experiments/utils/blindRun";

import { FeedbackProgress } from "./FeedbackProgress";
import { IdeaCarousel } from "./IdeaCarousel";
import { RatingCelebration } from "./RatingCelebration";
import { RecommendationDetail } from "./RecommendationDetail";
import { RefinementPanel } from "./RefinementPanel";
import { RunCompleteBanner } from "./RunCompleteBanner";
import { SessionQuickFeedback } from "./SessionQuickFeedback";
import { SourceCatalog } from "./EvidenceList";
import { RunUsagePanel } from "./RunUsagePanel";
import { InlineAlert } from "@/shared/ui/InlineAlert";

interface RecommendationViewerProps {
  token: string;
  runId: string;
  sessionId: string | null;
  run: RecommendationRun;
  recommendations: Recommendation[];
  refinementRecommendations?: Recommendation[];
  sources: SourceDocument[];
  activeIndex: number;
  onActiveIndexChange: (index: number) => void;
  error?: string | null;
  onFeedbackChange?: (ratedCount: number, total: number) => void;
}

function buildInitialRatings(recommendations: Recommendation[]): Record<string, number> {
  const ratings: Record<string, number> = {};
  for (const recommendation of recommendations) {
    const score = recommendation.user_feedback?.relevance_score;
    if (typeof score === "number") {
      ratings[recommendation.id] = score;
    }
  }
  return ratings;
}

function findNextIndex(
  recommendations: Recommendation[],
  skipIds: Set<string>,
  ratedIds: Set<string>,
  from: number,
): number {
  for (let i = from; i < recommendations.length; i += 1) {
    const id = recommendations[i].id;
    if (!ratedIds.has(id) && !skipIds.has(id)) {
      return i;
    }
  }
  for (let i = 0; i < from; i += 1) {
    const id = recommendations[i].id;
    if (!ratedIds.has(id) && !skipIds.has(id)) {
      return i;
    }
  }
  return -1;
}

export function RecommendationViewer({
  token,
  runId,
  sessionId,
  run,
  recommendations,
  refinementRecommendations = [],
  sources,
  activeIndex,
  onActiveIndexChange,
  onFeedbackChange,
  error,
}: RecommendationViewerProps) {
  const { t } = useTranslation();
  const [ratings, setRatings] = useState<Record<string, number>>(() => buildInitialRatings(recommendations));
  const [skippedIds, setSkippedIds] = useState<Set<string>>(() => new Set());
  const [celebration, setCelebration] = useState<"first" | "all" | null>(null);

  useEffect(() => {
    const initialRatings = buildInitialRatings(recommendations);
    setRatings(initialRatings);
    const ratedCount = Object.keys(initialRatings).length;
    if (ratedCount > 0) {
      onFeedbackChange?.(ratedCount, recommendations.length);
    }
  }, [onFeedbackChange, recommendations]);

  const scheduleAdvance = useCallback(
    (currentId: string, rated: Record<string, number>, skipped: Set<string>) => {
      const ratedIds = new Set(Object.keys(rated));
      const currentIdx = recommendations.findIndex((r) => r.id === currentId);
      const nextIdx = findNextIndex(recommendations, skipped, ratedIds, currentIdx + 1);
      if (nextIdx >= 0 && nextIdx !== currentIdx) {
        window.setTimeout(() => onActiveIndexChange(nextIdx), 400);
      }
    },
    [onActiveIndexChange, recommendations],
  );

  const handleRated = useCallback(
    (recommendationId: string, rating: number, isFirstRating: boolean) => {
      setRatings((prev) => {
        const next = { ...prev, [recommendationId]: rating };
        const nextCount = Object.keys(next).length;
        const total = recommendations.length;

        if (isFirstRating && nextCount === 1) {
          setCelebration("first");
        } else if (nextCount >= total && total > 0) {
          setCelebration("all");
        }

        if (isFirstRating) {
          scheduleAdvance(recommendationId, next, skippedIds);
        }
        onFeedbackChange?.(nextCount, recommendations.length);
        return next;
      });
    },
    [onFeedbackChange, recommendations.length, scheduleAdvance, skippedIds],
  );

  const handleSkip = useCallback(() => {
    const current = recommendations[activeIndex];
    if (!current) {
      return;
    }
    const nextSkipped = new Set(skippedIds);
    nextSkipped.add(current.id);
    setSkippedIds(nextSkipped);
    scheduleAdvance(current.id, ratings, nextSkipped);
  }, [activeIndex, ratings, recommendations, scheduleAdvance, skippedIds]);

  const jumpToUnrated = useCallback(() => {
    const ratedIds = new Set(Object.keys(ratings));
    const nextIdx = findNextIndex(recommendations, skippedIds, ratedIds, 0);
    if (nextIdx >= 0) {
      onActiveIndexChange(nextIdx);
    }
  }, [onActiveIndexChange, ratings, recommendations, skippedIds]);

  if (error) {
    return <InlineAlert variant="danger">{error}</InlineAlert>;
  }

  if (!recommendations.length && !refinementRecommendations.length) {
    return <p className="evidence-empty">{t("runs.noRecommendations")}</p>;
  }

  const active = recommendations[activeIndex];
  const blind = isBlindRun(run);
  const ratedIds = new Set(Object.keys(ratings));
  const ratedCount = ratedIds.size;
  const showSessionFeedback = ratedCount > 0;
  const remaining = Math.max(recommendations.length - ratedCount, 0);

  const celebrationMessage =
    celebration === "first"
      ? t("ideas.celebrationFirst", { remaining: remaining > 0 ? remaining : recommendations.length - 1 })
      : celebration === "all"
        ? t("ideas.celebrationAll")
        : "";

  return (
    <div className="idea-viewer">
      <RatingCelebration
        kind={celebration}
        message={celebrationMessage}
        onDismiss={() => setCelebration(null)}
      />

      <RunCompleteBanner ideaCount={recommendations.length} ratedCount={ratedCount} />

      {recommendations.length > 1 ? (
        <FeedbackProgress
          ratedCount={ratedCount}
          total={recommendations.length}
          onSkip={handleSkip}
          onJumpToUnrated={ratedCount < recommendations.length ? jumpToUnrated : undefined}
        />
      ) : null}

      {!blind ? <RunUsagePanel run={run} /> : null}

      {recommendations.length ? (
        <IdeaCarousel
          items={recommendations}
          activeIndex={activeIndex}
          ratedIds={ratedIds}
          skippedIds={skippedIds}
          onSelect={onActiveIndexChange}
        />
      ) : null}

      {active ? (
        <RecommendationDetail
          key={active.id}
          recommendation={active}
          index={activeIndex + 1}
          total={recommendations.length}
          runId={runId}
          sessionId={sessionId}
          token={token}
          sources={sources}
          blind={blind}
          initialRating={ratings[active.id] ?? null}
          onRated={handleRated}
          onSkip={recommendations.length > 1 ? handleSkip : undefined}
        />
      ) : null}

      <RefinementPanel items={refinementRecommendations} />

      {showSessionFeedback ? (
        <aside className="feedback-footer">
          <p className="feedback-footer__title">{t("survey.quickPrompt")}</p>
          <SessionQuickFeedback runId={runId} visible compact />
        </aside>
      ) : null}

      {sources.length > 0 ? (
        <details className="idea-sources-all">
          <summary>{t("runs.allSources", { count: sources.length })}</summary>
          <SourceCatalog sources={sources} />
        </details>
      ) : null}
    </div>
  );
}
