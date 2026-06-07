import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import { profileService, sessionService } from "../services";
import type { AuthResponse } from "../types/api";

const STORAGE_KEY = "postrec.auth";

export interface AuthUser {
  userId: string;
  phoneNumber: string;
  fullName?: string | null;
  email?: string | null;
  whatsappOptIn?: boolean;
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
    return JSON.parse(raw) as StoredAuth;
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

export function AuthProvider({ children }: { children: ReactNode }) {
  const [stored, setStored] = useState<StoredAuth | null>(() => readStorage());

  useEffect(() => {
    writeStorage(stored);
  }, [stored]);

  const signIn = useCallback(async (response: AuthResponse) => {
    const user: AuthUser = {
      userId: response.user_id,
      phoneNumber: response.phone_number,
      fullName: response.full_name,
      email: response.email,
      whatsappOptIn: response.whatsapp_opt_in,
    };

    let profileDone: boolean;
    let consentDone: boolean;
    try {
      const [profile, consent] = await Promise.all([
        profileService.getProfile(response.access_token),
        sessionService.getConsentStatus(response.access_token),
      ]);
      profileDone = Boolean(profile.research_area);
      consentDone = consent.accepted;
    } catch {
      profileDone = false;
      consentDone = false;
    }

    setStored({
      accessToken: response.access_token,
      user,
      consentDone,
      profileDone,
      sessionId: null,
      selectedRunId: null,
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
