import type { FormEvent } from "react";
import { useState } from "react";
import { Button, Form } from "react-bootstrap";
import { Trans, useTranslation } from "react-i18next";
import { Navigate, useNavigate } from "react-router-dom";

import { PageHeader } from "@/shared/ui/PageHeader";
import { PageShell } from "@/shared/ui/PageShell";
import { Panel } from "@/shared/ui/Panel";
import { InlineAlert } from "@/shared/ui/InlineAlert";
import { useConsentStrings } from "@/shared/i18n/useConsentStrings";
import { useAuth } from "@/features/auth/context/AuthContext";
import { sessionService } from "@/shared/api";
import { getErrorMessage } from "@/shared/api/errors";

export function ConsentPage() {
  const { t } = useTranslation();
  const { summary, checkboxes } = useConsentStrings();
  const { accessToken, user, consentDone, completeConsent, setSessionId } = useAuth();
  const navigate = useNavigate();
  const [agreed, setAgreed] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  if (consentDone) {
    return <Navigate to="/profile?tab=consent" replace />;
  }

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    if (!accessToken || !user) {
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const session = await sessionService.createSession(accessToken, user.userId);
      await sessionService.createConsent(accessToken, user.userId, session.session_id, true);
      setSessionId(session.session_id);
      completeConsent(session.session_id);
      navigate("/profile?tab=research");
    } catch (err) {
      setError(getErrorMessage(err, t("consent.errorSave")));
    } finally {
      setLoading(false);
    }
  };

  return (
    <PageShell width="narrow">
      <div className="page-stack page-stack--tight">
        <PageHeader title={t("consent.pageTitle")} subtitle={t("consent.pageSubtitle")} />

        <p className="consent-time-badge consent-time-badge--solo">{t("setup.timeEstimate")}</p>

        <Panel className="consent-page__panel">
          <p className="lead-text mb-4">
            <Trans i18nKey="consent.intro" components={{ strong: <strong /> }} />
          </p>
          <ul className="consent-panel__list mb-4">
            {summary.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>

          {error ? <InlineAlert variant="danger">{error}</InlineAlert> : null}

          <Form onSubmit={handleSubmit} className="form-stack">
            <details className="consent-details">
              <summary>{t("consent.readFullTerms")}</summary>
              <ul className="consent-panel__list mt-2 mb-0">
                {checkboxes.map((label) => (
                  <li key={label}>{label}</li>
                ))}
              </ul>
            </details>
            <Form.Check
              type="checkbox"
              id="consent-agree"
              className="consent-checks__item consent-checks__item--primary"
              label={t("consent.agreeAll")}
              checked={agreed}
              onChange={(e) => setAgreed(e.target.checked)}
            />
            <Button
              type="submit"
              variant="primary"
              size="lg"
              className="w-100"
              disabled={!agreed || loading}
            >
              {loading ? t("common.saving") : t("consent.acceptAndContinue")}
            </Button>
          </Form>
        </Panel>
      </div>
    </PageShell>
  );
}
