import { useState } from "react";
import { Button, Form } from "react-bootstrap";
import { useTranslation } from "react-i18next";

import type { RunMode } from "@/shared/types/api";

interface RunModeSelectorProps {
  value: RunMode;
  onChange: (mode: RunMode) => void;
  disabled?: boolean;
}

const PRIMARY_MODES: RunMode[] = ["sota", "quick"];
const ADVANCED_MODES: RunMode[] = ["exploratory", "fggv"];
const RECOMMENDED_MODE: RunMode = "sota";

function ModeCard({
  mode,
  selected,
  disabled,
  onSelect,
}: {
  mode: RunMode;
  selected: boolean;
  disabled?: boolean;
  onSelect: () => void;
}) {
  const { t } = useTranslation();
  const recommended = mode === RECOMMENDED_MODE;

  return (
    <button
      type="button"
      className={`run-mode-card ${selected ? "run-mode-card--selected" : ""}`}
      disabled={disabled}
      aria-pressed={selected}
      onClick={onSelect}
    >
      <div className="run-mode-card__head">
        <span className="run-mode-card__label">{t(`newRun.runMode.${mode}.label`)}</span>
        {recommended ? <span className="run-mode-card__badge">{t("newRun.runMode.recommended")}</span> : null}
      </div>
      <p className="run-mode-card__hint">{t(`newRun.runMode.${mode}.shortHint`)}</p>
    </button>
  );
}

export function RunModeSelector({ value, onChange, disabled }: RunModeSelectorProps) {
  const { t } = useTranslation();
  const [showAdvanced, setShowAdvanced] = useState(ADVANCED_MODES.includes(value));

  return (
    <Form.Group className="field-group">
      <Form.Label>{t("newRun.runMode.label")}</Form.Label>
      <p className="run-mode-selector__intro">{t("newRun.runMode.intro")}</p>

      <div className="run-mode-cards">
        {PRIMARY_MODES.map((mode) => (
          <ModeCard
            key={mode}
            mode={mode}
            selected={value === mode}
            disabled={disabled}
            onSelect={() => onChange(mode)}
          />
        ))}
      </div>

      <Button
        type="button"
        variant="link"
        className="run-mode-selector__advanced-toggle"
        onClick={() => setShowAdvanced((open) => !open)}
      >
        {showAdvanced ? t("newRun.runMode.hideAdvanced") : t("newRun.runMode.showAdvanced")}
      </Button>

      {showAdvanced ? (
        <div className="run-mode-cards">
          {ADVANCED_MODES.map((mode) => (
            <ModeCard
              key={mode}
              mode={mode}
              selected={value === mode}
              disabled={disabled}
              onSelect={() => onChange(mode)}
            />
          ))}
        </div>
      ) : null}

      <Form.Text className="inline-meta d-block">{t(`newRun.runMode.${value}.hint`)}</Form.Text>
    </Form.Group>
  );
}
