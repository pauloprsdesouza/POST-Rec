import type { AuthResponse, OtpRequestResponse } from "@/shared/types/api";
import type { IHttpClient } from "@/shared/api/httpClient";

export interface IAuthService {
  register(
    fullName: string,
    email: string,
    phoneNumber: string,
    whatsappOptIn: boolean,
  ): Promise<OtpRequestResponse>;
  requestLoginOtp(email: string): Promise<OtpRequestResponse>;
  verifyOtp(email: string, code: string): Promise<AuthResponse>;
  health(): Promise<{ status: string }>;
}

export class AuthService implements IAuthService {
  private client: IHttpClient;

  constructor(client: IHttpClient) {
    this.client = client;
  }

  register(
    fullName: string,
    email: string,
    phoneNumber: string,
    whatsappOptIn: boolean,
  ): Promise<OtpRequestResponse> {
    return this.client.post("/api/v1/auth/register", {
      full_name: fullName,
      email,
      phone_number: phoneNumber,
      whatsapp_opt_in: whatsappOptIn,
    });
  }

  requestLoginOtp(email: string): Promise<OtpRequestResponse> {
    return this.client.post("/api/v1/auth/login/otp/request", { email });
  }

  verifyOtp(email: string, code: string): Promise<AuthResponse> {
    return this.client.post("/api/v1/auth/otp/verify", { email, code });
  }

  health(): Promise<{ status: string }> {
    return this.client.get("/api/v1/health");
  }
}
