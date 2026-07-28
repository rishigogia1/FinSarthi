import { useEffect, useState } from "react";
import { Link, useRouterState } from "@tanstack/react-router";
import { api } from "@/lib/api-client";
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/components/ui/sidebar";
import {
  LayoutGrid,
  MessagesSquare,
  Users,
  BookOpen,
  BarChart3,
  Target,
  Receipt,
  User,
  Settings,
  Sparkles,
  LogOut,
} from "lucide-react";
import { Logo } from "@/components/logo";
import { conversations } from "@/lib/mock-data";
import { Badge } from "@/components/ui/badge";
import { useUser } from "@/routes/app";
import { Button } from "@/components/ui/button";

const primary = [
  { title: "Workspace", url: "/app", icon: LayoutGrid, exact: true },
  { title: "Transactions", url: "/app/transactions", icon: Receipt },
  { title: "Conversations", url: "/app/chat", icon: MessagesSquare },
  { title: "AI Team", url: "/app/team", icon: Users },
  { title: "Knowledge Hub", url: "/app/knowledge", icon: BookOpen },
  { title: "Insights", url: "/app/insights", icon: BarChart3 },
  { title: "Goals", url: "/app/goals", icon: Target },
];

const secondary = [
  { title: "Profile", url: "/app/profile", icon: User },
  { title: "Settings", url: "/app/settings", icon: Settings },
];

export function AppSidebar() {
  const pathname = useRouterState({ select: (r) => r.location.pathname });
  const { user, logout } = useUser();
  const [userConvs, setUserConvs] = useState<any[]>([]);

  useEffect(() => {
    api.getConversations().then(setUserConvs).catch(() => {});
  }, [pathname]);
  
  const isActive = (url: string, exact?: boolean) =>
    exact ? pathname === url : pathname === url || pathname.startsWith(url + "/");

  const initials = user?.name
    ? user.name
        .split(" ")
        .map((n) => n[0])
        .join("")
        .toUpperCase()
    : "U";

  return (
    <Sidebar collapsible="icon">
      <SidebarHeader className="border-b border-sidebar-border">
        <div className="flex items-center gap-2 px-1 py-1">
          <Logo />
        </div>
      </SidebarHeader>

      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupContent>
            <SidebarMenu>
              {primary.map((item) => (
                <SidebarMenuItem key={item.title}>
                  <SidebarMenuButton asChild isActive={isActive(item.url, item.exact)} tooltip={item.title}>
                    <Link to={item.url}>
                      <item.icon />
                      <span>{item.title}</span>
                    </Link>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>

        <SidebarGroup>
          <SidebarGroupLabel>Recent chats</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {userConvs.slice(0, 5).map((c) => (
                <SidebarMenuItem key={c.id}>
                  <SidebarMenuButton asChild tooltip={c.title}>
                    <Link to="/app/chat" search={{ activeId: c.id }}>
                      <Sparkles />
                      <span className="truncate">{c.title || "New Chat"}</span>
                    </Link>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>

        <SidebarGroup>
          <SidebarGroupContent>
            <SidebarMenu>
              {secondary.map((item) => (
                <SidebarMenuItem key={item.title}>
                  <SidebarMenuButton asChild isActive={isActive(item.url)} tooltip={item.title}>
                    <Link to={item.url}>
                      <item.icon />
                      <span>{item.title}</span>
                    </Link>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>

      <SidebarFooter className="border-t border-sidebar-border">
        <div className="flex items-center gap-3 px-1 py-2">
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-primary text-sm font-semibold text-primary-foreground">
            {initials}
          </div>
          <div className="min-w-0 flex-1 group-data-[collapsible=icon]:hidden">
            <p className="truncate text-sm font-medium">{user?.name}</p>
            <p className="truncate text-xs text-muted-foreground">{user?.email}</p>
          </div>
          <Button
            variant="ghost"
            size="icon"
            onClick={logout}
            className="group-data-[collapsible=icon]:hidden"
            title="Log out"
          >
            <LogOut className="h-4 w-4 text-muted-foreground hover:text-foreground" />
          </Button>
        </div>
      </SidebarFooter>
    </Sidebar>
  );
}

