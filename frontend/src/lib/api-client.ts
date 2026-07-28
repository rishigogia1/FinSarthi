// API client to communicate with the FastAPI backend.
import { tokenStorage } from "./token-storage";
import { sessionManager } from "./session-manager";

const API_BASE = (import.meta as any).env?.VITE_API_URL || "http://localhost:8001/api/v1";

function getHeaders() {
  const token = tokenStorage.getAccessToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  return headers;
}

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

async function request<T>(path: string, options: RequestInit = {}, isRetry = false): Promise<T> {
  const fetchUrl = `${API_BASE}${path}`;
  let response: Response;

  try {
    response = await fetch(fetchUrl, {
      ...options,
      headers: {
        ...getHeaders(),
        ...options.headers,
      },
    });
  } catch (err: any) {
    throw new ApiError("Failed to connect to backend server", 0);
  }

  if (!response.ok) {
    // Check if 401 and try silent token refresh
    if (response.status === 401 && !isRetry && !path.startsWith("/auth/")) {
      try {
        await sessionManager.handleTokenRefresh((refreshToken) =>
          api.refreshTokenDirect(refreshToken)
        );
        // Retry original request once with new token
        return await request<T>(path, options, true);
      } catch {
        if (typeof window !== "undefined") {
          sessionManager.clearSession();
          const currentPath = window.location.pathname + window.location.search;
          if (!currentPath.startsWith("/auth/")) {
            sessionStorage.setItem("auth_redirect", currentPath);
            window.location.href = "/auth/login";
          }
        }
      }
    }

    let errMsg = "An error occurred";
    try {
      const errorData = await response.json();
      errMsg = errorData?.detail?.error?.message || errorData?.detail || errMsg;
    } catch {
      // ignore
    }
    throw new ApiError(errMsg, response.status);
  }

  if (response.status === 204) {
    return {} as T;
  }

  return response.json();
}

export const api = {
  // Auth
  async login(payload: any) {
    const data = await request<any>("/auth/login", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    if (data?.tokens?.access_token) {
      tokenStorage.setAccessToken(data.tokens.access_token);
      tokenStorage.setRefreshToken(data.tokens.refresh_token);
      sessionManager.setCurrentUser(data.user);
    }
    return data;
  },

  async register(payload: any) {
    const data = await request<any>("/auth/register", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    if (data?.tokens?.access_token) {
      tokenStorage.setAccessToken(data.tokens.access_token);
      tokenStorage.setRefreshToken(data.tokens.refresh_token);
      sessionManager.setCurrentUser(data.user);
    }
    return data;
  },

  async refreshTokenDirect(refreshToken: string) {
    const data = await request<any>("/auth/refresh", {
      method: "POST",
      body: JSON.stringify({ refresh_token: refreshToken }),
    });
    return {
      access_token: data.access_token,
      refresh_token: data.refresh_token,
    };
  },

  async logout() {
    await sessionManager.logout((rt) =>
      request<any>("/auth/logout", {
        method: "POST",
        body: JSON.stringify({ refresh_token: rt }),
      })
    );
  },

  isLoggedIn() {
    return !!tokenStorage.getAccessToken() || !!tokenStorage.getRefreshToken();
  },

  // User & Profile
  async getMe() {
    return request<any>("/users/me");
  },

  async updateMe(payload: any) {
    return request<any>("/users/me", {
      method: "PATCH",
      body: JSON.stringify(payload),
    });
  },

  async getPreferences() {
    return request<any>("/users/me/preferences");
  },

  async updatePreferences(payload: any) {
    return request<any>("/users/me/preferences", {
      method: "PATCH",
      body: JSON.stringify(payload),
    });
  },

  // Chat
  async getConversations() {
    return request<any[]>("/chat/conversations");
  },

  async createConversation(payload: any) {
    const bodyObj = typeof payload === "string" ? { title: payload } : payload;
    return request<any>("/chat/conversations", {
      method: "POST",
      body: JSON.stringify(bodyObj),
    });
  },

  async updateConversation(conversationId: string, title: string) {
    return request<any>(`/chat/conversations/${conversationId}`, {
      method: "PATCH",
      body: JSON.stringify({ title }),
    });
  },

  async deleteConversation(conversationId: string) {
    return request<any>(`/chat/conversations/${conversationId}`, {
      method: "DELETE",
    });
  },

  async launchWorkflow(workflow_type: string) {
    return request<{ conversation: any; messages: any[]; dynamic_chips: string[] }>("/chat/workflows/launch", {
      method: "POST",
      body: JSON.stringify({ workflow_type }),
    });
  },

  async getMessages(conversationId: string) {
    return request<any[]>(`/chat/conversations/${conversationId}/messages`);
  },

  async sendMessage(conversationId: string, content: string, agent_name = "Planner") {
    return request<any>(`/chat/conversations/${conversationId}/messages`, {
      method: "POST",
      body: JSON.stringify({ content, agent_name }),
    });
  },

  // Team Dashboard
  async getTeamDashboard() {
    return request<any>("/dashboard/team");
  },

  // Planner V2 & Finance Transactions
  async getPlannerSummary(year?: number, month?: number) {
    const query = [];
    if (year) query.push(`year=${year}`);
    if (month) query.push(`month=${month}`);
    const qStr = query.length ? `?${query.join("&")}` : "";
    return request<any>(`/planner/summary${qStr}`);
  },

  async getTransactions(limit = 100) {
    return request<any>(`/finance/transactions?limit=${limit}&raw=true`);
  },

  async getTransactionsPaginated(params: Record<string, any> = {}) {
    const query = new URLSearchParams();
    Object.entries(params).forEach(([key, val]) => {
      if (val !== undefined && val !== null && val !== "") {
        query.append(key, String(val));
      }
    });
    const qStr = query.toString() ? `?${query.toString()}` : "";
    return request<{
      items: any[];
      total: number;
      page: number;
      page_size: number;
      total_pages: number;
    }>(`/finance/transactions${qStr}`);
  },

  async getTransaction(id: string) {
    return request<any>(`/finance/transactions/${id}`);
  },

  async createTransaction(payload: any) {
    return request<any>("/finance/transactions", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  async updateTransaction(id: string, payload: any) {
    return request<any>(`/finance/transactions/${id}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    });
  },

  async deleteTransaction(id: string) {
    return request<any>(`/finance/transactions/${id}`, {
      method: "DELETE",
    });
  },

  // Coach V2
  async getCoachSummary(year?: number, month?: number) {
    const query = [];
    if (year) query.push(`year=${year}`);
    if (month) query.push(`month=${month}`);
    const qStr = query.length ? `?${query.join("&")}` : "";
    return request<any>(`/coach/summary${qStr}`);
  },
};
