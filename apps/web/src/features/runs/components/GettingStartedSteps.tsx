import { useState } from "react";
import { useTranslation } from "react-i18next";

const STORAGE_KEY = "researchly:getting-started-seen";

export function GettingStartedSteps() {
  const { t } = useTranslation();
  const [open, setOpen] = useState(() => localStorage.getItem(STORAGE_KEY) !== "1");

  return (
    <details
      className="getting-started"
      open={open}
      onToggle={(event) => {
        const details = event.currentTarget as HTMLDetailsElement;
        setOpen(details.open);
        if (!details.open) {
          localStorage.setItem(STORAGE_KEY, "1");
        }
      }}
    >
      <summary className="getting-started__title">{t("newRun.gettingStarted.title")}</summary>
      <p className="getting-started__intro">{t("newRun.gettingStarted.intro")}</p>
      <ol className="getting-started__steps">
        {[1, 2, 3].map((num) => (
          <li key={num} className="getting-started__step">
            <span className="getting-started__num">{num}</span>
            <span>{t(`newRun.gettingStarted.step${num}`)}</span>
          </li>
        ))}
      </ol>
    </details>
  );
}
