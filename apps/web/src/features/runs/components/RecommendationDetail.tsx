import type { FormEvent } from "react";
import { useState } from "react";
import { Accordion, Alert, Button, Col, Form, Row } from "react-bootstrap";
import { useTranslation } from "react-i18next";

import { runService } from "@/shared/api";
import { getErrorMessage } from "@/shared/api/errors";
import type { Recommendation, SourceDocument } from "@/shared/types/api";
import { EvidenceList } from "./EvidenceList";
import { SotaVerificationPanel } from "./SotaVerificationPanel";

interface RecommendationDetailProps {
  recommendation: Recommendation;
  index: number;
  total: number;
  runId: string;
  sessionId: string | null;
  token: string;
  sources?: SourceDocument[];
}

export function RecommendationDetail({
  recommendation,
  index,
  total,
  runId,
  sessionId,
  token,
  sources = [],
}: RecommendationDetailProps) {
  const { t } = useTranslation();
  const [feedback, setFeedback] = useState({
    relevance: 3,
    clarity: 3,
    feasibility: 3,
    originality: 3,
    trust: 3,
    usefulness: 3,
    wouldUse: "maybe",
    decision: "save",
    comment: "",
  });
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [showFeedback, setShowFeedback] = useState(false);

  const scoreLabel =
    recommendation.final_score != null ? Math.round(recommendation.final_score) : null;
  const confidenceKey = (recommendation.confidence_level ?? "medium").toLowerCase();
  const confidence = t(`ideas.confidence.${confidenceKey}`, {
    defaultValue: confidenceKey.replace(/\b\w/g, (c) => c.toUpperCase()),
  });
  const sourceCount = recommendation.evidence_papers?.length ?? 0;

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setSubmitting(true);
    setError(null);
    setMessage(null);
    try {
      const result = await runService.submitFeedback(token, recommendation.id, {
        session_id: sessionId,
        run_id: runId,
        relevance_score: feedback.relevance,
        originality_score: feedback.originality,
        clarity_score: feedback.clarity,
        feasibility_score: feedback.feasibility,
        trust_score: feedback.trust,
        usefulness_score: feedback.usefulness,
        would_use_in_real_paper: feedback.wouldUse,
        decision: feedback.decision,
        comment: feedback.comment,
      });
      setMessage(
        t("ideas.feedbackSaved", { score: result.expectation_alignment_score.toFixed(2) }),
      );
      setShowFeedback(false);
    } catch (err) {
      setError(getErrorMessage(err, t("ideas.feedbackError")));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <article className="surface-card idea-detail">
      <div className="idea-detail__meta">
        <span className="idea-detail__counter">
          {t("ideas.countOfTotal", { current: index, total })}
        </span>
        {scoreLabel != null ? (
          <span className="idea-detail__score">{t("ideas.score", { value: scoreLabel })}</span>
        ) : null}
        <span className="idea-detail__chip">{confidence}</span>
        <span className="idea-detail__chip">{t("ideas.sourcesCount", { count: sourceCount })}</span>
      </div>

      <h2 className="idea-detail__title">{recommendation.title}</h2>

      {recommendation.technique_name ? (
        <p className="idea-detail__technique">{recommendation.technique_name}</p>
      ) : null}

      <Accordion defaultActiveKey="summary" className="idea-detail__sections">
        <Accordion.Item eventKey="summary" className="idea-section">
          <Accordion.Header>{t("ideas.summary")}</Accordion.Header>
          <Accordion.Body>
            <Section label={t("ideas.researchGap")} value={recommendation.research_gap} />
            <Section label={t("ideas.researchQuestion")} value={recommendation.research_question} />
            <Section label={t("ideas.hypothesis")} value={recommendation.hypothesis} />
            <Section label={t("ideas.contribution")} value={recommendation.expected_contribution} />
            <Section label={t("ideas.relatedWork")} value={recommendation.related_work_summary} />
            <SotaVerificationPanel recommendation={recommendation} sources={sources} />
            {recommendation.scores ? (
              <div className="idea-scores">
                {Object.entries(recommendation.scores)
                  .filter(([name]) =>
                    ["relevance", "novelty", "evidence", "feasibility"].includes(name),
                  )
                  .map(([name, value]) => (
                    <div key={name} className="idea-scores__item">
                      <div className="idea-scores__label">
                        {t(`ideas.scoreNames.${name}`, {
                          defaultValue: name.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase()),
                        })}
                      </div>
                      <div className="progress idea-scores__bar">
                        <div
                          className="progress-bar"
                          style={{ width: `${Math.min(value, 100)}%` }}
                        />
                      </div>
                    </div>
                  ))}
              </div>
            ) : null}
          </Accordion.Body>
        </Accordion.Item>

        <Accordion.Item eventKey="method" className="idea-section">
          <Accordion.Header>{t("ideas.methodPlan")}</Accordion.Header>
          <Accordion.Body>
            <Section label={t("ideas.proposedMethod")} value={recommendation.proposed_method} />
            <Section label={t("ideas.experimentalPlan")} value={recommendation.experimental_plan} />
            <ListSection label={t("ideas.datasets")} items={recommendation.datasets} />
            <ListSection label={t("ideas.metrics")} items={recommendation.evaluation_metrics} />
            <ListSection label={t("ideas.risks")} items={recommendation.risks} />
          </Accordion.Body>
        </Accordion.Item>

        <Accordion.Item eventKey="sources" className="idea-section">
          <Accordion.Header>{t("ideas.evidence", { count: sourceCount })}</Accordion.Header>
          <Accordion.Body>
            <EvidenceList papers={recommendation.evidence_papers} />
          </Accordion.Body>
        </Accordion.Item>
      </Accordion>

      {message ? (
        <Alert variant="success" className="mt-3 mb-0">
          {message}
        </Alert>
      ) : null}

      {!showFeedback ? (
        <Button
          variant="primary"
          className="idea-detail__rate-btn w-100"
          onClick={() => setShowFeedback(true)}
        >
          {t("ideas.rateIdea")}
        </Button>
      ) : (
        <div className="idea-feedback mt-3">
          <div className="idea-feedback__header">
            <h3 className="h6 mb-0">{t("ideas.yourFeedback")}</h3>
            <Button variant="link" className="p-0" onClick={() => setShowFeedback(false)}>
              {t("common.close")}
            </Button>
          </div>
          {error ? <Alert variant="danger">{error}</Alert> : null}
          <Form onSubmit={handleSubmit}>
            <p className="text-secondary small">{t("ideas.feedbackHint")}</p>
            <SliderField
              label={t("ideas.relevance")}
              value={feedback.relevance}
              onChange={(v) => setFeedback({ ...feedback, relevance: v })}
            />
            <SliderField
              label={t("ideas.clarity")}
              value={feedback.clarity}
              onChange={(v) => setFeedback({ ...feedback, clarity: v })}
            />
            <SliderField
              label={t("ideas.feasibilityLabel")}
              value={feedback.feasibility}
              onChange={(v) => setFeedback({ ...feedback, feasibility: v })}
            />
            <SliderField
              label={t("ideas.originality")}
              value={feedback.originality}
              onChange={(v) => setFeedback({ ...feedback, originality: v })}
            />
            <Row className="g-3 mt-1">
              <Col xs={6}>
                <Form.Label className="small">{t("ideas.useInPaper")}</Form.Label>
                <Form.Select
                  size="sm"
                  value={feedback.wouldUse}
                  onChange={(e) => setFeedback({ ...feedback, wouldUse: e.target.value })}
                >
                  <option value="yes">{t("common.yes")}</option>
                  <option value="maybe">{t("common.maybe")}</option>
                  <option value="no">{t("common.no")}</option>
                </Form.Select>
              </Col>
              <Col xs={6}>
                <Form.Label className="small">{t("ideas.decision")}</Form.Label>
                <Form.Select
                  size="sm"
                  value={feedback.decision}
                  onChange={(e) => setFeedback({ ...feedback, decision: e.target.value })}
                >
                  <option value="approved">{t("ideas.approved")}</option>
                  <option value="save">{t("ideas.saveDecision")}</option>
                  <option value="needs_revision">{t("ideas.needsRevision")}</option>
                  <option value="rejected">{t("ideas.rejected")}</option>
                </Form.Select>
              </Col>
            </Row>
            <Form.Group className="mt-2">
              <Form.Label className="small">{t("ideas.comments")}</Form.Label>
              <Form.Control
                as="textarea"
                rows={2}
                value={feedback.comment}
                onChange={(e) => setFeedback({ ...feedback, comment: e.target.value })}
              />
            </Form.Group>
            <Button type="submit" variant="primary" className="w-100 mt-3" disabled={submitting}>
              {submitting ? t("ideas.saving") : t("ideas.submitFeedback")}
            </Button>
          </Form>
        </div>
      )}
    </article>
  );
}

function Section({ label, value }: { label: string; value?: string | null }) {
  if (!value) return null;
  return (
    <div className="idea-block">
      <div className="idea-block__label">{label}</div>
      <p className="idea-block__text">{value}</p>
    </div>
  );
}

function ListSection({ label, items }: { label: string; items?: string[] }) {
  if (!items?.length) return null;
  return (
    <div className="idea-block">
      <div className="idea-block__label">{label}</div>
      <ul className="idea-block__list">
        {items.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </div>
  );
}

function SliderField({
  label,
  value,
  onChange,
}: {
  label: string;
  value: number;
  onChange: (value: number) => void;
}) {
  return (
    <Form.Group className="mb-2">
      <Form.Label className="small mb-1">
        {label} <strong>{value}</strong>
      </Form.Label>
      <Form.Range min={1} max={5} value={value} onChange={(e) => onChange(Number(e.target.value))} />
    </Form.Group>
  );
}
