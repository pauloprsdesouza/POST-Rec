import { useTranslation } from "react-i18next";

import { useEnumLabel } from "@/shared/i18n/useEnumLabel";

const SOURCE_KEYS = new Set(["openalex", "arxiv", "semantic_scholar", "crossref", "unknown"]);

export function normalizeSourceKey(source: string | undefined | null): string {
  if (!source?.trim()) {
    return "unknown";
  }
  const key = source.trim().toLowerCase().replace(/\s+/g, "_");
  return SOURCE_KEYS.has(key) ? key : "unknown";
}

interface SourceBadgeProps {
  source: string | undefined | null;
  /** Show short abbreviation instead of full label (e.g. in dense lists). */
  compact?: boolean;
}

export function SourceBadge({ source, compact = false }: SourceBadgeProps) {
  const { t } = useTranslation();
  const sourceLabel = useEnumLabel("enums.sources");
  const key = normalizeSourceKey(source);
  const label = compact ? t(`evidence.sourceShort.${key}`, { defaultValue: sourceLabel(key) }) : sourceLabel(key);

  return (
    <span
      className={`source-badge source-badge--${key}`}
      title={t("evidence.sourceTooltip", { source: sourceLabel(key) })}
      aria-label={t("evidence.sourceLabel", { source: sourceLabel(key) })}
    >
      {label}
    </span>
  );
}
