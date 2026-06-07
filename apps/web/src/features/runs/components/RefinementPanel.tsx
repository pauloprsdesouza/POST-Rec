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
    <aside className="refinement-panel">
      <h3 className="refinement-panel__title">{t("ideas.refinement.title")}</h3>
      <p className="refinement-panel__subtitle">{t("ideas.refinement.subtitle", { count: items.length })}</p>
      <div>
        {items.map((item) => (
          <div key={item.id} className="refinement-panel__item">
            <div className="refinement-panel__item-title">{item.title}</div>
            {item.validation_issues?.length ? (
              <ul className="refinement-panel__issues mb-0">
                {item.validation_issues.map((issue) => (
                  <li key={issue}>{issue}</li>
                ))}
              </ul>
            ) : null}
          </div>
        ))}
      </div>
    </aside>
  );
}
