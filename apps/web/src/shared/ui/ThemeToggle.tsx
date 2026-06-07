import { useTranslation } from "react-i18next";

import { useTheme } from "@/shared/theme/ThemeContext";

function SunIcon() {
  return (
    <svg className="theme-toggle__icon" viewBox="0 0 20 20" fill="none" aria-hidden>
      <circle cx="10" cy="10" r="3.5" stroke="currentColor" strokeWidth="1.5" />
      <path
        d="M10 2v2M10 16v2M3.5 10h2M14.5 10h2M5.4 5.4l1.4 1.4M13.2 13.2l1.4 1.4M5.4 14.6l1.4-1.4M13.2 6.8l1.4-1.4"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
      />
    </svg>
  );
}

function MoonIcon() {
  return (
    <svg className="theme-toggle__icon" viewBox="0 0 20 20" fill="none" aria-hidden>
      <path
        d="M15.5 11.2a5.5 5.5 0 0 1-6.7-6.7A5.5 5.5 0 1 0 15.5 11.2Z"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinejoin="round"
      />
    </svg>
  );
}

interface ThemeToggleProps {
  variant?: "navbar" | "inline";
}

export function ThemeToggle({ variant = "navbar" }: ThemeToggleProps) {
  const { t } = useTranslation();
  const { resolved, toggle } = useTheme();
  const isDark = resolved === "dark";
  const label = isDark ? t("nav.themeLight") : t("nav.themeDark");

  return (
    <button
      type="button"
      className={`theme-toggle theme-toggle--${variant}`}
      onClick={toggle}
      aria-label={label}
      title={label}
    >
      {isDark ? <SunIcon /> : <MoonIcon />}
    </button>
  );
}
