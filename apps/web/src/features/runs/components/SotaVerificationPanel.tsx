import { useTranslation } from "react-i18next";

import type { Recommendation, SotaAnchor, SourceDocument } from "@/shared/types/api";

import { PaperRefText } from "./PaperRefText";
import { ScoreBar } from "./ScoreBar";

interface SotaVerificationPanelProps {
  recommendation: Recommendation;
  sources?: SourceDocument[];
}

export function SotaVerificationPanel({
  recommendation,
  sources = [],
}: SotaVerificationPanelProps) {
  const { t } = useTranslation();

  const hasNarrative =
    recommendation.sota_summary ||
    recommendation.novelty_delta ||
    recommendation.closest_prior_work ||
    recommendation.differentiation_score_rationale;

  const hasSignals = recommendation.novelty_verified != null || recommendation.sota_fit != null;
  const hasPapers = (recommendation.sota_anchors?.length ?? 0) > 0;

  if (!hasNarrative && !hasSignals && !hasPapers) {
    return null;
  }

  const sourceByTitle = new Map(
    sources.filter((s) => s.title).map((s) => [s.title!.toLowerCase(), s]),
  );

  return (
    <section className="idea-verification" aria-labelledby="idea-verification-title">
      <header className="idea-verification__header">
        <div>
          <h3 className="idea-verification__title" id="idea-verification-title">
            {t("ideas.ideaVerification.title")}
          </h3>
          <p className="idea-verification__intro">{t("ideas.ideaVerification.intro")}</p>
        </div>
        {recommendation.novelty_verified != null && recommendation.novelty_verified >= 0.6 ? (
          <span className="idea-verification__badge">{t("ideas.ideaVerification.verifiedBadge")}</span>
        ) : null}
      </header>

      {hasNarrative ? (
        <div className="idea-verification__blocks">
          {recommendation.sota_summary ? (
            <VerificationBlock
              label={t("ideas.ideaVerification.literatureContext")}
              value={recommendation.sota_summary}
            />
          ) : null}
          {recommendation.novelty_delta ? (
            <VerificationBlock
              label={t("ideas.ideaVerification.whatsNew")}
              value={recommendation.novelty_delta}
            />
          ) : null}
          {recommendation.closest_prior_work ? (
            <VerificationBlock
              label={t("ideas.ideaVerification.closestWork")}
              value={recommendation.closest_prior_work}
            />
          ) : null}
          {recommendation.differentiation_score_rationale ? (
            <VerificationBlock
              label={t("ideas.ideaVerification.howItDiffers")}
              value={recommendation.differentiation_score_rationale}
            />
          ) : null}
        </div>
      ) : null}

      {hasSignals ? (
        <div className="idea-verification__signals">
          {recommendation.novelty_verified != null ? (
            <ScoreBar
              label={t("ideas.ideaVerification.noveltyConfidence")}
              value={recommendation.novelty_verified}
            />
          ) : null}
          {recommendation.sota_fit != null ? (
            <ScoreBar
              label={t("ideas.ideaVerification.literatureAlignment")}
              value={recommendation.sota_fit}
            />
          ) : null}
        </div>
      ) : null}

      {hasPapers ? (
        <div className="idea-verification__papers">
          <p className="idea-verification__papers-label">{t("ideas.ideaVerification.keyPapers")}</p>
          <ul className="idea-verification__paper-list">
            {recommendation.sota_anchors!.map((anchor) => (
              <li key={`${anchor.title}-${anchor.year ?? "na"}`}>
                <AnchorItem anchor={anchor} source={sourceByTitle.get((anchor.title ?? "").toLowerCase())} />
              </li>
            ))}
          </ul>
        </div>
      ) : null}
    </section>
  );
}

function VerificationBlock({ label, value }: { label: string; value: string }) {
  return (
    <div className="idea-verification__block">
      <p className="idea-verification__block-label">{label}</p>
      <p className="idea-verification__block-text">
        <PaperRefText text={value} />
      </p>
    </div>
  );
}

function AnchorItem({
  anchor,
  source,
}: {
  anchor: SotaAnchor;
  source?: SourceDocument;
}) {
  const content = (
    <>
      <span className="idea-verification__paper-title">{anchor.title}</span>
      {anchor.year ? <span className="idea-verification__paper-year">{anchor.year}</span> : null}
    </>
  );

  if (source?.url || anchor.url) {
    return (
      <a
        className="idea-verification__paper-link"
        href={source?.url ?? anchor.url ?? "#"}
        target="_blank"
        rel="noreferrer"
      >
        {content}
      </a>
    );
  }

  return <div className="idea-verification__paper-link idea-verification__paper-link--static">{content}</div>;
}
