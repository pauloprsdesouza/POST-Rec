import i18n from "i18next";
import { initReactI18next } from "react-i18next";

import enUS from "./locales/en-US.json";
import esES from "./locales/es-ES.json";
import ptBR from "./locales/pt-BR.json";

export const SUPPORTED_LOCALES = ["en-US", "es-ES", "pt-BR"] as const;
export type AppLocale = (typeof SUPPORTED_LOCALES)[number];

const STORAGE_KEY = "researchly.locale";

function normalizeLocale(raw: string | null | undefined): AppLocale {
  if (!raw) {
    return "en-US";
  }
  const lower = raw.toLowerCase();
  if (lower.startsWith("pt")) {
    return "pt-BR";
  }
  if (lower.startsWith("es")) {
    return "es-ES";
  }
  if (lower.startsWith("en")) {
    return "en-US";
  }
  return SUPPORTED_LOCALES.includes(raw as AppLocale) ? (raw as AppLocale) : "en-US";
}

function detectInitialLocale(): AppLocale {
  const stored = localStorage.getItem(STORAGE_KEY);
  if (stored) {
    return normalizeLocale(stored);
  }
  return normalizeLocale(navigator.language);
}

void i18n.use(initReactI18next).init({
  resources: {
    "en-US": { translation: enUS },
    "es-ES": { translation: esES },
    "pt-BR": { translation: ptBR },
  },
  lng: detectInitialLocale(),
  fallbackLng: "en-US",
  supportedLngs: [...SUPPORTED_LOCALES],
  interpolation: { escapeValue: false },
});

i18n.on("languageChanged", (lng) => {
  localStorage.setItem(STORAGE_KEY, lng);
  document.documentElement.lang = lng;
});

document.documentElement.lang = i18n.language;

export function setAppLocale(locale: AppLocale): void {
  void i18n.changeLanguage(locale);
}

export default i18n;
