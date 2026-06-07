import { Badge, Card, ListGroup } from "react-bootstrap";
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
    return <p className="text-secondary small mb-0">{t("evidence.noArticles")}</p>;
  }

  return (
    <div>
      <h6 className="fw-semibold">{heading}</h6>
      <p className="text-secondary small">{t("evidence.articlesCited", { count: papers.length })}</p>
      {papers.map((paper, index) => (
        <Card key={`${paper.title}-${index}`} className="surface-card surface-card--soft border-0 mb-2">
          <Card.Body className="py-3">
            <div className="d-flex justify-content-between gap-2">
              <strong>
                {index + 1}. {paper.title ?? t("common.untitled")}
              </strong>
              {paper.retrieval_source ? (
                <Badge bg="secondary">{sourceLabel(paper.retrieval_source)}</Badge>
              ) : null}
            </div>
            <div className="text-secondary small mt-1">
              {[
                paper.year,
                paper.venue,
                paper.citation_count != null
                  ? t("common.citations", { count: paper.citation_count })
                  : null,
              ]
                .filter(Boolean)
                .join(" · ")}
            </div>
            {paper.why_relevant ? <p className="small mt-2 mb-2">{paper.why_relevant}</p> : null}
            <div className="d-flex gap-2">
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
              <details className="mt-2">
                <summary className="small">{t("common.abstract")}</summary>
                <p className="small text-secondary mb-0 mt-2">{paper.abstract}</p>
              </details>
            ) : null}
          </Card.Body>
        </Card>
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
    return <p className="text-secondary small mb-0">{t("evidence.catalogUnavailable")}</p>;
  }

  const counts = sources.reduce<Record<string, number>>((acc, doc) => {
    const key = doc.source ?? "unknown";
    acc[key] = (acc[key] ?? 0) + 1;
    return acc;
  }, {});

  return (
    <div>
      <p className="text-secondary small">{t("evidence.papersUsed", { count: sources.length })}</p>
      <div className="d-flex flex-wrap gap-2 mb-3">
        {Object.entries(counts).map(([source, count]) => (
          <Badge key={source} bg="light" text="dark" className="border">
            {sourceLabel(source)}: {count}
          </Badge>
        ))}
      </div>
      <ListGroup variant="flush">
        {sources.map((doc, index) => (
          <ListGroup.Item key={`${doc.title}-${index}`} className="px-0">
            <Badge bg="secondary" className="me-2">
              {sourceLabel(doc.source)}
            </Badge>
            <strong>{doc.title ?? t("common.untitled")}</strong>
            {doc.year ? ` (${doc.year})` : ""}
          </ListGroup.Item>
        ))}
      </ListGroup>
    </div>
  );
}
