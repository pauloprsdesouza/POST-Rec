import type { FormEvent } from "react";
import { useState } from "react";
import { Button, Col, Form, Row } from "react-bootstrap";
import { useTranslation } from "react-i18next";

import type { RecommendationDefaults } from "@/shared/types/api";
import { formatSeedTopics, withParsedSeedTopics } from "@/features/profile/utils/seedTopics";

interface RecommendationPreferencesFormProps {
  defaults: RecommendationDefaults;
  onChange: (defaults: RecommendationDefaults) => void;
  onSubmit?: (event: FormEvent, defaults: RecommendationDefaults) => void;
  submitLabel?: string;
  submitHint?: string;
  submitting?: boolean;
  showResearchArea?: boolean;
  researchArea?: string;
  onResearchAreaChange?: (value: string) => void;
  formId?: string;
}

export function RecommendationPreferencesForm({
  defaults,
  onChange,
  onSubmit,
  submitLabel,
  submitHint,
  submitting = false,
  showResearchArea = false,
  researchArea = "",
  onResearchAreaChange,
  formId,
}: RecommendationPreferencesFormProps) {
  const { t } = useTranslation();
  const [topicsText, setTopicsText] = useState(() => formatSeedTopics(defaults.seed_topics));
  const [showAdvanced, setShowAdvanced] = useState(false);
  const buttonLabel = submitLabel ?? t("profile.savePreferences");

  const update = (partial: Partial<RecommendationDefaults>) => {
    onChange({ ...defaults, ...partial });
  };

  const syncSeedTopics = (text: string) => {
    onChange(withParsedSeedTopics(defaults, text));
  };

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault();
    const nextDefaults = withParsedSeedTopics(defaults, topicsText);
    onChange(nextDefaults);
    onSubmit?.(event, nextDefaults);
  };

  const formBody = (
    <>
      {showResearchArea ? (
        <Form.Group className="field-group">
          <Form.Label>{t("preferences.researchArea")}</Form.Label>
          <Form.Control
            value={researchArea}
            onChange={(e) => onResearchAreaChange?.(e.target.value)}
            placeholder={t("preferences.researchAreaPlaceholder")}
            required
          />
        </Form.Group>
      ) : null}

      <Form.Group className="field-group">
        <Form.Label>{t("preferences.seedTopics")}</Form.Label>
        <Form.Control
          as="textarea"
          rows={4}
          value={topicsText}
          onChange={(e) => setTopicsText(e.target.value)}
          onBlur={() => syncSeedTopics(topicsText)}
          placeholder={t("preferences.seedTopicsPlaceholder")}
          spellCheck
          style={{ whiteSpace: "pre-wrap" }}
        />
        <Form.Text>{t("preferences.seedTopicsHint")}</Form.Text>
      </Form.Group>

      <Button
        type="button"
        variant="link"
        className="pref-advanced-toggle px-0 mb-2"
        onClick={() => setShowAdvanced((open) => !open)}
      >
        {showAdvanced ? t("preferences.hideOptions") : t("preferences.moreOptions")}
      </Button>

      {showAdvanced ? (
        <>
          <Form.Group className="field-group">
            <Form.Label>{t("preferences.expectedOutput")}</Form.Label>
            <Form.Control
              as="textarea"
              rows={2}
              value={defaults.expected_output ?? t("preferences.defaultExpectedOutput")}
              onChange={(e) => update({ expected_output: e.target.value })}
            />
          </Form.Group>

          <Row className="g-3 mb-4">
            <Col md={6}>
              <Form.Label>{t("preferences.defaultDepth")}</Form.Label>
              <Form.Select
                value={defaults.desired_depth ?? "medium"}
                onChange={(e) => update({ desired_depth: e.target.value })}
              >
                <option value="shallow">{t("preferences.depthShallow")}</option>
                <option value="medium">{t("preferences.depthMedium")}</option>
                <option value="deep">{t("preferences.depthDeep")}</option>
              </Form.Select>
            </Col>
            <Col md={6}>
              <Form.Label>{t("preferences.maxArticleAge")}</Form.Label>
              <Form.Select
                value={String(defaults.max_article_age_years ?? 5)}
                onChange={(e) => update({ max_article_age_years: Number(e.target.value) })}
              >
                <option value="1">{t("preferences.maxArticleAgeOption", { years: 1 })}</option>
                <option value="2">{t("preferences.maxArticleAgeOption", { years: 2 })}</option>
                <option value="3">{t("preferences.maxArticleAgeOption", { years: 3 })}</option>
                <option value="5">{t("preferences.maxArticleAgeOption", { years: 5 })}</option>
                <option value="10">{t("preferences.maxArticleAgeOption", { years: 10 })}</option>
                <option value="15">{t("preferences.maxArticleAgeOption", { years: 15 })}</option>
                <option value="20">{t("preferences.maxArticleAgeOption", { years: 20 })}</option>
              </Form.Select>
            </Col>
          </Row>

          <Row className="g-3 mb-4">
            <Col md={12} className="d-flex align-items-end pb-1">
              <Form.Check
                type="switch"
                id="pref-avoid-experiments"
                label={t("preferences.avoidRealUserExperiments")}
                checked={defaults.avoid_real_user_experiments ?? true}
                onChange={(e) => update({ avoid_real_user_experiments: e.target.checked })}
              />
            </Col>
          </Row>
        </>
      ) : null}

      {onSubmit ? (
        <>
          <Button type="submit" variant="primary" size="lg" className="w-100" disabled={submitting}>
            {submitting ? t("common.saving") : buttonLabel}
          </Button>
          {submitHint ? <p className="form-submit-hint">{submitHint}</p> : null}
        </>
      ) : null}
    </>
  );

  if (onSubmit) {
    return (
      <Form id={formId} className="form-stack" onSubmit={handleSubmit}>
        {formBody}
      </Form>
    );
  }

  return <div className="form-stack">{formBody}</div>;
}

export function emptyRecommendationDefaults(expectedOutput = ""): RecommendationDefaults {
  return {
    seed_topics: [],
    expected_output: expectedOutput,
    desired_depth: "medium",
    avoid_real_user_experiments: true,
    max_article_age_years: 5,
  };
}

export function mergeRecommendationDefaults(
  profileDefaults?: RecommendationDefaults | null,
  learnedTopics?: string[] | null,
  expectedOutputFallback = "",
): RecommendationDefaults {
  const base = emptyRecommendationDefaults(expectedOutputFallback);
  const fromProfile = profileDefaults ?? {};
  const seedTopics = fromProfile.seed_topics?.length
    ? fromProfile.seed_topics
    : learnedTopics?.slice(0, 3).length
      ? learnedTopics.slice(0, 3)
      : base.seed_topics;

  return {
    seed_topics: seedTopics,
    expected_output: fromProfile.expected_output ?? base.expected_output,
    desired_depth: fromProfile.desired_depth ?? base.desired_depth,
    avoid_real_user_experiments:
      fromProfile.avoid_real_user_experiments ?? base.avoid_real_user_experiments,
    max_article_age_years: fromProfile.max_article_age_years ?? base.max_article_age_years,
  };
}
