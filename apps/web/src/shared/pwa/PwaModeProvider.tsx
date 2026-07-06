import { createContext, useContext, useEffect, useState, type ReactNode } from "react";

import { getPwaMode, syncPwaModeAttribute, type PwaMode } from "./detect";

const PwaModeContext = createContext(false);

export function PwaModeProvider({ children }: { children: ReactNode }) {
  const [isPwaMode, setIsPwaMode] = useState(() => getPwaMode() === "standalone");

  useEffect(() => {
    const update = () => {
      const mode = getPwaMode();
      syncPwaModeAttribute(mode);
      setIsPwaMode(mode === "standalone");
    };

    update();

    const mediaQueries = [
      "(display-mode: standalone)",
      "(display-mode: minimal-ui)",
      "(display-mode: fullscreen)",
    ].map((query) => window.matchMedia(query));

    for (const mq of mediaQueries) {
      mq.addEventListener("change", update);
    }

    return () => {
      for (const mq of mediaQueries) {
        mq.removeEventListener("change", update);
      }
    };
  }, []);

  return <PwaModeContext.Provider value={isPwaMode}>{children}</PwaModeContext.Provider>;
}

export function usePwaMode(): boolean {
  return useContext(PwaModeContext);
}

export type { PwaMode };
