import { useTranslation } from "react-i18next";

import type { RunOutcome } from "@/features/runs/utils/runs";

interface OutcomeBadgeProps {
  outcome: RunOutcome;
}

export function OutcomeBadge({ outcome }: OutcomeBadgeProps) {
  const { t } = useTranslation();
  const label = t(`status.${outcome}`);

  return <span className={`outcome-pill outcome-pill--${outcome}`}>{label}</span>;
}
