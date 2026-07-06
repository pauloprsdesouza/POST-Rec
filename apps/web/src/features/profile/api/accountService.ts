import type { UserAccount } from "@/shared/types/api";
import type { IHttpClient } from "@/shared/api/httpClient";

export interface IAccountService {
  getAccount(token: string): Promise<UserAccount>;
  updateAccount(token: string, data: UserAccount): Promise<UserAccount>;
}

export class AccountService implements IAccountService {
  private client: IHttpClient;

  constructor(client: IHttpClient) {
    this.client = client;
  }

  getAccount(token: string): Promise<UserAccount> {
    return this.client.get("/api/v1/users/me/account", { token });
  }

  updateAccount(token: string, data: UserAccount): Promise<UserAccount> {
    return this.client.put("/api/v1/users/me/account", data, { token });
  }
}

import { httpClient } from "@/shared/api/httpClient";

export const accountService = new AccountService(httpClient);
