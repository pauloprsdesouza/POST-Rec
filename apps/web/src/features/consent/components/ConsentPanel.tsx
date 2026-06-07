import { Badge } from "react-bootstrap";
import { Trans, useTranslation } from "react-i18next";

import { CONSENT_VERSION } from "@/shared/constants";
import { useConsentStrings } from "@/shared/i18n/useConsentStrings";
import type { UserConsentStatus } from "@/shared/types/api";

interface ConsentPanelProps {
  status: UserConsentStatus | null;
  readOnly?: boolean;
}

export function ConsentPanel({ status, readOnly = true }: ConsentPanelProps) {
  const { t, i18n } = useTranslation();
  const { summary, checkboxes } = useConsentStrings();
  const accepted = status?.accepted ?? false;

  const acceptedDate = status?.accepted_at
    ? new Intl.DateTimeFormat(i18n.language, {
        year: "numeric",
        month: "long",
        day: "numeric",
      }).format(new Date(status.accepted_at))
    : null;

  return (
    <div className="consent-panel">
      <div className="d-flex align-items-center gap-2 mb-3">
        <h6 className="mb-0 fw-semibold">{t("consent.panelTitle")}</h6>
        <Badge bg={accepted ? "success" : "secondary"}>
          {accepted ? t("consent.accepted") : t("consent.pending")}
        </Badge>
      </div>

      <p className="text-secondary">
        <Trans i18nKey="consent.panelIntro" components={{ strong: <strong /> }} />
      </p>
      <ul className="consent-panel__list">
        {summary.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>

      {readOnly && accepted ? (
        <div className="consent-panel__meta">
          {acceptedDate ? (
            <p className="small text-secondary mb-1">{t("consent.acceptedOn", { date: acceptedDate })}</p>
          ) : null}
          <p className="small text-secondary mb-0">
            {t("consent.version", { version: status?.consent_version ?? CONSENT_VERSION })}
          </p>
        </div>
      ) : null}

      {!readOnly ? (
        <div className="mt-3">
          <p className="small fw-semibold mb-2">{t("consent.agreedTo")}</p>
          <ul className="consent-panel__checks mb-0">
            {checkboxes.map((label) => (
              <li key={label}>{label}</li>
            ))}
          </ul>
        </div>
      ) : null}
    </div>
  );
}
