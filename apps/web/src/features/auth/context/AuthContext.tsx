import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";

import { authService } from "@/features/auth/api/authService";
import { profileService } from "@/features/profile/api/profileService";
import { sessionService } from "@/features/session/api/sessionService";
import { queryKeys } from "@/shared/query/keys";
import type { AuthResponse, UserRole } from "@/shared/types/api";

const STORAGE_KEY = "researchly.auth";

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

interface AuthStateValue {
  accessToken: string | null;
  user: AuthUser | null;
  isAuthenticated: boolean;
  isAdmin: boolean;
  consentDone: boolean;
  profileDone: boolean;
  sessionId: string | null;
  selectedRunId: string | null;
}

interface AuthActionsValue {
  signIn: (response: AuthResponse) => Promise<void>;
  signOut: () => void;
  updateUser: (partial: Partial<AuthUser>) => void;
  completeConsent: (sessionId: string) => void;
  completeProfile: () => void;
  setSessionId: (sessionId: string) => void;
  setSelectedRunId: (runId: string) => void;
}

type AuthContextValue = AuthStateValue & AuthActionsValue;

const AuthStateContext = createContext<AuthStateValue | undefined>(undefined);
const AuthActionsContext = createContext<AuthActionsValue | undefined>(undefined);

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
  };
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [stored, setStored] = useState<StoredAuth | null>(() => readStorage());
  const queryClient = useQueryClient();
  const accessToken = stored?.accessToken ?? null;

  const { data: onboardingFlags } = useQuery({
    queryKey: queryKeys.onboarding(accessToken),
    queryFn: () => resolveOnboardingFlags(accessToken!),
    enabled: Boolean(accessToken),
    staleTime: 5 * 60_000,
  });

  useEffect(() => {
    writeStorage(stored);
  }, [stored]);

  useEffect(() => {
    if (!onboardingFlags || !accessToken) {
      return;
    }

    setStored((current) => {
      if (!current || current.accessToken !== accessToken) {
        return current;
      }

      const profileDone = onboardingFlags.profileDone ?? current.profileDone;
      const consentDone = onboardingFlags.consentDone ?? current.consentDone;
      const role = onboardingFlags.isAdmin
        ? "admin"
        : (onboardingFlags.role ?? current.user?.role ?? "researcher");

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
  }, [accessToken, onboardingFlags]);

  const signIn = useCallback(
    async (response: AuthResponse) => {
      const flags = await resolveOnboardingFlags(response.access_token);
      void queryClient.prefetchQuery({
        queryKey: queryKeys.onboarding(response.access_token),
        queryFn: () => Promise.resolve(flags),
        staleTime: 5 * 60_000,
      });

      const user: AuthUser = {
        userId: response.user_id,
        phoneNumber: response.phone_number,
        fullName: response.full_name,
        email: response.email,
        whatsappOptIn: response.whatsapp_opt_in,
        role:
          flags.isAdmin || response.role === "admin"
            ? "admin"
            : (response.role ?? flags.role ?? "researcher"),
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

      void import("@/features/runs/pages/RunsPage");
    },
    [queryClient],
  );

  const signOut = useCallback(() => {
    setStored(null);
    queryClient.clear();
  }, [queryClient]);

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

  const stateValue = useMemo<AuthStateValue>(
    () => ({
      accessToken,
      user: stored?.user ?? null,
      isAuthenticated: Boolean(accessToken),
      isAdmin: stored?.user?.role === "admin",
      consentDone: stored?.consentDone ?? false,
      profileDone: stored?.profileDone ?? false,
      sessionId: stored?.sessionId ?? null,
      selectedRunId: stored?.selectedRunId ?? null,
    }),
    [accessToken, stored],
  );

  const actionsValue = useMemo<AuthActionsValue>(
    () => ({
      signIn,
      signOut,
      updateUser,
      completeConsent,
      completeProfile,
      setSessionId,
      setSelectedRunId,
    }),
    [signIn, signOut, updateUser, completeConsent, completeProfile, setSessionId, setSelectedRunId],
  );

  return (
    <AuthActionsContext.Provider value={actionsValue}>
      <AuthStateContext.Provider value={stateValue}>{children}</AuthStateContext.Provider>
    </AuthActionsContext.Provider>
  );
}

export function useAuthState(): AuthStateValue {
  const context = useContext(AuthStateContext);
  if (!context) {
    throw new Error("useAuthState must be used within AuthProvider");
  }
  return context;
}

export function useAuthActions(): AuthActionsValue {
  const context = useContext(AuthActionsContext);
  if (!context) {
    throw new Error("useAuthActions must be used within AuthProvider");
  }
  return context;
}

export function useAuth(): AuthContextValue {
  return { ...useAuthState(), ...useAuthActions() };
}
