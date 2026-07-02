import { createContext, useContext, type ReactNode } from "react";

import type { PaperRefEntry } from "@/features/runs/utils/paperRefs";

interface PaperRefContextValue {
  index: Map<string, PaperRefEntry>;
  onNavigateToPaper?: (paperId: string) => void;
}

const PaperRefContext = createContext<PaperRefContextValue>({
  index: new Map(),
});

export function PaperRefProvider({
  index,
  onNavigateToPaper,
  children,
}: {
  index: Map<string, PaperRefEntry>;
  onNavigateToPaper?: (paperId: string) => void;
  children: ReactNode;
}) {
  return (
    <PaperRefContext.Provider value={{ index, onNavigateToPaper }}>{children}</PaperRefContext.Provider>
  );
}

export function usePaperRefs() {
  return useContext(PaperRefContext);
}
