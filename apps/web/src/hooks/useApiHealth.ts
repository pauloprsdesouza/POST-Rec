import { useEffect, useState } from "react";

import { authService } from "../services";

export function useApiHealth(pollMs = 30_000) {
  const [online, setOnline] = useState<boolean | null>(null);

  useEffect(() => {
    let active = true;

    const check = async () => {
      try {
        await authService.health();
        if (active) {
          setOnline(true);
        }
      } catch {
        if (active) {
          setOnline(false);
        }
      }
    };

    void check();
    const timer = window.setInterval(check, pollMs);
    return () => {
      active = false;
      window.clearInterval(timer);
    };
  }, [pollMs]);

  return online;
}
