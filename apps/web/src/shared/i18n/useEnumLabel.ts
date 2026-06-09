import { useCallback } from "react";
import { useTranslation } from "react-i18next";

type EnumNamespace = "enums.academicLevel" | "enums.experience" | "enums.sources";

export function useEnumLabel(namespace: EnumNamespace) {
  const { t } = useTranslation();

  return useCallback(
    (value: string | null | undefined) => {
      if (!value) {
        return t("common.unknown");
      }
      return t(`${namespace}.${value}`, { defaultValue: value });
    },
    [namespace, t],
  );
}
