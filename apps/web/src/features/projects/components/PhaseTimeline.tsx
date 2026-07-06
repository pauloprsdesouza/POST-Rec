import { useTranslation } from "react-i18next";

import { getPhaseVisualState, sortPhases } from "@/features/projects/utils/projectUtils";
import type { ResearchProject } from "@/shared/types/api";

interface PhaseTimelineProps {
  project: ResearchProject;
  activePhaseId: string | null;
  onSelectPhase: (phaseId: string) => void;
}

export function PhaseTimeline({ project, activePhaseId, onSelectPhase }: PhaseTimelineProps) {
  const { t } = useTranslation();
  const phases = sortPhases(project.phases);
  const resolvedActiveId = activePhaseId ?? project.current_phase_id;

  return (
    <nav className="phase-timeline" aria-label={t("projects.phaseNav")}>
      <ol className="phase-timeline__list">
        {phases.map((phase, index) => {
          const state = getPhaseVisualState(phase, project.current_phase_id);
          const isActive = phase.id === resolvedActiveId;

          return (
            <li
              key={phase.id}
              className={[
                "phase-timeline__item",
                `phase-timeline__item--${state}`,
                isActive ? "phase-timeline__item--selected" : "",
              ]
                .filter(Boolean)
                .join(" ")}
            >
              <button
                type="button"
                className={`phase-timeline__btn${isActive ? " phase-timeline__btn--active" : ""}`}
                onClick={() => onSelectPhase(phase.id)}
                aria-current={isActive ? "step" : undefined}
              >
                <span className="phase-timeline__rail" aria-hidden>
                  <span className="phase-timeline__marker">
                    {state === "done" ? "✓" : index + 1}
                  </span>
                  {index < phases.length - 1 ? <span className="phase-timeline__connector" /> : null}
                </span>
                <span className="phase-timeline__content">
                  <span className="phase-timeline__label">{phase.title}</span>
                </span>
              </button>
            </li>
          );
        })}
      </ol>
    </nav>
  );
}
