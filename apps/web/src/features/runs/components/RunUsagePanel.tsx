import { useTranslation } from "react-i18next";

import type { RecommendationRun, RunUsageSummary } from "@/shared/types/api";
import { formatEstimatedCost } from "@/features/runs/utils/formatCost";

interface RunUsagePanelProps {
  run: RecommendationRun;
}

function formatTokenCount(value: number, locale: string): string {
  return new Intl.NumberFormat(locale).format(value);
}

export function RunUsagePanel({ run }: RunUsagePanelProps) {
  const { t, i18n } = useTranslation();
  const usage: RunUsageSummary | null | undefined = run.usage;

  if (!usage) {
    return null;
  }

  const hasUsage = usage.lines.length > 0 || usage.estimated_cost_usd > 0;
  if (!hasUsage) {
    return null;
  }

  const locale = i18n.language;
  const totalCost = formatEstimatedCost(usage.estimated_cost_usd, locale);
  const avgCost =
    usage.estimated_cost_per_recommendation_usd != null
      ? formatEstimatedCost(usage.estimated_cost_per_recommendation_usd, locale)
      : null;

  return (
    <details className="run-usage panel">
      <summary className="run-usage__summary">{t("usage.summary", { cost: totalCost })}</summary>

      <div className="run-usage__body">
        <p className="run-usage__note">{t("usage.estimatedNote")}</p>

        <div className="run-usage__stats">
          <div className="run-usage__stat">
            <span className="run-usage__stat-label">{t("usage.totalCost")}</span>
            <span className="run-usage__stat-value">{totalCost}</span>
          </div>
          <div className="run-usage__stat">
            <span className="run-usage__stat-label">{t("usage.inputTokens")}</span>
            <span className="run-usage__stat-value">
              {formatTokenCount(usage.input_tokens, locale)}
            </span>
          </div>
          <div className="run-usage__stat">
            <span className="run-usage__stat-label">{t("usage.outputTokens")}</span>
            <span className="run-usage__stat-value">
              {formatTokenCount(usage.output_tokens, locale)}
            </span>
          </div>
          {avgCost ? (
            <div className="run-usage__stat">
              <span className="run-usage__stat-label">{t("usage.avgPerIdea")}</span>
              <span className="run-usage__stat-value">{avgCost}</span>
            </div>
          ) : null}
        </div>

        {usage.lines.length > 0 ? (
          <div className="run-usage__breakdown">
            <h3 className="run-usage__breakdown-title">{t("usage.breakdown")}</h3>
            <ul className="run-usage__lines">
              {usage.lines.map((line) => (
                <li key={`${line.operation}-${line.model}`} className="run-usage__line">
                  <div className="run-usage__line-top">
                    <span className="run-usage__line-label">
                      {t(`usage.operations.${line.operation}`, {
                        defaultValue: line.operation.replace(/_/g, " "),
                      })}
                    </span>
                    <span className="run-usage__line-cost">
                      {formatEstimatedCost(line.estimated_cost_usd, locale)}
                    </span>
                  </div>
                  <div className="run-usage__line-meta">
                    <span>{line.model}</span>
                    <span>
                      {t("usage.lineTokens", {
                        input: formatTokenCount(line.input_tokens, locale),
                        output: formatTokenCount(line.output_tokens, locale),
                        total: formatTokenCount(line.total_tokens, locale),
                      })}
                    </span>
                  </div>
                </li>
              ))}
            </ul>
            <p className="run-usage__shared-note">{t("usage.sharedGenerationNote")}</p>
          </div>
        ) : null}
      </div>
    </details>
  );
}
