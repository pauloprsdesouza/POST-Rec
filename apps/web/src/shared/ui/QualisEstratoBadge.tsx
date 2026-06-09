import { useTranslation } from "react-i18next";

export type QualisTier = "a" | "b" | "c";

export function qualisTier(estrato: string): QualisTier {
  const letter = estrato.trim().charAt(0).toUpperCase();
  if (letter === "A") return "a";
  if (letter === "B") return "b";
  return "c";
}

interface QualisEstratoBadgeProps {
  estrato: string;
  period?: string | null;
}

export function QualisEstratoBadge({ estrato, period }: QualisEstratoBadgeProps) {
  const { t } = useTranslation();
  const normalized = estrato.trim().toUpperCase();
  const tier = qualisTier(normalized);
  const normalizedPeriod = period?.trim() || null;
  const labelKey = normalizedPeriod ? "evidence.qualisLabelWithPeriod" : "evidence.qualisLabel";
  const tooltipKey = normalizedPeriod ? "evidence.qualisTooltipWithPeriod" : "evidence.qualisTooltip";
  const i18nParams = normalizedPeriod
    ? { estrato: normalized, period: normalizedPeriod }
    : { estrato: normalized };

  return (
    <span
      className={`qualis-badge qualis-badge--${tier}`}
      title={t(tooltipKey, i18nParams)}
      aria-label={t(labelKey, i18nParams)}
    >
      <span className="qualis-badge__label">{t("evidence.qualisPrefix")}</span>
      <span className="qualis-badge__estrato">{normalized}</span>
      {normalizedPeriod ? (
        <span className="qualis-badge__period">{normalizedPeriod}</span>
      ) : null}
    </span>
  );
}
