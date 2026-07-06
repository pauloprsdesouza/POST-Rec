import { useCallback, useEffect, useMemo, useState } from "react";

import { usePwaMode } from "./PwaModeProvider";
import { dismissPwaInstallBanner, isPwaInstallDismissed } from "./pwaInstallStorage";

interface BeforeInstallPromptEvent extends Event {
  prompt: () => Promise<void>;
  userChoice: Promise<{ outcome: "accepted" | "dismissed" }>;
}

function isIosDevice(): boolean {
  if (typeof navigator === "undefined") {
    return false;
  }
  return /iphone|ipad|ipod/i.test(navigator.userAgent);
}

export function usePwaInstall() {
  const isPwaMode = usePwaMode();
  const [dismissed, setDismissed] = useState(isPwaInstallDismissed);
  const [deferredPrompt, setDeferredPrompt] = useState<BeforeInstallPromptEvent | null>(null);
  const [iosHintOpen, setIosHintOpen] = useState(false);

  const isIos = useMemo(() => isIosDevice(), []);

  useEffect(() => {
    if (isPwaMode || dismissed) {
      return;
    }

    const onBeforeInstall = (event: Event) => {
      event.preventDefault();
      setDeferredPrompt(event as BeforeInstallPromptEvent);
    };

    window.addEventListener("beforeinstallprompt", onBeforeInstall);
    return () => window.removeEventListener("beforeinstallprompt", onBeforeInstall);
  }, [dismissed, isPwaMode]);

  const canShow = !isPwaMode && !dismissed && (deferredPrompt !== null || isIos);

  const dismiss = useCallback(() => {
    dismissPwaInstallBanner();
    setDismissed(true);
    setIosHintOpen(false);
  }, []);

  const install = useCallback(async () => {
    if (deferredPrompt) {
      await deferredPrompt.prompt();
      const { outcome } = await deferredPrompt.userChoice;
      setDeferredPrompt(null);
      if (outcome === "accepted") {
        dismiss();
      }
      return;
    }

    if (isIos) {
      setIosHintOpen(true);
    }
  }, [deferredPrompt, dismiss, isIos]);

  return {
    canShow,
    dismiss,
    install,
    iosHintOpen,
    setIosHintOpen,
  };
}
