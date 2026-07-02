import { useTranslation } from "react-i18next";

import { MathBlock } from "@/features/transparency/components/MathBlock";
import { NotationTable } from "@/features/transparency/components/NotationTable";
import { TransparencySection } from "@/features/transparency/components/TransparencySection";
import { WeightTable } from "@/features/transparency/components/WeightTable";
import { PageHeader } from "@/shared/ui/PageHeader";
import {
  EAS_WEIGHTS,
  FGGV_WEIGHTS,
  FINAL_RANKING_WEIGHTS,
  HYBRID_RETRIEVAL,
  IDEA_SCORE_DIMENSIONS,
  LITERATURE_SOURCES,
  PAPER_RELEVANCE,
  PIPELINE_STEPS,
  SOTA_TIER_DEFAULTS,
  VERIFIED_RANKING_WEIGHTS,
  WOULD_USE_SCORES,
} from "@/features/transparency/constants/transparencyModel";

const TOC_SECTIONS = [
  "overview",
  "contributions",
  "pipeline",
  "notation",
  "inputs",
  "retrieval",
  "sotaTiers",
  "relevance",
  "embeddings",
  "landscape",
  "generation",
  "ideaScores",
  "finalScore",
  "fggv",
  "feedback",
  "evaluation",
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
            <li>{t("transparency.overview.bullet4")}</li>
          </ul>
        </TransparencySection>

        <TransparencySection id="contributions" title={t("transparency.sections.contributions")}>
          <p>{t("transparency.contributions.intro")}</p>
          <ul className="transparency-list">
            <li>{t("transparency.contributions.c1")}</li>
            <li>{t("transparency.contributions.c2")}</li>
            <li>{t("transparency.contributions.c3")}</li>
            <li>{t("transparency.contributions.c4")}</li>
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

        <TransparencySection id="notation" title={t("transparency.sections.notation")} collapsible defaultOpen={false}>
          <p>{t("transparency.notation.intro")}</p>
          <NotationTable />
          <MathBlock caption={t("transparency.notation.expansionCaption")}>
            <span className="math-line">T* = unique(T_seed ∪ T_learned ∪ T_techniques)</span>
            <span className="math-line math-line--sub">
              P = {"{ p | s_rel(p) ≥ τ_rel }"}, default τ_rel = {PAPER_RELEVANCE.minKeepScore}
            </span>
          </MathBlock>
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

        <TransparencySection id="sotaTiers" title={t("transparency.sections.sotaTiers")}>
          <p>{t("transparency.sotaTiers.intro")}</p>
          <ul className="transparency-list">
            <li>{t("transparency.sotaTiers.recent", { years: SOTA_TIER_DEFAULTS.recentYears })}</li>
            <li>
              {t("transparency.sotaTiers.seminal", { citations: SOTA_TIER_DEFAULTS.seminalCitations })}
            </li>
            <li>{t("transparency.sotaTiers.quota", { quota: formatPct(SOTA_TIER_DEFAULTS.tierQuota) })}</li>
          </ul>
          <p>{t("transparency.sotaTiers.audit")}</p>
        </TransparencySection>

        <TransparencySection id="relevance" title={t("transparency.sections.relevance")} collapsible defaultOpen={false}>
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

        <TransparencySection id="embeddings" title={t("transparency.sections.embeddings")} collapsible defaultOpen={false}>
          <p>{t("transparency.embeddings.p1")}</p>
          <MathBlock caption={t("transparency.embeddings.formulaCaption")}>
            <span className="math-line">e_d = Embed(title_d ∥ abstract_d)</span>
          </MathBlock>
          <p>{t("transparency.embeddings.p2")}</p>
        </TransparencySection>

        <TransparencySection id="landscape" title={t("transparency.sections.landscape")}>
          <p>{t("transparency.landscape.intro")}</p>
          <ol className="transparency-list">
            <li>{t("transparency.landscape.step1")}</li>
            <li>{t("transparency.landscape.step2")}</li>
            <li>{t("transparency.landscape.step3")}</li>
            <li>{t("transparency.landscape.step4")}</li>
          </ol>
          <p>{t("transparency.landscape.gapNote")}</p>
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

        <TransparencySection id="finalScore" title={t("transparency.sections.finalScore")} collapsible defaultOpen={false}>
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

        <TransparencySection id="fggv" title={t("transparency.sections.fggv")} collapsible defaultOpen={false}>
          <p>{t("transparency.fggv.intro")}</p>
          <ul className="transparency-list">
            <li>{t("transparency.fggv.lfm")}</li>
            <li>{t("transparency.fggv.gfa")}</li>
            <li>{t("transparency.fggv.cfn")}</li>
            <li>{t("transparency.fggv.fds")}</li>
          </ul>
          <MathBlock caption={t("transparency.fggv.formulaCaption")}>
            <span className="math-line">
              FGGV = {FGGV_WEIGHTS.verifiedBase}·S_verified + {FGGV_WEIGHTS.fni}·FNI +{" "}
              {FGGV_WEIGHTS.gfa}·GFA + {FGGV_WEIGHTS.documentNovelty}·document_novelty
            </span>
            <span className="math-line math-line--sub">FNI_f = 1 − max sim(facet_f, LFM_f)</span>
          </MathBlock>
          <p className="transparency-note">{t("transparency.fggv.modeNote")}</p>
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

        <TransparencySection id="evaluation" title={t("transparency.sections.evaluation")} collapsible defaultOpen={false}>
          <p>{t("transparency.evaluation.intro")}</p>
          <ul className="transparency-list">
            <li>{t("transparency.evaluation.online")}</li>
            <li>{t("transparency.evaluation.offline")}</li>
            <li>{t("transparency.evaluation.expert")}</li>
          </ul>
          <p className="transparency-note">{t("transparency.evaluation.docNote")}</p>
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
