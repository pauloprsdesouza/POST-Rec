import { Dropdown } from "react-bootstrap";
import { useTranslation } from "react-i18next";

import { SUPPORTED_LOCALES, setAppLocale, type AppLocale } from "@/shared/i18n";

interface LanguageSwitcherProps {
  variant?: "navbar" | "inline";
}

export function LanguageSwitcher({ variant = "inline" }: LanguageSwitcherProps) {
  const { t, i18n } = useTranslation();
  const current = i18n.language as AppLocale;

  if (variant === "navbar") {
    return (
      <Dropdown align="end" className="language-switcher language-switcher--navbar">
        <Dropdown.Toggle
          variant="link"
          className="language-switcher__toggle text-decoration-none"
          aria-label={t("nav.language")}
        >
          {current.split("-")[0].toUpperCase()}
        </Dropdown.Toggle>
        <Dropdown.Menu className="language-switcher__menu">
          {SUPPORTED_LOCALES.map((locale) => (
            <Dropdown.Item
              key={locale}
              active={locale === current}
              onClick={() => setAppLocale(locale)}
            >
              {t(`locale.${locale}`)}
            </Dropdown.Item>
          ))}
        </Dropdown.Menu>
      </Dropdown>
    );
  }

  return (
    <div className="language-switcher language-switcher--inline">
      <label className="language-switcher__label" htmlFor="app-locale">
        {t("nav.language")}
      </label>
      <select
        id="app-locale"
        className="form-select form-select-sm language-switcher__select"
        value={current}
        onChange={(e) => setAppLocale(e.target.value as AppLocale)}
      >
        {SUPPORTED_LOCALES.map((locale) => (
          <option key={locale} value={locale}>
            {t(`locale.${locale}`)}
          </option>
        ))}
      </select>
    </div>
  );
}
