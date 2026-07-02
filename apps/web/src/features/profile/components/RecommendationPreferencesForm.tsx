import type { FormEvent } from "react";

import { useRef } from "react";

import { Button, Form } from "react-bootstrap";

import { useTranslation } from "react-i18next";



import { RunModeSelector } from "@/features/runs/components/RunModeSelector";

import { SeedTopicsInput, type SeedTopicsInputHandle } from "@/features/profile/components/SeedTopicsInput";

import type { RecommendationDefaults, RunModeSelection } from "@/shared/types/api";



const DEPTH_OPTIONS = ["shallow", "medium", "deep"] as const;
const DEPTH_LABELS: Record<(typeof DEPTH_OPTIONS)[number], string> = {
  shallow: "preferences.depthShallow",
  medium: "preferences.depthMedium",
  deep: "preferences.depthDeep",
};

const ARTICLE_AGE_OPTIONS = [1, 2, 3, 5, 10, 15, 20] as const;



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

  submitDataCoach?: string;

  runMode?: RunModeSelection;

  onRunModeChange?: (mode: RunModeSelection) => void;

  hideRunModeOnMobile?: boolean;

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

  submitDataCoach,

  runMode,

  onRunModeChange,

  hideRunModeOnMobile = false,

}: RecommendationPreferencesFormProps) {

  const { t } = useTranslation();

  const seedTopicsRef = useRef<SeedTopicsInputHandle>(null);

  const buttonLabel = submitLabel ?? t("profile.savePreferences");



  const update = (partial: Partial<RecommendationDefaults>) => {

    onChange({ ...defaults, ...partial });

  };



  const handleSubmit = (event: FormEvent) => {

    event.preventDefault();

    const seedTopics = seedTopicsRef.current?.flushDraft() ?? defaults.seed_topics ?? [];

    const nextDefaults = { ...defaults, seed_topics: seedTopics };

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

          <Form.Text>{t("preferences.researchAreaHint")}</Form.Text>

        </Form.Group>

      ) : null}



      <Form.Group className="field-group">

        <Form.Label htmlFor="seed-topics-input">{t("preferences.seedTopics")}</Form.Label>

        <p className="form-field-intro">{t("preferences.seedTopicsWhy")}</p>

        <SeedTopicsInput

          ref={seedTopicsRef}

          id="seed-topics-input"

          value={defaults.seed_topics ?? []}

          onChange={(seed_topics) => update({ seed_topics })}

          placeholder={t("preferences.seedTopicsPlaceholder")}

          disabled={submitting}

        />

        <Form.Text>{t("preferences.seedTopicsHint")}</Form.Text>

      </Form.Group>



      {runMode !== undefined && onRunModeChange ? (

        <div

          className={`field-group ${hideRunModeOnMobile ? "d-none d-lg-block" : ""}`}

          data-coach="coach-newrun-mode"

        >

          <RunModeSelector

            value={runMode}

            onChange={onRunModeChange}

            disabled={submitting}

            menuPlacement="bottom"

          />

        </div>

      ) : null}



      <Form.Group className="field-group">

        <Form.Label>{t("preferences.defaultDepth")}</Form.Label>

        <Form.Text className="d-block mb-2">{t("preferences.depthHint")}</Form.Text>

        <div className="depth-chips" role="group" aria-label={t("preferences.defaultDepth")}>

          {DEPTH_OPTIONS.map((depth) => (

            <button

              key={depth}

              type="button"

              className={`depth-chips__btn ${(defaults.desired_depth ?? "medium") === depth ? "depth-chips__btn--active" : ""}`}

              aria-pressed={(defaults.desired_depth ?? "medium") === depth}

              disabled={submitting}

              onClick={() => update({ desired_depth: depth })}

            >

              {t(DEPTH_LABELS[depth])}

            </button>

          ))}

        </div>

      </Form.Group>



      <Form.Group className="field-group">

        <Form.Label>{t("preferences.maxArticleAge")}</Form.Label>

        <Form.Select

          value={String(defaults.max_article_age_years ?? 5)}

          onChange={(e) => update({ max_article_age_years: Number(e.target.value) })}

          disabled={submitting}

        >

          {ARTICLE_AGE_OPTIONS.map((years) => (

            <option key={years} value={years}>

              {t("preferences.maxArticleAgeOption", { years })}

            </option>

          ))}

        </Form.Select>

        <Form.Text>{t("preferences.maxArticleAgeHint")}</Form.Text>

      </Form.Group>



      <details className="pref-details">

        <summary>{t("preferences.moreOptions")}</summary>

        <Form.Group className="field-group mt-3">

          <Form.Label>{t("preferences.expectedOutput")}</Form.Label>

          <Form.Control

            as="textarea"

            rows={2}

            value={defaults.expected_output ?? t("preferences.defaultExpectedOutput")}

            onChange={(e) => update({ expected_output: e.target.value })}

            disabled={submitting}

          />

          <Form.Text>{t("preferences.expectedOutputHint")}</Form.Text>

        </Form.Group>

      </details>



      {onSubmit ? (

        <div

          className={`run-composer-footer ${submitDataCoach ? "d-none d-lg-block" : ""}`}

          {...(submitDataCoach ? { "data-coach": submitDataCoach } : {})}

        >

          <div className="run-composer-footer__submit">

            <Button type="submit" variant="primary" size="lg" className="w-100" disabled={submitting}>

              {submitting ? t("common.saving") : buttonLabel}

            </Button>

            {submitHint ? <p className="form-submit-hint">{submitHint}</p> : null}

          </div>

        </div>

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

    max_article_age_years: fromProfile.max_article_age_years ?? base.max_article_age_years,

  };

}


