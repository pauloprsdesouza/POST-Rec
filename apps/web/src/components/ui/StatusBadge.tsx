import { Badge } from "react-bootstrap";
import { useTranslation } from "react-i18next";

interface StatusBadgeProps {
  status: string;
}

const VARIANTS: Record<string, string> = {
  completed: "success",
  failed: "danger",
  cancelled: "secondary",
  queued: "secondary",
  cost_limit_exceeded: "warning",
  failed_schema_validation: "danger",
};

function humanizeStatus(status: string): string {
  return status.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

export function StatusBadge({ status }: StatusBadgeProps) {
  const { t } = useTranslation();
  const variant = VARIANTS[status] ?? "primary";
  const label = t(`status.${status}`, { defaultValue: humanizeStatus(status) });

  return <Badge bg={variant}>{label}</Badge>;
}
