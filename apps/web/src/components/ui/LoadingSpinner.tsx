import { Spinner } from "react-bootstrap";
import { useTranslation } from "react-i18next";

interface LoadingSpinnerProps {
  label?: string;
}

export function LoadingSpinner({ label }: LoadingSpinnerProps) {
  const { t } = useTranslation();

  return (
    <div className="page-loading">
      <div className="d-flex flex-column align-items-center justify-content-center text-secondary">
        <Spinner animation="border" role="status" className="mb-2" />
        <span>{label ?? t("common.loading")}</span>
      </div>
    </div>
  );
}
