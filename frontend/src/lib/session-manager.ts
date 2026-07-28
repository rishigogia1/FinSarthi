/**
 * lib/session-manager.ts — Session & Identity Lifecycle Manager.
 * 
 * Sits between AuthContext and api-client to manage:
 *  - App boot session restoration
 *  - Silent mutex-guarded refresh token rotation
 *  - Network connection error backoffs for backend restarts (ECONNREFUSED, 502, 503, 504)
 *  - Complete logout cleanup
 */

import { tokenStorage, TokenStorage } from "./token-storage";

export interface UserProfile {
  id: string;
  name: string;
  email: string;
  income_pattern?: string;
  risk_appetite?: string;
  literacy_level?: string;
  language_preference?: string;
}

type AuthStateListener = (user: UserProfile | null, ready: boolean) => void;

class SessionManager {
  private storage: TokenStorage;
  private isRefreshing = false;
  private refreshQueue: Array<{
    resolve: (token: string) => void;
    reject: (err: any) => void;
  }> = [];
  private listeners: Set<AuthStateListener> = new Set();
  private currentUser: UserProfile | null = null;
  private isWorkspaceReady = false;

  constructor(storage: TokenStorage = tokenStorage) {
    this.storage = storage;
  }

  public subscribe(listener: AuthStateListener): () => void {
    this.listeners.add(listener);
    // Initial emit
    listener(this.currentUser, this.isWorkspaceReady);
    return () => this.listeners.delete(listener);
  }

  private notify() {
    this.listeners.forEach((listener) =>
      listener(this.currentUser, this.isWorkspaceReady)
    );
  }

  public getCurrentUser(): UserProfile | null {
    return this.currentUser;
  }

  public isReady(): boolean {
    return this.isWorkspaceReady;
  }

  public setCurrentUser(user: UserProfile | null) {
    this.currentUser = user;
    this.isWorkspaceReady = true;
    this.notify();
  }

  /**
   * App boot restoration flow:
   * 1. Read stored tokens
   * 2. Refresh token if access token missing or expired
   * 3. Fetch current user (/users/me)
   * 4. Set workspaceReady = true
   */
  public async bootSession(
    fetchMeFn: () => Promise<UserProfile>,
    refreshFn: (refreshToken: string) => Promise<{ access_token: string; refresh_token: string }>
  ): Promise<UserProfile | null> {
    const accessToken = this.storage.getAccessToken();
    const refreshToken = this.storage.getRefreshToken();

    if (!accessToken && !refreshToken) {
      this.currentUser = null;
      this.isWorkspaceReady = true;
      this.notify();
      return null;
    }

    try {
      // 1. Try getMe with current access token
      if (accessToken) {
        try {
          const user = await this.executeWithRetry(() => fetchMeFn());
          this.currentUser = user;
          this.isWorkspaceReady = true;
          this.notify();
          return user;
        } catch (err: any) {
          // If 401, proceed to refresh token below
          if (err?.status !== 401) {
            // Transient error retry already handled inside executeWithRetry
          }
        }
      }

      // 2. If access token missing or getMe returned 401, attempt silent refresh
      if (refreshToken) {
        const newAccessToken = await this.handleTokenRefresh(refreshFn);
        if (newAccessToken) {
          const user = await this.executeWithRetry(() => fetchMeFn());
          this.currentUser = user;
          this.isWorkspaceReady = true;
          this.notify();
          return user;
        }
      }
    } catch (err) {
      console.warn("Session restoration failed:", err);
    }

    // Session invalid or refresh failed
    this.clearSession();
    return null;
  }

  /**
   * Mutex-guarded token refresh with queueing for concurrent requests.
   */
  public async handleTokenRefresh(
    refreshFn: (refreshToken: string) => Promise<{ access_token: string; refresh_token: string }>
  ): Promise<string> {
    const refreshToken = this.storage.getRefreshToken();
    if (!refreshToken) {
      this.clearSession();
      throw new Error("No refresh token available");
    }

    if (this.isRefreshing) {
      return new Promise<string>((resolve, reject) => {
        this.refreshQueue.push({ resolve, reject });
      });
    }

    this.isRefreshing = true;

    try {
      const data = await refreshFn(refreshToken);
      this.storage.setAccessToken(data.access_token);
      this.storage.setRefreshToken(data.refresh_token);

      const newToken = data.access_token;
      this.refreshQueue.forEach((prom) => prom.resolve(newToken));
      this.refreshQueue = [];
      this.isRefreshing = false;
      return newToken;
    } catch (err) {
      this.refreshQueue.forEach((prom) => prom.reject(err));
      this.refreshQueue = [];
      this.isRefreshing = false;
      this.clearSession();
      throw err;
    }
  }

  /**
   * Executes a network request with exponential backoff retries for transient backend disconnects (ECONNREFUSED, 502, 503, 504).
   */
  public async executeWithRetry<T>(
    requestFn: () => Promise<T>,
    maxRetries = 3
  ): Promise<T> {
    let attempt = 0;
    while (true) {
      try {
        return await requestFn();
      } catch (err: any) {
        attempt++;
        const status = err?.status || err?.statusCode;
        const isTransient =
          !status || status === 502 || status === 503 || status === 504 || err?.message?.includes("Failed to fetch");

        if (isTransient && attempt <= maxRetries) {
          const backoffMs = Math.pow(2, attempt) * 250; // 500ms, 1000ms, 2000ms
          await new Promise((res) => setTimeout(res, backoffMs));
          continue;
        }
        throw err;
      }
    }
  }

  /**
   * Complete logout lifecycle.
   */
  public async logout(
    logoutApiFn?: (refreshToken: string) => Promise<any>
  ): Promise<void> {
    const refreshToken = this.storage.getRefreshToken();
    if (refreshToken && logoutApiFn) {
      try {
        await logoutApiFn(refreshToken);
      } catch {
        // Ignore logout revocation errors on network drop
      }
    }
    this.clearSession();
  }

  public clearSession(): void {
    this.storage.clear();
    this.currentUser = null;
    this.isWorkspaceReady = true;
    this.notify();
  }
}

export const sessionManager = new SessionManager();
