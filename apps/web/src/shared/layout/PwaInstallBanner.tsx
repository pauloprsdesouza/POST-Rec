import { useTranslation } from "react-i18next";

import { usePwaInstall } from "@/shared/pwa/usePwaInstall";
import { AlertModal } from "@/shared/ui/ConfirmModal";
import { PromoBanner } from "@/shared/ui/PromoBanner";

export function PwaInstallBanner() {
  const { t } = useTranslation();
  const { canShow, dismiss, install, iosHintOpen, setIosHintOpen } = usePwaInstall();

  if (!canShow) {
    return null;
  }

  return (
    <>
      <PromoBanner
        id="pwa-install-banner-heading"
        badge={t("pwa.installBadge")}
        message={t("pwa.installMessage")}
        actions={
          <>
            <button
              type="button"
              className="btn btn-primary promo-banner__cta"
              onClick={() => void install()}
            >
              {t("pwa.installAction")}
            </button>
            <button type="button" className="btn btn-link promo-banner__dismiss" onClick={dismiss}>
              {t("pwa.dismiss")}
            </button>
          </>
        }
      />

      <AlertModal show={iosHintOpen} onHide={() => setIosHintOpen(false)} title={t("pwa.iosTitle")}>
        <ol className="promo-banner__ios-steps mb-0">
          <li>{t("pwa.iosStep1")}</li>
          <li>{t("pwa.iosStep2")}</li>
          <li>{t("pwa.iosStep3")}</li>
        </ol>
      </AlertModal>
    </>
  );
}
