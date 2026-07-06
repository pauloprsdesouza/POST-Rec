const STORAGE_KEY = "researchly-pwa-install-dismissed";

export function isPwaInstallDismissed(): boolean {
  try {
    return localStorage.getItem(STORAGE_KEY) === "1";
  } catch {
    return false;
  }
}

export function dismissPwaInstallBanner(): void {
  try {
    localStorage.setItem(STORAGE_KEY, "1");
  } catch {
    // ignore
  }
}
