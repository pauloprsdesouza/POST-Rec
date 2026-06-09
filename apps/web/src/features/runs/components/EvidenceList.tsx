import { Badge } from "react-bootstrap";
import { useTranslation } from "react-i18next";

import { useEnumLabel } from "@/shared/i18n/useEnumLabel";
import type { EvidencePaper, SourceDocument } from "@/shared/types/api";

interface EvidenceListProps {
  papers?: EvidencePaper[];
  title?: string;
}

export function EvidenceList({ papers, title }: EvidenceListProps) {
  const { t } = useTranslation();
  const sourceLabel = useEnumLabel("enums.sources");
  const heading = title ?? t("evidence.supportingArticles");

  if (!papers?.length) {
    return <p className="evidence-empty">{t("evidence.noArticles")}</p>;
  }

  return (
    <div className="evidence-section">
      <h3 className="evidence-section__heading">{heading}</h3>
      <p className="evidence-section__meta">{t("evidence.articlesCited", { count: papers.length })}</p>
      {papers.map((paper, index) => (
        <article key={`${paper.title}-${index}`} className="evidence-card">
          <div className="d-flex justify-content-between gap-2">
            <strong className="evidence-card__title">
              {index + 1}. {paper.title ?? t("common.untitled")}
            </strong>
            {paper.retrieval_source ? (
              <Badge bg="secondary">{sourceLabel(paper.retrieval_source)}</Badge>
            ) : null}
          </div>
          <div className="evidence-card__meta">
            {[
              paper.year,
              paper.venue,
              paper.citation_count != null ? t("common.citations", { count: paper.citation_count }) : null,
            ]
              .filter(Boolean)
              .join(" · ")}
          </div>
          {paper.why_relevant ? <p className="evidence-card__relevance mb-0">{paper.why_relevant}</p> : null}
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
          {paper.abstract ? (
            <details className="evidence-card__abstract mt-3">
              <summary>{t("common.abstract")}</summary>
              <p>{paper.abstract}</p>
            </details>
          ) : null}
        </article>
      ))}
    </div>
  );
}

interface SourceCatalogProps {
  sources?: SourceDocument[];
}

export function SourceCatalog({ sources }: SourceCatalogProps) {
  const { t } = useTranslation();
  const sourceLabel = useEnumLabel("enums.sources");

  if (!sources?.length) {
    return <p className="evidence-empty">{t("evidence.catalogUnavailable")}</p>;
  }

  const counts = sources.reduce<Record<string, number>>((acc, doc) => {
    const key = doc.source ?? "unknown";
    acc[key] = (acc[key] ?? 0) + 1;
    return acc;
  }, {});

  return (
    <div className="source-catalog">
      <p className="source-catalog__meta">{t("evidence.papersUsed", { count: sources.length })}</p>
      <div className="source-catalog__chips">
        {Object.entries(counts).map(([source, count]) => (
          <span key={source} className="source-catalog__chip">
            {sourceLabel(source)}: {count}
          </span>
        ))}
      </div>
      <ul className="source-catalog__list">
        {sources.map((doc, index) => (
          <li key={`${doc.title}-${index}`} className="source-catalog__item">
            <Badge bg="secondary" className="me-2">
              {sourceLabel(doc.source)}
            </Badge>
            <strong>{doc.title ?? t("common.untitled")}</strong>
            {doc.year ? ` (${doc.year})` : ""}
          </li>
        ))}
      </ul>
    </div>
  );
}
