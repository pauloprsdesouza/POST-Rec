import { useTranslation } from "react-i18next";

import { usePaperRefs } from "@/features/runs/components/PaperRefContext";
import {
  formatPaperRefLabel,
  formatPaperRefTooltip,
  splitPaperRefText,
} from "@/features/runs/utils/paperRefs";

interface PaperRefTextProps {
  text: string;
  className?: string;
}

export function PaperRefText({ text, className }: PaperRefTextProps) {
  const { t } = useTranslation();
  const { index, onNavigateToPaper } = usePaperRefs();
  const parts = splitPaperRefText(text);

  return (
    <span className={className}>
      {parts.map((part, indexKey) => {
        if (part.type === "text") {
          return <span key={`text-${indexKey}`}>{part.value}</span>;
        }

        const entry = index.get(part.paperId);
        if (!entry) {
          return <span key={`ref-${indexKey}`}>{part.value}</span>;
        }

        const label = formatPaperRefLabel(entry);
        const tooltip = formatPaperRefTooltip(entry);

        if (entry.url) {
          return (
            <a
              key={`ref-${indexKey}`}
              className="paper-ref-link"
              href={entry.url}
              target="_blank"
              rel="noreferrer"
              title={tooltip}
              aria-label={t("ideas.paperRefOpen", { citation: tooltip })}
            >
              {label}
            </a>
          );
        }

        if (entry.inEvidence && onNavigateToPaper) {
          return (
            <button
              key={`ref-${indexKey}`}
              type="button"
              className="paper-ref-link paper-ref-link--internal"
              title={tooltip}
              aria-label={t("ideas.paperRefViewEvidence", { citation: tooltip })}
              onClick={() => onNavigateToPaper(part.paperId)}
            >
              {label}
            </button>
          );
        }

        return (
          <span key={`ref-${indexKey}`} className="paper-ref-link paper-ref-link--static" title={tooltip}>
            {label}
          </span>
        );
      })}
    </span>
  );
}
