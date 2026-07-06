import type { FormEvent } from "react";
import { useEffect, useState } from "react";
import { Button } from "react-bootstrap";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";

import {
  mergeRecommendationDefaults,
  RecommendationPreferencesForm,
} from "@/features/profile/components/RecommendationPreferencesForm";
import { RunModeSelector } from "@/features/runs/components/RunModeSelector";
import { GettingStartedSteps } from "@/features/runs/components/GettingStartedSteps";
import { PageHeader } from "@/shared/ui/PageHeader";
import { PageShell } from "@/shared/ui/PageShell";
import { StickyFooter } from "@/shared/ui/StickyFooter";
import { Surface } from "@/shared/ui/Surface";
import { InlineAlert } from "@/shared/ui/InlineAlert";
import { LoadingSpinner } from "@/shared/ui/LoadingSpinner";
import { useAuth } from "@/features/auth/context/AuthContext";
import { useRuns } from "@/features/runs/context/RunsContext";
import i18n from "@/shared/i18n";
import { profileService, runService, sessionService } from "@/shared/api";
import { getErrorMessage } from "@/shared/api/errors";
import type { RecommendationDefaults, RunModeSelection, UserProfile } from "@/shared/types/api";

export function NewRunPage() {
  const { t } = useTranslation();
  const { accessToken, user, sessionId, setSessionId, setSelectedRunId } = useAuth();
  const { invalidateRuns } = useRuns();
  const navigate = useNavigate();
  const [profile, setProfile] = useState<UserProfile>({});
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [researchArea, setResearchArea] = useState("");
  const [preferences, setPreferences] = useState<RecommendationDefaults>(
    mergeRecommendationDefaults(null, null, ""),
  );
  const [runMode, setRunMode] = useState<RunModeSelection>("auto");

  useEffect(() => {
    if (!accessToken) {
      return;
    }
    profileService
      .getProfile(accessToken)
      .then((data) => {
        setProfile(data);
        setResearchArea(data.research_area ?? "");
        const preferredMode = data.recommendation_defaults?.preferred_run_mode;
        if (
          preferredMode === "auto" ||
          preferredMode === "quick" ||
          preferredMode === "sota" ||
          preferredMode === "exploratory" ||
          preferredMode === "fggv"
        ) {
          setRunMode(preferredMode);
        }
        setPreferences(
          mergeRecommendationDefaults(
            data.recommendation_defaults,
            data.learned_topics,
            i18n.t("preferences.defaultExpectedOutput"),
          ),
        );
      })
      .finally(() => setLoading(false));
  }, [accessToken]);

  const handleSubmit = async (event: FormEvent, formDefaults: RecommendationDefaults) => {
    event.preventDefault();
    if (!accessToken || !user) {
      return;
    }

    const topicList = formDefaults.seed_topics ?? [];
    if (topicList.length === 0) {
      setError(t("newRun.seedTopicRequired"));
      return;
    }

    setSubmitting(true);
    setError(null);

    try {
      let activeSessionId = sessionId;
      if (!activeSessionId) {
        const session = await sessionService.createSession(accessToken, user.userId);
        activeSessionId = session.session_id;
        setSessionId(activeSessionId);
      }

      const expectation = await runService.createExpectation(accessToken, {
        session_id: activeSessionId,
        user_id: user.userId,
        research_area: researchArea,
        seed_topics: topicList,
        expected_output: formDefaults.expected_output ?? undefined,
        desired_depth: formDefaults.desired_depth ?? "medium",
        publication_goal: "conference_or_journal",
      });

      const run = await runService.createRun(accessToken, {
        session_id: activeSessionId,
        expectation_id: expectation.id,
        topics: topicList,
        mode: runMode,
        max_papers: 50,
        max_recommendations: 5,
        constraints: {
          max_article_age_years: formDefaults.max_article_age_years ?? 5,
        },
      });

      setSelectedRunId(run.run_id);
      invalidateRuns();
      navigate(`/runs/${run.run_id}`);
    } catch (err) {
      setError(getErrorMessage(err, t("newRun.errorStart")));
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return <LoadingSpinner label={t("common.loadingPreferences")} />;
  }

  return (
    <PageShell withStickyFooter>
      <div className="page-stack">
        <header className="page-stack__block">
          <PageHeader title={t("newRun.title")} subtitle={t("newRun.subtitle")} />
          <p className="inline-meta new-run-meta">{t("newRun.valueStripInline")}</p>
        </header>

        {error ? <InlineAlert variant="danger">{error}</InlineAlert> : null}

        <GettingStartedSteps />

        <Surface>
          <div className="form-stack">
            <div data-coach="coach-newrun-topics">
              <RecommendationPreferencesForm
                formId="new-run-form"
                defaults={preferences}
                onChange={setPreferences}
                onSubmit={handleSubmit}
                submitLabel={submitting ? t("newRun.starting") : t("newRun.generate")}
                submitHint={t("newRun.generateHint")}
                submitting={submitting}
                showResearchArea
                researchArea={researchArea}
                onResearchAreaChange={setResearchArea}
                submitDataCoach="coach-newrun-submit"
                runMode={runMode}
                onRunModeChange={setRunMode}
                hideRunModeOnMobile
              />
            </div>
          </div>
        </Surface>

        {(profile.learned_topics?.length ?? 0) > 0 ? (
          <p className="inline-meta mb-0">
            {t("newRun.learnedTopicsNote", { count: profile.learned_topics?.length ?? 0 })}
          </p>
        ) : null}
      </div>

      <StickyFooter variant="fixed" visibleClass="d-lg-none">
        <div className="sticky-footer__mode" data-coach="coach-newrun-mode">
          <span className="sticky-footer__mode-label">{t("newRun.runMode.label")}</span>
          <RunModeSelector
            value={runMode}
            onChange={setRunMode}
            disabled={submitting}
            layout="compact"
            menuPlacement="top"
            showLabel={false}
            hideHint
          />
        </div>
        <Button
          type="submit"
          form="new-run-form"
          variant="primary"
          className="sticky-footer__submit"
          disabled={submitting}
          data-coach="coach-newrun-submit"
        >
          {submitting ? t("newRun.starting") : t("newRun.generateShort")}
        </Button>
        <p className="sticky-footer__hint">{t("newRun.stickyHint")}</p>
      </StickyFooter>
    </PageShell>
  );
}
