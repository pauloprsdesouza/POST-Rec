export type ThemePreference = "light" | "dark" | "system";

const STORAGE_KEY = "postrec-theme";

export function getStoredTheme(): ThemePreference {
  try {
    const value = localStorage.getItem(STORAGE_KEY);
    if (value === "light" || value === "dark" || value === "system") {
      return value;
    }
  } catch {
    // ignore
  }
  return "system";
}

export function setStoredTheme(theme: ThemePreference): void {
  try {
    localStorage.setItem(STORAGE_KEY, theme);
  } catch {
    // ignore
  }
}

export function resolveTheme(preference: ThemePreference): "light" | "dark" {
  if (preference === "light" || preference === "dark") {
    return preference;
  }
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

export function applyTheme(resolved: "light" | "dark"): void {
  document.documentElement.setAttribute("data-theme", resolved);
  document.documentElement.setAttribute("data-bs-theme", resolved);
  document.documentElement.style.colorScheme = resolved;
}

export function initTheme(): ThemePreference {
  const preference = getStoredTheme();
  applyTheme(resolveTheme(preference));
  return preference;
}
