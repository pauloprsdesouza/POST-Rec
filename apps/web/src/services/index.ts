import { AuthService } from "./auth/AuthService";
import { AccountService } from "./account/AccountService";
import { httpClient } from "./http/HttpClient";
import { ProfileService } from "./profile/ProfileService";
import { RunService } from "./runs/RunService";
import { SessionService } from "./session/SessionService";
import { ValidationService } from "./validation/ValidationService";

export const authService = new AuthService(httpClient);
export const accountService = new AccountService(httpClient);
export const profileService = new ProfileService(httpClient);
export const runService = new RunService(httpClient);
export const sessionService = new SessionService(httpClient);
export const validationService = new ValidationService(httpClient);

export type { IAuthService } from "./auth/AuthService";
export type { IAccountService } from "./account/AccountService";
export type { IProfileService } from "./profile/ProfileService";
export type { IRunService } from "./runs/RunService";
export type { ISessionService } from "./session/SessionService";
export type { IValidationService } from "./validation/ValidationService";
