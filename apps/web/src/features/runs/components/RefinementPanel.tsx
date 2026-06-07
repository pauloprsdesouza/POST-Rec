import { Alert, ListGroup } from "react-bootstrap";
import { useTranslation } from "react-i18next";

import type { Recommendation } from "@/shared/types/api";

interface RefinementPanelProps {
  items: Recommendation[];
}

export function RefinementPanel({ items }: RefinementPanelProps) {
  const { t } = useTranslation();

  if (!items.length) {
    return null;
  }

  return (
    <Alert variant="warning" className="refinement-panel mt-4">
      <h3 className="h6 mb-2">{t("ideas.refinement.title")}</h3>
      <p className="small mb-3">{t("ideas.refinement.subtitle", { count: items.length })}</p>
      <ListGroup variant="flush">
        {items.map((item) => (
          <ListGroup.Item key={item.id} className="px-0 bg-transparent border-0">
            <strong>{item.title}</strong>
            {item.validation_issues?.length ? (
              <ul className="small mb-0 mt-1">
                {item.validation_issues.map((issue) => (
                  <li key={issue}>{issue}</li>
                ))}
              </ul>
            ) : null}
          </ListGroup.Item>
        ))}
      </ListGroup>
    </Alert>
  );
}
