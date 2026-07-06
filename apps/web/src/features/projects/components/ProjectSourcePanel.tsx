import { useEffect, useId, useRef } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";

import {
  getRecommendationFieldMeta,
  getRecommendationFieldValue,
  recommendationFieldAnchorId,
  recommendationSectionAnchorId,
  type RecommendationSourceSection,
} from "@/features/projects/utils/recommendationFields";
import { EvidenceList } from "@/features/runs/components/EvidenceList";
import { PaperRefText } from "@/features/runs/components/PaperRefText";
import type { Recommendation } from "@/shared/types/api";

interface ProjectSourcePanelProps {
  recommendation: Recommendation;
  runId: string;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  focusField?: string | null;
  onFocusHandled?: () => void;
}

const SECTION_ORDER: RecommendationSourceSection[] = ["about", "summary", "method", "evidence"];

export function ProjectSourcePanel({
  recommendation,
  runId,
  open,
  onOpenChange,
  focusField,
  onFocusHandled,
}: ProjectSourcePanelProps) {
  const { t } = useTranslation();
  const panelId = useId();
  const rootRef = useRef<HTMLElement>(null);

  useEffect(() => {
    if (!open || !focusField || !rootRef.current) {
      return;
    }

    const meta = getRecommendationFieldMeta(focusField);
    const targetId =
      meta.section === "evidence"
        ? recommendationSectionAnchorId("evidence")
        : recommendationFieldAnchorId(focusField);

    window.requestAnimationFrame(() => {
      rootRef.current
        ?.querySelector<HTMLElement>(`#${CSS.escape(targetId)}`)
        ?.scrollIntoView({ behavior: "smooth", block: "nearest" });
      onFocusHandled?.();
    });
  }, [open, focusField, onFocusHandled]);

  const sectionFields: Record<RecommendationSourceSection, string[]> = {
    about: ["research_gap", "research_question", "expected_contribution"],
    summary: ["hypothesis", "related_work_summary"],
    method: ["proposed_method", "experimental_plan", "datasets", "evaluation_metrics", "risks"],
    evidence: [],
  };

  return (
    <section
      ref={rootRef}
      className={`project-source-panel${open ? " project-source-panel--open" : ""}`}
      aria-labelledby={`${panelId}-title`}
    >
      <div className="project-source-panel__header">
        <h2 id={`${panelId}-title`} className="project-source-panel__title">
          {t("projects.source.panelTitle")}
        </h2>
        <div className="project-source-panel__actions">
          <button
            type="button"
            className="btn btn-outline-secondary btn-sm"
            aria-expanded={open}
            aria-controls={`${panelId}-body`}
            onClick={() => onOpenChange(!open)}
          >
            {open ? t("projects.source.hidePanel") : t("projects.source.showPanel")}
          </button>
          <Link to={`/runs/${runId}`} className="btn btn-link btn-sm project-source-panel__run-link">
            {t("projects.source.viewInRun")} →
          </Link>
        </div>
      </div>

      {open ? (
        <div id={`${panelId}-body`} className="project-source-panel__body">
          <p className="project-source-panel__idea-title">{recommendation.title}</p>

          {SECTION_ORDER.map((section) => {
            if (section === "evidence") {
              const count = recommendation.evidence_papers?.length ?? 0;
              if (!count) {
                return null;
              }
              return (
                <div
                  key={section}
                  id={recommendationSectionAnchorId(section)}
                  className="project-source-panel__section"
                >
                  <h3 className="project-source-panel__section-title">
                    {t("projects.source.sections.evidence", { count })}
                  </h3>
                  <EvidenceList papers={recommendation.evidence_papers} />
                </div>
              );
            }

            const blocks = sectionFields[section]
              .map((field) => {
                const value = getRecommendationFieldValue(recommendation, field);
                if (Array.isArray(value)) {
                  if (!value.length) {
                    return null;
                  }
                  return { field, value, isList: true as const };
                }
                if (!value?.trim()) {
                  return null;
                }
                return { field, value, isList: false as const };
              })
              .filter(Boolean);

            if (!blocks.length) {
              return null;
            }

            return (
              <div
                key={section}
                id={recommendationSectionAnchorId(section)}
                className="project-source-panel__section"
              >
                <h3 className="project-source-panel__section-title">
                  {t(`projects.source.sections.${section}`)}
                </h3>
                {blocks.map((block) => {
                  if (!block) {
                    return null;
                  }
                  const meta = getRecommendationFieldMeta(block.field);
                  const label = meta.labelKey.startsWith("projects.")
                    ? t(meta.labelKey)
                    : t(meta.labelKey);

                  return (
                    <div
                      key={block.field}
                      id={recommendationFieldAnchorId(block.field)}
                      className="project-source-panel__block"
                    >
                      <h4 className="project-source-panel__block-label">{label}</h4>
                      {block.isList ? (
                        <ul className="project-source-panel__list">
                          {block.value.map((item) => (
                            <li key={item}>
                              <PaperRefText text={item} />
                            </li>
                          ))}
                        </ul>
                      ) : (
                        <p className="project-source-panel__text">
                          <PaperRefText text={block.value} />
                        </p>
                      )}
                    </div>
                  );
                })}
              </div>
            );
          })}
        </div>
      ) : null}
    </section>
  );
}
