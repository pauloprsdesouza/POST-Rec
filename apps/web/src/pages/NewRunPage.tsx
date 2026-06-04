import type { FormEvent } from "react";
import { useEffect, useState } from "react";
import { Alert, Card } from "react-bootstrap";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";

import {
  mergeRecommendationDefaults,
  RecommendationPreferencesForm,
} from "../components/profile/RecommendationPreferencesForm";
import { RunModeSelector } from "../components/runs/RunModeSelector";
import { PageHeader } from "../components/ui/PageHeader";
import { LoadingSpinner } from "../components/ui/LoadingSpinner";
import { useAuth } from "../contexts/AuthContext";
import { useRuns } from "../contexts/RunsContext";
import i18n from "../i18n";
import { profileService, runService, sessionService } from "../services";
import { HttpError } from "../services/http/HttpClient";
import type { RecommendationDefaults, RunMode, UserProfile } from "../types/api";

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
  const [runMode, setRunMode] = useState<RunMode>("quick");

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
        const academic = (data.academic_level ?? "").toLowerCase();
        if (preferredMode === "quick" || preferredMode === "sota" || preferredMode === "exploratory") {
          setRunMode(preferredMode);
        } else if (academic === "phd" || academic === "professor") {
          setRunMode("sota");
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

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    if (!accessToken || !user) {
      return;
    }

    const topicList = preferences.seed_topics ?? [];
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
        expected_output: preferences.expected_output ?? undefined,
        desired_depth: preferences.desired_depth ?? "medium",
        avoid_real_user_experiments: preferences.avoid_real_user_experiments ?? true,
        publication_goal: "conference_or_journal",
      });

      const run = await runService.createRun(accessToken, {
        session_id: activeSessionId,
        expectation_id: expectation.id,
        topics: topicList,
        mode: runMode,
        max_papers: 50,
        max_recommendations: 5,
      });

      setSelectedRunId(run.run_id);
      invalidateRuns();
      navigate(`/runs/${run.run_id}`);
    } catch (err) {
      setError(err instanceof HttpError ? err.message : t("newRun.errorStart"));
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return <LoadingSpinner label={t("common.loadingPreferences")} />;
  }

  return (
    <div className="page-shell">
      <PageHeader title={t("newRun.title")} subtitle={t("newRun.subtitle")} />

      {error ? <Alert variant="danger">{error}</Alert> : null}

      <Card className="page-card border-0">
        <Card.Body>
          <RunModeSelector value={runMode} onChange={setRunMode} disabled={submitting} />
          <RecommendationPreferencesForm
            defaults={preferences}
            onChange={setPreferences}
            onSubmit={handleSubmit}
            submitLabel={submitting ? t("newRun.starting") : t("newRun.generate")}
            submitting={submitting}
            showResearchArea
            researchArea={researchArea}
            onResearchAreaChange={setResearchArea}
          />
        </Card.Body>
      </Card>

      {(profile.learned_topics?.length ?? 0) > 0 ? (
        <p className="text-secondary small mt-3 mb-0">
          {t("newRun.learnedTopicsNote", { count: profile.learned_topics?.length ?? 0 })}
        </p>
      ) : null}
    </div>
  );
}
