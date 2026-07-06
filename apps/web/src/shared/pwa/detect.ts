/** True when the app runs as an installed PWA (home screen / Add to Home Screen). */
export function isPwaDisplayMode(): boolean {
  if (typeof window === "undefined") {
    return false;
  }

  const navigatorWithStandalone = window.navigator as Navigator & { standalone?: boolean };

  return (
    window.matchMedia("(display-mode: standalone)").matches ||
    window.matchMedia("(display-mode: minimal-ui)").matches ||
    window.matchMedia("(display-mode: fullscreen)").matches ||
    navigatorWithStandalone.standalone === true
  );
}

export type PwaMode = "standalone" | "browser";

export function getPwaMode(): PwaMode {
  return isPwaDisplayMode() ? "standalone" : "browser";
}

export function syncPwaModeAttribute(mode: PwaMode = getPwaMode()): void {
  document.documentElement.dataset.pwaMode = mode;
}
