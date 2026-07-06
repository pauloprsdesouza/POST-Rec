import i18n from "i18next";
import { initReactI18next } from "react-i18next";

import enUS from "./locales/en-US.json";

export const SUPPORTED_LOCALES = ["en-US", "es-ES", "pt-BR"] as const;
export type AppLocale = (typeof SUPPORTED_LOCALES)[number];

const STORAGE_KEY = "researchly.locale";

const localeLoaders: Record<AppLocale, () => Promise<{ default: Record<string, unknown> }>> = {
  "en-US": () => Promise.resolve({ default: enUS }),
  "es-ES": () => import("./locales/es-ES.json"),
  "pt-BR": () => import("./locales/pt-BR.json"),
};

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

async function ensureLocaleLoaded(locale: AppLocale): Promise<void> {
  if (i18n.hasResourceBundle(locale, "translation")) {
    return;
  }
  const module = await localeLoaders[locale]();
  i18n.addResourceBundle(locale, "translation", module.default, true, true);
}

const initialLocale = detectInitialLocale();

void i18n
  .use(initReactI18next)
  .init({
    resources: {
      "en-US": { translation: enUS },
    },
    lng: initialLocale === "en-US" ? "en-US" : "en-US",
    fallbackLng: "en-US",
    supportedLngs: [...SUPPORTED_LOCALES],
    interpolation: { escapeValue: false },
  })
  .then(async () => {
    if (initialLocale !== "en-US") {
      await ensureLocaleLoaded(initialLocale);
      await i18n.changeLanguage(initialLocale);
    }
    document.documentElement.lang = i18n.language;
  });

i18n.on("languageChanged", (lng) => {
  const locale = normalizeLocale(lng);
  localStorage.setItem(STORAGE_KEY, locale);
  document.documentElement.lang = locale;
  void ensureLocaleLoaded(locale);
});

document.documentElement.lang = initialLocale;

export function setAppLocale(locale: AppLocale): void {
  void ensureLocaleLoaded(locale).then(() => {
    void i18n.changeLanguage(locale);
  });
}

export default i18n;
