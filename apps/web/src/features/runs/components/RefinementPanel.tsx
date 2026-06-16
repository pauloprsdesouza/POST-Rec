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
      <ul className="refinement-panel__list">
        {items.map((item) => (
          <li key={item.id} className="refinement-panel__item">
            <span className="refinement-panel__item-title">{item.title}</span>
          </li>
        ))}
      </ul>
    </aside>
  );
}
