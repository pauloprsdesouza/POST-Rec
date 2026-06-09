import { useTranslation } from "react-i18next";

interface LoadingSpinnerProps {
  label?: string;
}

export function LoadingSpinner({ label }: LoadingSpinnerProps) {
  const { t } = useTranslation();

  return (
    <div className="page-loading">
      <div className="d-flex flex-column align-items-center justify-content-center">
        <div className="page-loading__brand" role="status" aria-label={label ?? t("common.loading")} />
        <span className="page-loading__label">{label ?? t("common.loading")}</span>
      </div>
    </div>
  );
}
