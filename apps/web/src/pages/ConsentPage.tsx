import type { FormEvent } from "react";
import { useState } from "react";
import { Alert, Button, Card, Form } from "react-bootstrap";
import { Trans, useTranslation } from "react-i18next";
import { Navigate, useNavigate } from "react-router-dom";

import { PageHeader } from "../components/ui/PageHeader";
import { useConsentStrings } from "../i18n/useConsentStrings";
import { useAuth } from "../contexts/AuthContext";
import { sessionService } from "../services";
import { HttpError } from "../services/http/HttpClient";

export function ConsentPage() {
  const { t } = useTranslation();
  const { summary, checkboxes } = useConsentStrings();
  const { accessToken, user, consentDone, completeConsent, setSessionId } = useAuth();
  const navigate = useNavigate();
  const [checks, setChecks] = useState([false, false, false, false]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  if (consentDone) {
    return <Navigate to="/profile?tab=consent" replace />;
  }

  const allChecked = checks.every(Boolean);

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
      navigate("/profile");
    } catch (err) {
      setError(err instanceof HttpError ? err.message : t("consent.errorSave"));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page-shell page-shell--narrow">
      <PageHeader title={t("consent.pageTitle")} subtitle={t("consent.pageSubtitle")} />

      <Card className="page-card consent-card border-0">
        <Card.Body className="p-md-5">
          <p className="lead-text mb-3">
            <Trans i18nKey="consent.intro" components={{ strong: <strong /> }} />
          </p>
          <ul className="consent-panel__list mb-4">
            {summary.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>

          {error ? <Alert variant="danger">{error}</Alert> : null}

          <Form onSubmit={handleSubmit}>
            <div className="consent-checks">
              {checkboxes.map((label, index) => (
                <Form.Check
                  key={label}
                  type="checkbox"
                  id={`consent-${index}`}
                  className="consent-checks__item"
                  label={label}
                  checked={checks[index]}
                  onChange={(e) => {
                    const next = [...checks];
                    next[index] = e.target.checked;
                    setChecks(next);
                  }}
                />
              ))}
            </div>
            <Button
              type="submit"
              variant="primary"
              size="lg"
              className="mt-4 w-100"
              disabled={!allChecked || loading}
            >
              {loading ? t("common.saving") : t("consent.acceptAndContinue")}
            </Button>
          </Form>
        </Card.Body>
      </Card>
    </div>
  );
}
