import type { FormEvent } from "react";
import { Button, Col, Form, Row } from "react-bootstrap";
import { useTranslation } from "react-i18next";

import type { RecommendationDefaults } from "../../types/api";

interface RecommendationPreferencesFormProps {
  defaults: RecommendationDefaults;
  onChange: (defaults: RecommendationDefaults) => void;
  onSubmit?: (event: FormEvent) => void;
  submitLabel?: string;
  submitting?: boolean;
  showResearchArea?: boolean;
  researchArea?: string;
  onResearchAreaChange?: (value: string) => void;
}

export function RecommendationPreferencesForm({
  defaults,
  onChange,
  onSubmit,
  submitLabel,
  submitting = false,
  showResearchArea = false,
  researchArea = "",
  onResearchAreaChange,
}: RecommendationPreferencesFormProps) {
  const { t } = useTranslation();
  const topicsText = (defaults.seed_topics ?? []).join("\n");
  const buttonLabel = submitLabel ?? t("profile.savePreferences");

  const update = (partial: Partial<RecommendationDefaults>) => {
    onChange({ ...defaults, ...partial });
  };

  const formBody = (
    <>
      {showResearchArea ? (
        <Form.Group className="mb-3">
          <Form.Label>{t("preferences.researchArea")}</Form.Label>
          <Form.Control
            value={researchArea}
            onChange={(e) => onResearchAreaChange?.(e.target.value)}
            placeholder={t("preferences.researchAreaPlaceholder")}
            required
          />
        </Form.Group>
      ) : null}

      <Form.Group className="mb-3">
        <Form.Label>{t("preferences.seedTopics")}</Form.Label>
        <Form.Control
          as="textarea"
          rows={4}
          value={topicsText}
          onChange={(e) =>
            update({
              seed_topics: e.target.value
                .split("\n")
                .map((topic) => topic.trim())
                .filter(Boolean),
            })
          }
          placeholder={t("preferences.seedTopicsPlaceholder")}
        />
        <Form.Text>{t("preferences.seedTopicsHint")}</Form.Text>
      </Form.Group>

      <Form.Group className="mb-3">
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
        <Col md={6} className="d-flex align-items-end pb-1">
          <Form.Check
            type="switch"
            id="pref-avoid-experiments"
            label={t("preferences.avoidRealUserExperiments")}
            checked={defaults.avoid_real_user_experiments ?? true}
            onChange={(e) => update({ avoid_real_user_experiments: e.target.checked })}
          />
        </Col>
      </Row>

      {onSubmit ? (
        <Button type="submit" variant="primary" disabled={submitting}>
          {submitting ? t("common.saving") : buttonLabel}
        </Button>
      ) : null}
    </>
  );

  if (onSubmit) {
    return <Form onSubmit={onSubmit}>{formBody}</Form>;
  }

  return <div>{formBody}</div>;
}

export function emptyRecommendationDefaults(expectedOutput = ""): RecommendationDefaults {
  return {
    seed_topics: [],
    expected_output: expectedOutput,
    desired_depth: "medium",
    avoid_real_user_experiments: true,
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
  };
}
