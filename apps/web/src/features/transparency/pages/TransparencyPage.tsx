import { useTranslation } from "react-i18next";

import { MathBlock } from "@/features/transparency/components/MathBlock";
import { TransparencySection } from "@/features/transparency/components/TransparencySection";
import { WeightTable } from "@/features/transparency/components/WeightTable";
import { PageHeader } from "@/shared/ui/PageHeader";
import {
  EAS_WEIGHTS,
  FINAL_RANKING_WEIGHTS,
  HYBRID_RETRIEVAL,
  IDEA_SCORE_DIMENSIONS,
  LITERATURE_SOURCES,
  PAPER_RELEVANCE,
  PIPELINE_STEPS,
  VERIFIED_RANKING_WEIGHTS,
  WOULD_USE_SCORES,
} from "@/features/transparency/constants/transparencyModel";

const TOC_SECTIONS = [
  "overview",
  "pipeline",
  "inputs",
  "retrieval",
  "relevance",
  "embeddings",
  "generation",
  "ideaScores",
  "finalScore",
  "feedback",
  "limitations",
] as const;

function formatPct(value: number): string {
  return `${Math.round(value * 100)}%`;
}

export function TransparencyPage() {
  const { t } = useTranslation();
  const rel = PAPER_RELEVANCE;

  return (
    <div className="page-shell page-shell--wide transparency-page">
      <div className="page-stack">
        <PageHeader title={t("transparency.title")} subtitle={t("transparency.subtitle")} />

        <nav className="transparency-toc panel" aria-label={t("transparency.tocLabel")}>
          <p className="panel__title mb-3">{t("transparency.tocLabel")}</p>
          <ol className="transparency-toc__list">
          {TOC_SECTIONS.map((id) => (
            <li key={id}>
              <a href={`#${id}`}>{t(`transparency.sections.${id}`)}</a>
            </li>
          ))}
        </ol>
      </nav>

      <article className="transparency-article">
        <TransparencySection id="overview" title={t("transparency.sections.overview")}>
          <p>{t("transparency.overview.p1")}</p>
          <p>{t("transparency.overview.p2")}</p>
          <ul className="transparency-list">
            <li>{t("transparency.overview.bullet1")}</li>
            <li>{t("transparency.overview.bullet2")}</li>
            <li>{t("transparency.overview.bullet3")}</li>
          </ul>
        </TransparencySection>

        <TransparencySection id="pipeline" title={t("transparency.sections.pipeline")}>
          <p>{t("transparency.pipeline.intro")}</p>
          <ol className="transparency-pipeline">
            {PIPELINE_STEPS.map((step, index) => (
              <li key={step} className="transparency-pipeline__step">
                <span className="transparency-pipeline__index">{index + 1}</span>
                <div>
                  <strong>{t(`transparency.pipeline.steps.${step}.title`)}</strong>
                  <p>{t(`transparency.pipeline.steps.${step}.body`)}</p>
                </div>
              </li>
            ))}
          </ol>
        </TransparencySection>

        <TransparencySection id="inputs" title={t("transparency.sections.inputs")}>
          <p>{t("transparency.inputs.p1")}</p>
          <ul className="transparency-list">
            <li>{t("transparency.inputs.seedTopics")}</li>
            <li>{t("transparency.inputs.researchArea")}</li>
            <li>{t("transparency.inputs.expectedOutput")}</li>
            <li>{t("transparency.inputs.depth")}</li>
            <li>{t("transparency.inputs.constraints")}</li>
          </ul>
          <p>{t("transparency.inputs.profile")}</p>
          <MathBlock caption={t("transparency.inputs.expansionCaption")}>
            <span className="math-line">T* = unique(T_seed ∪ T_learned ∪ T_techniques)</span>
          </MathBlock>
        </TransparencySection>

        <TransparencySection id="retrieval" title={t("transparency.sections.retrieval")}>
          <p>{t("transparency.retrieval.p1")}</p>
          <ul className="transparency-list transparency-list--inline">
            {LITERATURE_SOURCES.map((source) => (
              <li key={source}>{source}</li>
            ))}
          </ul>
          <p>{t("transparency.retrieval.p2")}</p>
          <p>{t("transparency.retrieval.dualPass")}</p>
          <p>{t("transparency.retrieval.hybridNote", { quota: formatPct(HYBRID_RETRIEVAL.sotaQuota) })}</p>
        </TransparencySection>

        <TransparencySection id="relevance" title={t("transparency.sections.relevance")}>
          <p>{t("transparency.relevance.intro")}</p>
          <MathBlock caption={t("transparency.relevance.overlapCaption")}>
            <span className="math-line">O(A, Q) = |A ∩ Q| / |Q|</span>
            <span className="math-line math-line--sub">
              {t("transparency.relevance.tokenNote")}
            </span>
          </MathBlock>
          <MathBlock caption={t("transparency.relevance.scoreCaption")}>
            <span className="math-line">
              s_rel(p) = {rel.titleWeight}·O(T_title, Q) + {rel.bodyWeight}·O(T_body, Q) + b_cite −
              p_avoid
            </span>
            <span className="math-line math-line--sub">
              b_cite = min(ln(1 + c) / {rel.citationLogDivisor}, {rel.citationBoostMax})
            </span>
            <span className="math-line math-line--sub">
              p_avoid = {rel.avoidPenalty} {t("transparency.relevance.ifAvoidedOverlap")}
            </span>
          </MathBlock>
          <p>{t("transparency.relevance.filter", { min: rel.minKeepScore })}</p>
          <p>{t("transparency.relevance.weakCap", { cap: rel.weakOverlapCap })}</p>
        </TransparencySection>

        <TransparencySection id="embeddings" title={t("transparency.sections.embeddings")}>
          <p>{t("transparency.embeddings.p1")}</p>
          <MathBlock caption={t("transparency.embeddings.formulaCaption")}>
            <span className="math-line">e_d = Embed(title_d ∥ abstract_d)</span>
          </MathBlock>
          <p>{t("transparency.embeddings.p2")}</p>
        </TransparencySection>

        <TransparencySection id="generation" title={t("transparency.sections.generation")}>
          <p>{t("transparency.generation.p1")}</p>
          <ul className="transparency-list">
            <li>{t("transparency.generation.rule1")}</li>
            <li>{t("transparency.generation.rule2")}</li>
            <li>{t("transparency.generation.rule3")}</li>
          </ul>
          <p>{t("transparency.generation.p2")}</p>
        </TransparencySection>

        <TransparencySection id="ideaScores" title={t("transparency.sections.ideaScores")}>
          <p>{t("transparency.ideaScores.intro")}</p>
          <ul className="transparency-list">
            {IDEA_SCORE_DIMENSIONS.map((dim) => (
              <li key={dim}>
                <strong>{t(`transparency.dimensions.${dim}`)}</strong>
                {" — "}
                {t(`transparency.dimensionDesc.${dim}`)}
              </li>
            ))}
          </ul>
          <p className="transparency-note">{t("transparency.ideaScores.llmNote")}</p>
        </TransparencySection>

        <TransparencySection id="finalScore" title={t("transparency.sections.finalScore")}>
          <p>{t("transparency.finalScore.intro")}</p>
          <MathBlock caption={t("transparency.finalScore.verifiedCaption")}>
            <span className="math-line">
              S_verified = Σ w_i · dim_i + w_sota · SOTA_fit + w_nov · novelty_verified
            </span>
          </MathBlock>
          <WeightTable rows={VERIFIED_RANKING_WEIGHTS} labelPrefix="transparency.dimensions" />
          <p>{t("transparency.finalScore.verifiedNote")}</p>
          <p className="transparency-note">{t("transparency.finalScore.legacyNote")}</p>
          <WeightTable rows={FINAL_RANKING_WEIGHTS} labelPrefix="transparency.dimensions" />
          <p>{t("transparency.finalScore.sort")}</p>
        </TransparencySection>

        <TransparencySection id="feedback" title={t("transparency.sections.feedback")}>
          <p>{t("transparency.feedback.intro")}</p>
          <MathBlock caption={t("transparency.feedback.easCaption")}>
            <span className="math-line">
              EAS = 0.25·U + 0.20·R + 0.20·C + 0.15·F + 0.10·T + 0.10·W
            </span>
          </MathBlock>
          <WeightTable rows={EAS_WEIGHTS} labelPrefix="transparency.feedbackDims" />
          <p>{t("transparency.feedback.wouldUse")}</p>
          <ul className="transparency-list">
            <li>{t("transparency.feedback.wouldUseYes", { score: WOULD_USE_SCORES.yes })}</li>
            <li>{t("transparency.feedback.wouldUseMaybe", { score: WOULD_USE_SCORES.maybe })}</li>
            <li>{t("transparency.feedback.wouldUseNo", { score: WOULD_USE_SCORES.no })}</li>
          </ul>
          <p>{t("transparency.feedback.profileLoop")}</p>
        </TransparencySection>

        <TransparencySection id="limitations" title={t("transparency.sections.limitations")}>
          <ul className="transparency-list">
            <li>{t("transparency.limitations.l1")}</li>
            <li>{t("transparency.limitations.l2")}</li>
            <li>{t("transparency.limitations.l3")}</li>
            <li>{t("transparency.limitations.l4")}</li>
            <li>{t("transparency.limitations.l5")}</li>
          </ul>
        </TransparencySection>
      </article>
      </div>
    </div>
  );
}
