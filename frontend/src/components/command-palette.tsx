import { useEffect, useState } from "react";
import { useNavigate } from "@tanstack/react-router";
import {
  CommandDialog,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
  CommandSeparator,
} from "@/components/ui/command";
import {
  LayoutGrid,
  MessagesSquare,
  Users,
  BookOpen,
  BarChart3,
  Target,
  User,
  Settings,
  Sparkles,
  Search,
} from "lucide-react";

export function CommandPalette() {
  const [open, setOpen] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    const down = (e: KeyboardEvent) => {
      if ((e.key === "k" || e.key === "K") && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        setOpen((o) => !o);
      }
    };
    document.addEventListener("keydown", down);
    return () => document.removeEventListener("keydown", down);
  }, []);

  const go = (to: string) => {
    setOpen(false);
    navigate({ to });
  };

  return (
    <CommandDialog open={open} onOpenChange={setOpen}>
      <CommandInput placeholder="Search FinSarthi — pages, chats, knowledge…" />
      <CommandList>
        <CommandEmpty>No results found.</CommandEmpty>
        <CommandGroup heading="Quick actions">
          <CommandItem onSelect={() => go("/app/chat")}>
            <Sparkles /> Start a new chat
          </CommandItem>
          <CommandItem onSelect={() => go("/app/knowledge")}>
            <Search /> Search Knowledge Hub
          </CommandItem>
        </CommandGroup>
        <CommandSeparator />
        <CommandGroup heading="Navigate">
          <CommandItem onSelect={() => go("/app")}>
            <LayoutGrid /> Workspace
          </CommandItem>
          <CommandItem onSelect={() => go("/app/chat")}>
            <MessagesSquare /> Conversations
          </CommandItem>
          <CommandItem onSelect={() => go("/app/team")}>
            <Users /> AI Team
          </CommandItem>
          <CommandItem onSelect={() => go("/app/knowledge")}>
            <BookOpen /> Knowledge Hub
          </CommandItem>
          <CommandItem onSelect={() => go("/app/insights")}>
            <BarChart3 /> Insights
          </CommandItem>
          <CommandItem onSelect={() => go("/app/goals")}>
            <Target /> Goals
          </CommandItem>
          <CommandItem onSelect={() => go("/app/profile")}>
            <User /> Profile
          </CommandItem>
          <CommandItem onSelect={() => go("/app/settings")}>
            <Settings /> Settings
          </CommandItem>
        </CommandGroup>
      </CommandList>
    </CommandDialog>
  );
}
