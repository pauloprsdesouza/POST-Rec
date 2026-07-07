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
      <h3 className="refinement-panel__title">
        {t("ideas.refinement.title")}
        <span className="refinement-panel__count">{items.length}</span>
      </h3>
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
