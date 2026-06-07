import { AuthService } from "@/features/auth/api/authService";
import { AccountService } from "@/features/profile/api/accountService";
import { httpClient } from "@/shared/api/httpClient";
import { ProfileService } from "@/features/profile/api/profileService";
import { RunService } from "@/features/runs/api/runService";
import { SessionService } from "@/features/session/api/sessionService";
import { ValidationService } from "@/features/insights/api/validationService";

export const authService = new AuthService(httpClient);
export const accountService = new AccountService(httpClient);
export const profileService = new ProfileService(httpClient);
export const runService = new RunService(httpClient);
export const sessionService = new SessionService(httpClient);
export const validationService = new ValidationService(httpClient);

export type { IAuthService } from "@/features/auth/api/authService";
export type { IAccountService } from "@/features/profile/api/accountService";
export type { IProfileService } from "@/features/profile/api/profileService";
export type { IRunService } from "@/features/runs/api/runService";
export type { ISessionService } from "@/features/session/api/sessionService";
export type { IValidationService } from "@/features/insights/api/validationService";
