import { createFileRoute, Outlet, useRouterState, useNavigate } from "@tanstack/react-router";
import { SidebarProvider, SidebarTrigger, SidebarInset } from "@/components/ui/sidebar";
import { AppSidebar } from "@/components/app-sidebar";
import { Search, Bell, Command } from "lucide-react";
import { Button } from "@/components/ui/button";
import { createContext, useContext, useEffect } from "react";
import { useAuth } from "@/context/auth-context";
import { UserProfile } from "@/lib/session-manager";

export { type UserProfile };

export const UserContext = createContext<{
  user: UserProfile | null;
  loading: boolean;
  logout: () => void;
} | null>(null);

export const useUser = () => {
  const ctx = useContext(UserContext);
  if (!ctx) throw new Error("useUser must be used within UserProvider");
  return ctx;
};

export const Route = createFileRoute("/app")({
  component: AppLayout,
});

const titles: Record<string, { t: string; s: string }> = {
  "/app": { t: "Workspace", s: "Your personal AI financial workspace" },
  "/app/transactions": { t: "Transactions", s: "Manage your daily cashflow & tracking" },
  "/app/chat": { t: "Conversations", s: "Chat with your AI team" },
  "/app/team": { t: "AI Team", s: "Five agents. One workspace." },
  "/app/knowledge": { t: "Knowledge Hub", s: "Schemes, guides, and how-tos" },
  "/app/insights": { t: "Insights", s: "Your financial health at a glance" },
  "/app/goals": { t: "Goals", s: "Plan, save, and track progress" },
  "/app/profile": { t: "Profile", s: "Your account and preferences" },
  "/app/settings": { t: "Settings", s: "Preferences and accessibility" },
};

function AppLayout() {
  const { location } = useRouterState();
  const pathname = location.pathname;
  const meta = titles[pathname] ?? { t: "Workspace", s: "" };
  const navigate = useNavigate();
  const { user, isAuthenticated, isLoading, workspaceReady, logout } = useAuth();

  useEffect(() => {
    if (!isLoading && workspaceReady && !isAuthenticated) {
      const targetUrl = location.href;
      if (typeof window !== "undefined" && targetUrl && !targetUrl.includes("/auth/")) {
        sessionStorage.setItem("auth_redirect", targetUrl);
      }
      navigate({ to: "/auth/login" });
    }
  }, [isLoading, workspaceReady, isAuthenticated, navigate, location.href]);

  if (isLoading || !workspaceReady) {
    return (
      <div className="flex min-h-dvh w-full items-center justify-center bg-background">
        <div className="flex flex-col items-center gap-3">
          <span className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
          <p className="text-sm text-muted-foreground font-medium">Restoring FinSarthi workspace...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return null;
  }

  const handleLogout = async () => {
    await logout();
    navigate({ to: "/auth/login" });
  };

  return (
    <UserContext.Provider value={{ user, loading: false, logout: handleLogout }}>
      <SidebarProvider>
        <div className="flex min-h-dvh w-full bg-background">
          <AppSidebar />
          <SidebarInset>
            <header className="sticky top-0 z-30 flex h-16 items-center gap-3 border-b border-border bg-background/80 px-4 backdrop-blur sm:px-6">
              <SidebarTrigger />
              <div className="hidden sm:block">
                <p className="text-sm font-semibold leading-tight">{meta.t}</p>
                <p className="text-xs text-muted-foreground">{meta.s}</p>
              </div>
              <div className="ml-auto flex items-center gap-2">
                <Button
                  variant="outline"
                  className="hidden h-9 gap-2 rounded-lg px-3 text-muted-foreground md:inline-flex"
                  onClick={() => {
                    const event = new KeyboardEvent("keydown", { key: "k", metaKey: true });
                    document.dispatchEvent(event);
                  }}
                >
                  <Search className="h-4 w-4" />
                  <span className="text-xs">Search…</span>
                  <kbd className="ml-4 inline-flex items-center gap-1 rounded border border-border bg-muted px-1.5 py-0.5 text-[10px] font-medium">
                    <Command className="h-3 w-3" />K
                  </kbd>
                </Button>
                <Button variant="ghost" size="icon" aria-label="Notifications">
                  <Bell className="h-4 w-4" />
                </Button>
              </div>
            </header>
            <main className="flex-1">
              <Outlet />
            </main>
          </SidebarInset>
        </div>
      </SidebarProvider>
    </UserContext.Provider>
  );
}
