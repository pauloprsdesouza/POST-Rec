import { useCallback, useState } from "react";
import { useTranslation } from "react-i18next";

import { useAuth } from "@/features/auth/context/AuthContext";
import { sessionService } from "@/shared/api";
import { getErrorMessage } from "@/shared/api/errors";
import { InlineAlert } from "@/shared/ui/InlineAlert";

import { BinaryFeedback } from "./feedback/BinaryFeedback";

interface SessionQuickFeedbackProps {
  runId: string;
  visible?: boolean;
}

export function SessionQuickFeedback({ runId, visible = true }: SessionQuickFeedbackProps) {
  const { t } = useTranslation();
  const { accessToken, user, sessionId } = useAuth();
  const [submitting, setSubmitting] = useState(false);
  const [done, setDone] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = useCallback(
    async (positive: boolean) => {
      if (!accessToken || !user || submitting || done) {
        return;
      }
      setSubmitting(true);
      setError(null);
      try {
        await sessionService.submitSurvey(accessToken, {
          session_id: sessionId,
          run_id: runId,
          user_id: user.userId,
          expectation_met_score: positive ? 5 : 2,
        });
        setDone(true);
      } catch (err) {
        setError(getErrorMessage(err, t("survey.errorSubmit")));
      } finally {
        setSubmitting(false);
      }
    },
    [accessToken, done, runId, sessionId, submitting, t, user],
  );

  if (!visible) {
    return null;
  }

  if (done) {
    return (
      <section className="session-feedback session-feedback--done" aria-live="polite">
        <p className="session-feedback__confirmation">{t("survey.thankYouShort")}</p>
      </section>
    );
  }

  return (
    <section className="session-feedback" aria-label={t("survey.quickPrompt")}>
      <div className="session-feedback__row">
        <p className="session-feedback__question">{t("survey.quickPrompt")}</p>
        <BinaryFeedback
          disabled={submitting}
          positiveLabel={t("ideas.useful")}
          negativeLabel={t("ideas.notUseful")}
          ariaLabel={t("survey.quickPrompt")}
          onSelect={(positive) => {
            void submit(positive);
          }}
        />
      </div>

      {submitting ? <p className="session-feedback__meta">{t("survey.submitting")}</p> : null}
      {error ? <InlineAlert variant="danger">{error}</InlineAlert> : null}
    </section>
  );
}
