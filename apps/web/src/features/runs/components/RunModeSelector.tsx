import { useEffect, useId, useRef, useState } from "react";
import { useTranslation } from "react-i18next";

import type { RunModeSelection } from "@/shared/types/api";

interface RunModeSelectorProps {
  value: RunModeSelection;
  onChange: (mode: RunModeSelection) => void;
  disabled?: boolean;
  layout?: "default" | "compact";
  menuPlacement?: "top" | "bottom";
  showLabel?: boolean;
}

const MODE_OPTIONS: RunModeSelection[] = ["auto", "sota", "quick", "exploratory", "fggv"];

export function RunModeSelector({
  value,
  onChange,
  disabled,
  layout = "default",
  menuPlacement = "bottom",
  showLabel = true,
}: RunModeSelectorProps) {
  const { t } = useTranslation();
  const menuId = useId();
  const labelId = useId();
  const rootRef = useRef<HTMLDivElement>(null);
  const [open, setOpen] = useState(false);
  const compact = layout === "compact";

  useEffect(() => {
    if (!open) {
      return;
    }
    const handlePointerDown = (event: MouseEvent) => {
      if (!rootRef.current?.contains(event.target as Node)) {
        setOpen(false);
      }
    };
    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handlePointerDown);
    document.addEventListener("keydown", handleEscape);
    return () => {
      document.removeEventListener("mousedown", handlePointerDown);
      document.removeEventListener("keydown", handleEscape);
    };
  }, [open]);

  const selectMode = (mode: RunModeSelection) => {
    onChange(mode);
    setOpen(false);
  };

  const modeHint = t(`newRun.runMode.${value}.hint`, {
    defaultValue: t(`newRun.runMode.${value}.shortHint`),
  });

  return (
    <div
      className={`run-mode-picker ${compact ? "run-mode-picker--compact" : ""}`}
      ref={rootRef}
    >
      {showLabel && !compact ? (
        <span className="run-mode-picker__label" id={labelId}>
          {t("newRun.runMode.label")}
        </span>
      ) : null}

      <button
        type="button"
        className="run-mode-picker__trigger"
        disabled={disabled}
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-controls={menuId}
        aria-labelledby={showLabel && !compact ? labelId : undefined}
        onClick={() => setOpen((current) => !current)}
      >
        <span className="run-mode-picker__trigger-text">
          <span className="run-mode-picker__trigger-label">{t(`newRun.runMode.${value}.label`)}</span>
          {!compact ? (
            <span className="run-mode-picker__trigger-hint">{t(`newRun.runMode.${value}.shortHint`)}</span>
          ) : null}
        </span>
        <span className="run-mode-picker__chevron" aria-hidden>
          {open ? "▴" : "▾"}
        </span>
      </button>

      {open ? (
        <div
          className={`run-mode-picker__menu run-mode-picker__menu--${menuPlacement}`}
          id={menuId}
          role="listbox"
          aria-label={t("newRun.runMode.label")}
        >
          {MODE_OPTIONS.map((mode) => {
            const selected = value === mode;
            return (
              <button
                key={mode}
                type="button"
                role="option"
                aria-selected={selected}
                className={`run-mode-picker__option ${selected ? "run-mode-picker__option--selected" : ""}`}
                onClick={() => selectMode(mode)}
              >
                <span className="run-mode-picker__option-main">
                  <span className="run-mode-picker__option-head">
                    <span className="run-mode-picker__option-label">{t(`newRun.runMode.${mode}.label`)}</span>
                    {mode === "auto" ? (
                      <span className="run-mode-picker__option-badge">{t("newRun.runMode.recommended")}</span>
                    ) : null}
                  </span>
                  <span className="run-mode-picker__option-hint">{t(`newRun.runMode.${mode}.shortHint`)}</span>
                </span>
                {selected ? (
                  <span className="run-mode-picker__option-check" aria-hidden>
                    ✓
                  </span>
                ) : null}
              </button>
            );
          })}
        </div>
      ) : null}

      <p className={`run-mode-picker__hint ${compact ? "run-mode-picker__hint--compact" : ""}`}>{modeHint}</p>
    </div>
  );
}
