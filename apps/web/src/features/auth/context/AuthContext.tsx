import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import { profileService, sessionService, authService } from "@/shared/api";
import type { AuthResponse, UserRole } from "@/shared/types/api";

const STORAGE_KEY = "postrec.auth";

export interface AuthUser {
  userId: string;
  phoneNumber: string;
  fullName?: string | null;
  email?: string | null;
  whatsappOptIn?: boolean;
  role: UserRole;
}

interface StoredAuth {
  accessToken: string;
  user: AuthUser;
  consentDone: boolean;
  profileDone: boolean;
  sessionId?: string | null;
  selectedRunId?: string | null;
}

interface AuthContextValue {
  accessToken: string | null;
  user: AuthUser | null;
  isAuthenticated: boolean;
  isAdmin: boolean;
  consentDone: boolean;
  profileDone: boolean;
  sessionId: string | null;
  selectedRunId: string | null;
  signIn: (response: AuthResponse) => Promise<void>;
  signOut: () => void;
  updateUser: (partial: Partial<AuthUser>) => void;
  completeConsent: (sessionId: string) => void;
  completeProfile: () => void;
  setSessionId: (sessionId: string) => void;
  setSelectedRunId: (runId: string) => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

function readStorage(): StoredAuth | null {
  const raw = localStorage.getItem(STORAGE_KEY);
  if (!raw) {
    return null;
  }
  try {
    const parsed = JSON.parse(raw) as StoredAuth;
    if (parsed.user && !parsed.user.role) {
      parsed.user.role = "researcher";
    }
    return parsed;
  } catch {
    return null;
  }
}

function writeStorage(data: StoredAuth | null): void {
  if (!data) {
    localStorage.removeItem(STORAGE_KEY);
    return;
  }
  localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
}

async function resolveOnboardingFlags(accessToken: string) {
  const [profileResult, consentResult, meResult] = await Promise.allSettled([
    profileService.getProfile(accessToken),
    sessionService.getConsentStatus(accessToken),
    authService.getMe(accessToken),
  ]);

  return {
    profileDone:
      profileResult.status === "fulfilled" ? Boolean(profileResult.value.research_area) : null,
    consentDone: consentResult.status === "fulfilled" ? consentResult.value.accepted : null,
    role: meResult.status === "fulfilled" ? meResult.value.role : null,
    isAdmin: meResult.status === "fulfilled" ? Boolean(meResult.value.is_admin) : null,
    canUseResearchFeatures:
      meResult.status === "fulfilled" ? meResult.value.can_use_research_features !== false : null,
  };
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [stored, setStored] = useState<StoredAuth | null>(() => readStorage());

  useEffect(() => {
    writeStorage(stored);
  }, [stored]);

  useEffect(() => {
    const accessToken = stored?.accessToken;
    if (!accessToken) {
      return;
    }

    let cancelled = false;

    void (async () => {
      const flags = await resolveOnboardingFlags(accessToken);
      if (cancelled) {
        return;
      }

      setStored((current) => {
        if (!current || current.accessToken !== accessToken) {
          return current;
        }

        const profileDone = flags.profileDone ?? current.profileDone;
        const consentDone = flags.consentDone ?? current.consentDone;
        const role = flags.isAdmin ? "admin" : (flags.role ?? current.user?.role ?? "researcher");

        if (
          profileDone === current.profileDone &&
          consentDone === current.consentDone &&
          role === current.user?.role
        ) {
          return current;
        }

        return {
          ...current,
          profileDone,
          consentDone,
          user: current.user ? { ...current.user, role } : current.user,
        };
      });
    })();

    return () => {
      cancelled = true;
    };
  }, [stored?.accessToken]);

  const signIn = useCallback(async (response: AuthResponse) => {
    const flags = await resolveOnboardingFlags(response.access_token);

    const user: AuthUser = {
      userId: response.user_id,
      phoneNumber: response.phone_number,
      fullName: response.full_name,
      email: response.email,
      whatsappOptIn: response.whatsapp_opt_in,
      role: flags.isAdmin || response.role === "admin" ? "admin" : (response.role ?? flags.role ?? "researcher"),
    };

    setStored((previous) => {
      const consentDone = flags.consentDone ?? previous?.consentDone ?? false;
      const profileDone = flags.profileDone ?? previous?.profileDone ?? false;

      return {
        accessToken: response.access_token,
        user,
        consentDone,
        profileDone,
        sessionId: consentDone ? (previous?.sessionId ?? null) : null,
        selectedRunId: previous?.selectedRunId ?? null,
      };
    });
  }, []);

  const signOut = useCallback(() => {
    setStored(null);
  }, []);

  const updateUser = useCallback((partial: Partial<AuthUser>) => {
    setStored((current) =>
      current
        ? {
            ...current,
            user: { ...current.user, ...partial },
          }
        : current,
    );
  }, []);

  const completeConsent = useCallback((sessionId: string) => {
    setStored((current) =>
      current
        ? {
            ...current,
            consentDone: true,
            sessionId,
          }
        : current,
    );
  }, []);

  const completeProfile = useCallback(() => {
    setStored((current) => (current ? { ...current, profileDone: true } : current));
  }, []);

  const setSessionId = useCallback((sessionId: string) => {
    setStored((current) => (current ? { ...current, sessionId } : current));
  }, []);

  const setSelectedRunId = useCallback((runId: string) => {
    setStored((current) => (current ? { ...current, selectedRunId: runId } : current));
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      accessToken: stored?.accessToken ?? null,
      user: stored?.user ?? null,
      isAuthenticated: Boolean(stored?.accessToken),
      isAdmin: stored?.user?.role === "admin",
      consentDone: stored?.consentDone ?? false,
      profileDone: stored?.profileDone ?? false,
      sessionId: stored?.sessionId ?? null,
      selectedRunId: stored?.selectedRunId ?? null,
      signIn,
      signOut,
      updateUser,
      completeConsent,
      completeProfile,
      setSessionId,
      setSelectedRunId,
    }),
    [stored, signIn, signOut, updateUser, completeConsent, completeProfile, setSessionId, setSelectedRunId],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return context;
}
