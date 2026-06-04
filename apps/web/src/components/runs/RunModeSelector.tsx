import { Form } from "react-bootstrap";
import { useTranslation } from "react-i18next";

import type { RunMode } from "../../types/api";

interface RunModeSelectorProps {
  value: RunMode;
  onChange: (mode: RunMode) => void;
  disabled?: boolean;
}

const MODES: RunMode[] = ["quick", "sota", "exploratory", "fggv"];

export function RunModeSelector({ value, onChange, disabled }: RunModeSelectorProps) {
  const { t } = useTranslation();

  return (
    <Form.Group className="mb-3">
      <Form.Label>{t("newRun.runMode.label")}</Form.Label>
      <div className="run-mode-selector">
        {MODES.map((mode) => (
          <Form.Check
            key={mode}
            type="radio"
            id={`run-mode-${mode}`}
            name="run-mode"
            label={t(`newRun.runMode.${mode}.label`)}
            checked={value === mode}
            disabled={disabled}
            onChange={() => onChange(mode)}
            className="run-mode-selector__option"
          />
        ))}
      </div>
      <Form.Text className="text-secondary">{t(`newRun.runMode.${value}.hint`)}</Form.Text>
    </Form.Group>
  );
}
