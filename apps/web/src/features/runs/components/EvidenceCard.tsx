import { useId, useLayoutEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";

import { QualisEstratoBadge } from "@/shared/ui/QualisEstratoBadge";
import { SourceBadge } from "@/shared/ui/SourceBadge";
import type { EvidencePaper } from "@/shared/types/api";

type RelevanceTier = "high" | "medium" | "low";

function normalizeRelevanceScore(score: number | undefined): number | null {
  if (score == null || Number.isNaN(score)) {
    return null;
  }
  const value = score > 1 ? score / 100 : score;
  return Math.max(0, Math.min(1, value));
}

function relevanceTier(score: number): RelevanceTier {
  if (score >= 0.7) {
    return "high";
  }
  if (score >= 0.45) {
    return "medium";
  }
  return "low";
}

function EvidenceRelevanceMeter({ score }: { score: number }) {
  const { t } = useTranslation();
  const normalized = normalizeRelevanceScore(score)!;
  const tier = relevanceTier(normalized);
  const percent = Math.round(normalized * 100);

  return (
    <div
      className={`evidence-relevance-meter evidence-relevance-meter--${tier}`}
      title={t("evidence.relevanceScoreTooltip", { percent })}
    >
      <span className="evidence-relevance-meter__label">{t(`evidence.relevanceTier.${tier}`)}</span>
      <div
        className="evidence-relevance-meter__track"
        role="meter"
        aria-valuenow={percent}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label={t("evidence.relevanceScoreAria", { percent })}
      >
        <div className="evidence-relevance-meter__fill" style={{ width: `${percent}%` }} />
      </div>
      <span className="evidence-relevance-meter__value">{percent}%</span>
    </div>
  );
}

function EvidenceRelevanceNote({ text }: { text: string }) {
  const { t } = useTranslation();
  const bodyId = useId();
  const textRef = useRef<HTMLParagraphElement>(null);
  const [expanded, setExpanded] = useState(false);
  const [clampable, setClampable] = useState(false);

  useLayoutEffect(() => {
    const node = textRef.current;
    if (!node) {
      return;
    }
    setClampable(node.scrollHeight > node.clientHeight + 1);
  }, [text, expanded]);

  return (
    <section className="evidence-card__relevance" aria-labelledby={`${bodyId}-label`}>
      <div className="evidence-card__relevance-head">
        <p id={`${bodyId}-label`} className="evidence-card__relevance-label">
          {t("evidence.whyRelevant")}
        </p>
      </div>
      <blockquote className="evidence-card__relevance-quote">
        <p
          ref={textRef}
          id={bodyId}
          className={`evidence-card__relevance-text ${expanded ? "evidence-card__relevance-text--expanded" : ""}`}
        >
          {text}
        </p>
      </blockquote>
      {clampable ? (
        <button
          type="button"
          className="evidence-card__relevance-toggle btn btn-link btn-sm px-0"
          aria-expanded={expanded}
          aria-controls={bodyId}
          onClick={() => setExpanded((open) => !open)}
        >
          {expanded ? t("evidence.showLess") : t("evidence.showMore")}
        </button>
      ) : null}
    </section>
  );
}

function EvidenceSignals({ paper }: { paper: EvidencePaper }) {
  const hasQualis = Boolean(paper.qualis_estrato?.trim());
  const hasSource = Boolean(paper.retrieval_source?.trim());

  if (!hasQualis && !hasSource) {
    return null;
  }

  return (
    <div className="evidence-card__signals">
      {hasQualis ? (
        <QualisEstratoBadge estrato={paper.qualis_estrato!} period={paper.qualis_period} />
      ) : null}
      {hasSource ? <SourceBadge source={paper.retrieval_source} /> : null}
    </div>
  );
}

interface EvidenceCardProps {
  paper: EvidencePaper;
  index: number;
}

export function EvidenceCard({ paper, index }: EvidenceCardProps) {
  const { t } = useTranslation();
  const relevanceScore = normalizeRelevanceScore(paper.relevance_score);
  const primaryLink = paper.doi
    ? paper.doi.startsWith("http")
      ? paper.doi
      : `https://doi.org/${paper.doi}`
    : paper.url;

  const metaParts = [
    paper.venue,
    paper.year,
    paper.citation_count != null ? t("common.citations", { count: paper.citation_count }) : null,
  ].filter(Boolean);

  return (
    <article className="evidence-card">
      <header className="evidence-card__header">
        <span className="evidence-card__index" aria-hidden>
          {index + 1}
        </span>
        <div className="evidence-card__identity">
          {primaryLink ? (
            <a
              href={primaryLink}
              target="_blank"
              rel="noreferrer"
              className="evidence-card__title evidence-card__title--link"
            >
              {paper.title ?? t("common.untitled")}
            </a>
          ) : (
            <h4 className="evidence-card__title">{paper.title ?? t("common.untitled")}</h4>
          )}
          {metaParts.length ? <p className="evidence-card__meta">{metaParts.join(" · ")}</p> : null}
        </div>
      </header>

      {paper.why_relevant?.trim() ? (
        <EvidenceRelevanceNote text={paper.why_relevant.trim()} />
      ) : (
        <p className="evidence-card__relevance-missing">{t("evidence.noRelevance")}</p>
      )}

      <footer className="evidence-card__footer">
        <div className="evidence-card__footer-main">
          <EvidenceSignals paper={paper} />
          {relevanceScore != null ? <EvidenceRelevanceMeter score={relevanceScore} /> : null}
        </div>

        {paper.doi || paper.url ? (
          <div className="evidence-card__actions">
            {paper.doi ? (
              <a
                href={paper.doi.startsWith("http") ? paper.doi : `https://doi.org/${paper.doi}`}
                target="_blank"
                rel="noreferrer"
                className="btn btn-sm btn-outline-primary"
              >
                {t("evidence.doi")}
              </a>
            ) : null}
            {paper.url ? (
              <a href={paper.url} target="_blank" rel="noreferrer" className="btn btn-sm btn-outline-secondary">
                {t("common.open")}
              </a>
            ) : null}
          </div>
        ) : null}
      </footer>

      {paper.abstract ? (
        <details className="evidence-card__abstract">
          <summary>{t("common.abstract")}</summary>
          <p>{paper.abstract}</p>
        </details>
      ) : null}
    </article>
  );
}
