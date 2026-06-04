import { useMemo } from "react";
import { useTranslation } from "react-i18next";

function asStringArray(value: unknown): string[] {
  if (Array.isArray(value)) {
    return value.filter((item): item is string => typeof item === "string");
  }
  return [];
}

export function useConsentStrings() {
  const { t } = useTranslation();

  return useMemo(
    () => ({
      summary: asStringArray(t("consent.summary", { returnObjects: true })),
      checkboxes: asStringArray(t("consent.checkboxes", { returnObjects: true })),
    }),
    [t],
  );
}
