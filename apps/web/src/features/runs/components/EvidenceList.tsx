import { useTranslation } from "react-i18next";

import { EvidenceCard } from "./EvidenceCard";
import { QualisEstratoBadge } from "@/shared/ui/QualisEstratoBadge";
import { SourceBadge } from "@/shared/ui/SourceBadge";
import type { EvidencePaper, SourceDocument } from "@/shared/types/api";

interface EvidenceListProps {
  papers?: EvidencePaper[];
  title?: string;
}

export function EvidenceList({ papers, title }: EvidenceListProps) {
  const { t } = useTranslation();
  const heading = title ?? t("evidence.supportingArticles");

  if (!papers?.length) {
    return <p className="evidence-empty">{t("evidence.noArticles")}</p>;
  }

  const explainedCount = papers.filter((paper) => paper.why_relevant?.trim()).length;

  return (
    <div className="evidence-section">
      <div className="evidence-section__intro">
        <h3 className="evidence-section__heading">{heading}</h3>
        <p className="evidence-section__meta">
          {t("evidence.articlesCited", { count: papers.length })}
          {explainedCount > 0 ? ` · ${t("evidence.explainedCount", { count: explainedCount })}` : null}
        </p>
        <p className="evidence-section__hint">{t("evidence.intro")}</p>
      </div>
      <ul className="evidence-section__list">
        {papers.map((paper, index) => (
          <li key={`${paper.title}-${index}`}>
            <EvidenceCard paper={paper} index={index} />
          </li>
        ))}
      </ul>
    </div>
  );
}

interface SourceCatalogProps {
  sources?: SourceDocument[];
}

export function SourceCatalog({ sources }: SourceCatalogProps) {
  const { t } = useTranslation();

  if (!sources?.length) {
    return <p className="evidence-empty">{t("evidence.catalogUnavailable")}</p>;
  }

  const counts = sources.reduce<Record<string, number>>((acc, doc) => {
    const key = doc.source ?? "unknown";
    acc[key] = (acc[key] ?? 0) + 1;
    return acc;
  }, {});

  const qualisCount = sources.filter((doc) => doc.qualis_estrato?.trim()).length;

  return (
    <div className="source-catalog">
      <p className="source-catalog__meta">
        {t("evidence.papersUsed", { count: sources.length })}
        {qualisCount > 0 ? ` · ${t("evidence.qualisCount", { count: qualisCount })}` : null}
      </p>
      <div className="source-catalog__chips">
        {Object.entries(counts).map(([source, count]) => (
          <span key={source} className="source-catalog__chip">
            <SourceBadge source={source} compact />
            <span className="source-catalog__chip-count">{count}</span>
          </span>
        ))}
      </div>
      <ul className="source-catalog__list">
        {sources.map((doc, index) => {
          const metaParts = [
            doc.venue,
            doc.year,
            doc.citation_count != null ? t("common.citations", { count: doc.citation_count }) : null,
          ].filter(Boolean);

          return (
            <li key={`${doc.id ?? doc.title}-${index}`} className="source-catalog__item">
              <div className="source-catalog__item-head">
                <div className="source-catalog__item-signals">
                  <SourceBadge source={doc.source} compact />
                  {doc.qualis_estrato?.trim() ? (
                    <QualisEstratoBadge estrato={doc.qualis_estrato} />
                  ) : null}
                </div>
                <strong className="source-catalog__item-title">{doc.title ?? t("common.untitled")}</strong>
              </div>
              {metaParts.length ? <p className="source-catalog__item-meta">{metaParts.join(" · ")}</p> : null}
            </li>
          );
        })}
      </ul>
    </div>
  );
}
