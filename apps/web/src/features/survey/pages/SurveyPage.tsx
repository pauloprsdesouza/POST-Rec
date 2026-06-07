import type { FormEvent } from "react";
import { useState } from "react";
import { Alert, Button, Card, Col, Form, Row } from "react-bootstrap";
import { useTranslation } from "react-i18next";

import { PageHeader } from "@/shared/ui/PageHeader";
import { useAuth } from "@/features/auth/context/AuthContext";
import { sessionService } from "@/shared/api";
import { getErrorMessage } from "@/shared/api/errors";

export function SurveyPage() {
  const { t } = useTranslation();
  const { accessToken, user, sessionId, selectedRunId } = useAuth();
  const [expectationMet, setExpectationMet] = useState(3);
  const [wouldUseAny, setWouldUseAny] = useState("maybe");
  const [wouldUseAgain, setWouldUseAgain] = useState(false);
  const [wouldRecommend, setWouldRecommend] = useState(false);
  const [helped, setHelped] = useState("");
  const [hurt, setHurt] = useState("");
  const [comment, setComment] = useState("");
  const [success, setSuccess] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    if (!accessToken || !user) {
      return;
    }

    setSubmitting(true);
    setError(null);
    setSuccess(null);

    try {
      await sessionService.submitSurvey(accessToken, {
        session_id: sessionId,
        run_id: selectedRunId,
        user_id: user.userId,
        expectation_met_score: expectationMet,
        would_use_any_recommendation_in_real_paper: wouldUseAny,
        would_use_again: wouldUseAgain,
        would_recommend: wouldRecommend,
        what_helped_most: helped,
        what_hurt_most: hurt,
        free_comment: comment,
      });
      setSuccess(t("survey.thankYou"));
    } catch (err) {
      setError(getErrorMessage(err, t("survey.errorSubmit")));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="page-shell page-shell--narrow">
      <PageHeader title={t("survey.title")} subtitle={t("survey.subtitle")} />

      {success ? <Alert variant="success">{success}</Alert> : null}
      {error ? <Alert variant="danger">{error}</Alert> : null}

      <Card className="page-card border-0">
        <Card.Body>
          <Form onSubmit={handleSubmit}>
            <Form.Group className="mb-4">
              <Form.Label>{t("survey.expectationsMet", { score: expectationMet })}</Form.Label>
              <Form.Range
                min={1}
                max={5}
                value={expectationMet}
                onChange={(e) => setExpectationMet(Number(e.target.value))}
              />
            </Form.Group>

            <Form.Group className="mb-3">
              <Form.Label>{t("survey.wouldUseInPaper")}</Form.Label>
              <Form.Select value={wouldUseAny} onChange={(e) => setWouldUseAny(e.target.value)}>
                <option value="yes">{t("common.yes")}</option>
                <option value="maybe">{t("common.maybe")}</option>
                <option value="no">{t("common.no")}</option>
              </Form.Select>
            </Form.Group>

            <Row className="g-3 mb-3">
              <Col md={6}>
                <Form.Check
                  type="checkbox"
                  id="would-use-again"
                  label={t("survey.wouldUseAgain")}
                  checked={wouldUseAgain}
                  onChange={(e) => setWouldUseAgain(e.target.checked)}
                />
              </Col>
              <Col md={6}>
                <Form.Check
                  type="checkbox"
                  id="would-recommend"
                  label={t("survey.wouldRecommend")}
                  checked={wouldRecommend}
                  onChange={(e) => setWouldRecommend(e.target.checked)}
                />
              </Col>
            </Row>

            <Form.Group className="mb-3">
              <Form.Label>{t("survey.whatHelped")}</Form.Label>
              <Form.Control as="textarea" rows={3} value={helped} onChange={(e) => setHelped(e.target.value)} />
            </Form.Group>
            <Form.Group className="mb-3">
              <Form.Label>{t("survey.whatImprove")}</Form.Label>
              <Form.Control as="textarea" rows={3} value={hurt} onChange={(e) => setHurt(e.target.value)} />
            </Form.Group>
            <Form.Group className="mb-4">
              <Form.Label>{t("survey.additionalComments")}</Form.Label>
              <Form.Control as="textarea" rows={3} value={comment} onChange={(e) => setComment(e.target.value)} />
            </Form.Group>

            <Button type="submit" variant="primary" className="w-100" disabled={submitting}>
              {submitting ? t("survey.submitting") : t("survey.submit")}
            </Button>
          </Form>
        </Card.Body>
      </Card>
    </div>
  );
}
