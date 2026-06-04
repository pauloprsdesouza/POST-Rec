import type { UserAccount } from "../../types/api";
import type { IHttpClient } from "../http/HttpClient";

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
