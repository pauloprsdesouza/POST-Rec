import { useTranslation } from "react-i18next";

export type RunsFilter = "all" | "ready" | "active";

interface RunsStatsStripProps {
  total: number;
  active: number;
  ready: number;
  filter: RunsFilter;
  onFilterChange: (filter: RunsFilter) => void;
}

export function RunsStatsStrip({ total, active, ready, filter, onFilterChange }: RunsStatsStripProps) {
  const { t } = useTranslation();

  const items: { id: RunsFilter; label: string; count: number }[] = [
    { id: "all", label: t("runs.filterAll"), count: total },
    { id: "ready", label: t("runs.filterReady"), count: ready },
    { id: "active", label: t("runs.filterActive"), count: active },
  ];

  return (
    <div className="segmented-control" role="tablist" aria-label={t("runs.filterLabel")}>
      {items.map((item) => {
        const selected = filter === item.id;
        return (
          <button
            key={item.id}
            type="button"
            role="tab"
            aria-selected={selected}
            className={`segmented-control__item ${selected ? "segmented-control__item--selected" : ""}`}
            onClick={() => onFilterChange(item.id)}
          >
            <span className="segmented-control__count">{item.count}</span>
            {item.label}
          </button>
        );
      })}
    </div>
  );
}
