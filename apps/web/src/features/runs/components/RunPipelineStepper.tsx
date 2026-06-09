import { useTranslation } from "react-i18next";

import {
  RUN_PIPELINE_STAGES,
  getRunPipelineStageIndex,
  resolvePipelineStage,
} from "@/features/runs/utils/runs";

interface RunPipelineStepperProps {
  status: string;
}

export function RunPipelineStepper({ status }: RunPipelineStepperProps) {
  const { t } = useTranslation();
  const currentStage = resolvePipelineStage(status);
  const currentIndex = getRunPipelineStageIndex(status);

  return (
    <ol className="run-pipeline" aria-label={t("progress.pipelineLabel")}>
      {RUN_PIPELINE_STAGES.map((stage, index) => {
        const state =
          currentIndex < 0
            ? "pending"
            : index < currentIndex
              ? "done"
              : index === currentIndex
                ? "current"
                : "pending";
        const label = t(`status.${stage}`, { defaultValue: stage.replace(/_/g, " ") });

        return (
          <li
            key={stage}
            className={`run-pipeline__step run-pipeline__step--${state}`}
            aria-current={state === "current" ? "step" : undefined}
          >
            <span className="run-pipeline__marker" aria-hidden />
            <span className="run-pipeline__label">{label}</span>
            {state === "current" && currentStage === stage ? (
              <span className="run-pipeline__pulse" aria-hidden />
            ) : null}
          </li>
        );
      })}
    </ol>
  );
}
