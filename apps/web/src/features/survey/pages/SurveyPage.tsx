import { useCallback, useState } from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useSearchParams } from "react-router-dom";

import { PageHeader } from "@/shared/ui/PageHeader";
import { InlineAlert } from "@/shared/ui/InlineAlert";
import { useAuth } from "@/features/auth/context/AuthContext";
import { sessionService } from "@/shared/api";
import { getErrorMessage } from "@/shared/api/errors";

export function SurveyPage() {
  const { t } = useTranslation();
  const [searchParams] = useSearchParams();
  const runIdFromQuery = searchParams.get("run_id");
  const { accessToken, user, sessionId, selectedRunId } = useAuth();
  const [expectationMet, setExpectationMet] = useState<number | null>(null);
  const [wouldUseAgain, setWouldUseAgain] = useState<boolean | null>(null);
  const [done, setDone] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const submit = useCallback(
    async (score: number, useAgain: boolean) => {
      if (!accessToken || !user || submitting || done) {
        return;
      }
      setSubmitting(true);
      setError(null);
      try {
        await sessionService.submitSurvey(accessToken, {
          session_id: sessionId,
          run_id: runIdFromQuery ?? selectedRunId,
          user_id: user.userId,
          expectation_met_score: score,
          would_use_any_recommendation_in_real_paper: score >= 4 ? "yes" : score >= 3 ? "maybe" : "no",
          would_use_again: useAgain,
          would_recommend: useAgain,
        });
        setDone(true);
      } catch (err) {
        setError(getErrorMessage(err, t("survey.errorSubmit")));
      } finally {
        setSubmitting(false);
      }
    },
    [accessToken, done, runIdFromQuery, selectedRunId, sessionId, submitting, t, user],
  );

  const handleScore = (value: number) => {
    setExpectationMet(value);
    if (wouldUseAgain != null) {
      void submit(value, wouldUseAgain);
    }
  };

  const handleUseAgain = (value: boolean) => {
    setWouldUseAgain(value);
    if (expectationMet != null) {
      void submit(expectationMet, value);
    }
  };

  if (done) {
    return (
      <div className="page-shell page-shell--narrow">
        <div className="page-stack page-stack--tight">
          <PageHeader title={t("survey.title")} />
          <div className="panel surface-inset text-center">
            <p className="lead mb-4">{t("survey.thankYouShort")}</p>
            <div className="d-flex flex-wrap gap-2 justify-content-center">
              <Link to="/runs/new" className="btn btn-primary">
                {t("runs.completeBanner.newRun")}
              </Link>
              <Link to="/runs" className="btn btn-outline-secondary">
                {t("survey.backToRuns")}
              </Link>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="page-shell page-shell--narrow">
      <div className="page-stack page-stack--tight">
        <PageHeader title={t("survey.title")} subtitle={t("survey.subtitleShort")} />
        {error ? <InlineAlert variant="danger">{error}</InlineAlert> : null}

        <div className="panel">
          <div className="session-quick-feedback session-quick-feedback--standalone">
            <p className="session-quick-feedback__hint">{t("survey.autoSaveHint")}</p>

            <div className="session-quick-feedback__row">
              <span className="session-quick-feedback__label">{t("survey.quickSatisfaction")}</span>
              <div className="quick-rating__stars" role="group">
                {[1, 2, 3, 4, 5].map((value) => (
                  <button
                    key={value}
                    type="button"
                    className={`quick-rating__star ${expectationMet === value ? "quick-rating__star--selected" : ""} ${expectationMet != null && expectationMet >= value ? "quick-rating__star--filled" : ""}`}
                    aria-label={t("ideas.rateValue", { value })}
                    aria-pressed={expectationMet === value}
                    onClick={() => handleScore(value)}
                  >
                    ★
                  </button>
                ))}
              </div>
            </div>

            <div className="session-quick-feedback__row">
              <span className="session-quick-feedback__label">{t("survey.quickUseAgain")}</span>
              <div className="quick-rating__chips">
                <button
                  type="button"
                  className={`quick-rating__chip ${wouldUseAgain === true ? "quick-rating__chip--active" : ""}`}
                  aria-pressed={wouldUseAgain === true}
                  onClick={() => handleUseAgain(true)}
                >
                  {t("common.yes")}
                </button>
                <button
                  type="button"
                  className={`quick-rating__chip ${wouldUseAgain === false ? "quick-rating__chip--active" : ""}`}
                  aria-pressed={wouldUseAgain === false}
                  onClick={() => handleUseAgain(false)}
                >
                  {t("common.no")}
                </button>
              </div>
            </div>

            {submitting ? <p className="session-quick-feedback__saving">{t("survey.submitting")}</p> : null}
          </div>
        </div>
      </div>
    </div>
  );
}
