/**
 * context/auth-context.tsx — Global Authentication & Workspace Provider.
 */
import React, { createContext, useContext, useEffect, useState } from "react";
import { api } from "@/lib/api-client";
import { sessionManager, UserProfile } from "@/lib/session-manager";

interface AuthContextType {
  user: UserProfile | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  workspaceReady: boolean;
  login: (payload: any) => Promise<any>;
  register: (payload: any) => Promise<any>;
  logout: () => Promise<void>;
  refreshSession: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | null>(null);

export const useAuth = () => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within an AuthProvider");
  return ctx;
};

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<UserProfile | null>(sessionManager.getCurrentUser());
  const [workspaceReady, setWorkspaceReady] = useState(sessionManager.isReady());
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Subscribe to sessionManager updates
    const unsubscribe = sessionManager.subscribe((currentUser, isReady) => {
      setUser(currentUser);
      setWorkspaceReady(isReady);
      setIsLoading(!isReady);
    });

    // Boot session on mount
    sessionManager
      .bootSession(
        () => api.getMe(),
        (rt) => api.refreshTokenDirect(rt)
      )
      .finally(() => {
        setIsLoading(false);
      });

    return () => {
      unsubscribe();
    };
  }, []);

  const handleLogin = async (payload: any) => {
    setIsLoading(true);
    try {
      const res = await api.login(payload);
      return res;
    } finally {
      setIsLoading(false);
    }
  };

  const handleRegister = async (payload: any) => {
    setIsLoading(true);
    try {
      const res = await api.register(payload);
      return res;
    } finally {
      setIsLoading(false);
    }
  };

  const handleLogout = async () => {
    setIsLoading(true);
    try {
      await api.logout();
    } finally {
      setIsLoading(false);
    }
  };

  const handleRefreshSession = async () => {
    await sessionManager.bootSession(
      () => api.getMe(),
      (rt) => api.refreshTokenDirect(rt)
    );
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        isLoading,
        workspaceReady,
        login: handleLogin,
        register: handleRegister,
        logout: handleLogout,
        refreshSession: handleRefreshSession,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};
