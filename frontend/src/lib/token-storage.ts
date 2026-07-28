/**
 * lib/token-storage.ts — TokenStorage abstraction layer.
 * 
 * Abstracts access & refresh token persistence so the app can easily migrate
 * from localStorage to HTTP-only cookies in production without altering code logic.
 */

export interface TokenStorage {
  getAccessToken(): string | null;
  setAccessToken(token: string): void;
  getRefreshToken(): string | null;
  setRefreshToken(token: string): void;
  clear(): void;
}

export class LocalStorageTokenStorage implements TokenStorage {
  private ACCESS_TOKEN_KEY = "token";
  private REFRESH_TOKEN_KEY = "refresh_token";

  getAccessToken(): string | null {
    if (typeof window === "undefined") return null;
    return localStorage.getItem(this.ACCESS_TOKEN_KEY);
  }

  setAccessToken(token: string): void {
    if (typeof window === "undefined") return;
    localStorage.setItem(this.ACCESS_TOKEN_KEY, token);
  }

  getRefreshToken(): string | null {
    if (typeof window === "undefined") return null;
    return localStorage.getItem(this.REFRESH_TOKEN_KEY);
  }

  setRefreshToken(token: string): void {
    if (typeof window === "undefined") return;
    localStorage.setItem(this.REFRESH_TOKEN_KEY, token);
  }

  clear(): void {
    if (typeof window === "undefined") return;
    localStorage.removeItem(this.ACCESS_TOKEN_KEY);
    localStorage.removeItem(this.REFRESH_TOKEN_KEY);
  }
}

export const tokenStorage: TokenStorage = new LocalStorageTokenStorage();
