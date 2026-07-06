import { useTranslation } from "react-i18next";

import { usePwaInstall } from "@/shared/pwa/usePwaInstall";
import { AlertModal } from "@/shared/ui/ConfirmModal";

export function PwaInstallBanner() {
  const { t } = useTranslation();
  const { canShow, dismiss, install, iosHintOpen, setIosHintOpen } = usePwaInstall();

  if (!canShow) {
    return null;
  }

  return (
    <>
      <aside className="pwa-install-banner" aria-labelledby="pwa-install-banner-heading">
        <div className="pwa-install-banner__inner">
          <div className="pwa-install-banner__row">
            <div className="pwa-install-banner__copy">
              <span className="pwa-install-banner__badge">{t("pwa.installBadge")}</span>
              <p id="pwa-install-banner-heading" className="pwa-install-banner__message">
                {t("pwa.installMessage")}
              </p>
            </div>
            <div className="pwa-install-banner__actions">
              <button
                type="button"
                className="btn btn-primary pwa-install-banner__cta"
                onClick={() => void install()}
              >
                {t("pwa.installAction")}
              </button>
              <button type="button" className="btn btn-link pwa-install-banner__dismiss" onClick={dismiss}>
                {t("pwa.dismiss")}
              </button>
            </div>
          </div>
        </div>
      </aside>

      <AlertModal show={iosHintOpen} onHide={() => setIosHintOpen(false)} title={t("pwa.iosTitle")}>
        <ol className="pwa-install-banner__ios-steps mb-0">
          <li>{t("pwa.iosStep1")}</li>
          <li>{t("pwa.iosStep2")}</li>
          <li>{t("pwa.iosStep3")}</li>
        </ol>
      </AlertModal>
    </>
  );
}
