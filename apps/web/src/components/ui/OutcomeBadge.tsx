import { Badge } from "react-bootstrap";
import { useTranslation } from "react-i18next";

import type { RunOutcome } from "../../utils/runs";

interface OutcomeBadgeProps {
  outcome: RunOutcome;
}

const VARIANTS: Record<RunOutcome, string> = {
  ready: "success",
  in_progress: "primary",
  failed: "danger",
  incomplete: "warning",
};

export function OutcomeBadge({ outcome }: OutcomeBadgeProps) {
  const { t } = useTranslation();
  const variant = VARIANTS[outcome];
  const label = t(`status.${outcome}`);

  return <Badge bg={variant}>{label}</Badge>;
}
