import { useTranslation } from "react-i18next";

import {
  getRecommendationFieldMeta,
} from "@/features/projects/utils/recommendationFields";

interface ProjectLinkedFieldsProps {
  fields: string[];
  onNavigateToField: (field: string) => void;
}

export function ProjectLinkedFields({ fields, onNavigateToField }: ProjectLinkedFieldsProps) {
  const { t } = useTranslation();

  if (!fields.length) {
    return null;
  }

  const uniqueFields = [...new Set(fields)];

  return (
    <div className="project-linked-fields">
      <p className="project-linked-fields__label">{t("projects.source.linkedFields")}</p>
      <ul className="project-linked-fields__list">
        {uniqueFields.map((field) => {
          const meta = getRecommendationFieldMeta(field);
          const label = meta.labelKey.startsWith("projects.")
            ? t(meta.labelKey)
            : t(meta.labelKey, { defaultValue: field.replace(/_/g, " ") });

          return (
            <li key={field}>
              <button
                type="button"
                className="project-linked-fields__chip"
                onClick={() => onNavigateToField(field)}
              >
                {label}
              </button>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
