import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useState, useRef } from "react";
import { motion } from "framer-motion";
import {
  ArrowUp,
  Mic,
  Paperclip,
  Copy,
  ThumbsUp,
  ThumbsDown,
  Sparkles,
  Search,
  Plus,
  MoreVertical,
  Pencil,
  Trash2,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";
import { api } from "@/lib/api-client";
import { toast } from "sonner";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";

export const Route = createFileRoute("/app/chat")({
  component: ChatPage,
  validateSearch: (search: Record<string, unknown>) => {
    return {
      prompt: (search.prompt as string) || undefined,
      activeId: (search.activeId as string) || undefined,
    };
  },
});

function ChatPage() {
  const search = Route.useSearch();
  const [conversations, setConversations] = useState<any[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [messages, setMessages] = useState<any[]>([]);
  const [inputText, setInputText] = useState("");
  const [loading, setLoading] = useState(false);
  const [sending, setSending] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [deleteTarget, setDeleteTarget] = useState<any | null>(null);
  const [renameTarget, setRenameTarget] = useState<any | null>(null);
  const [renameTitleInput, setRenameTitleInput] = useState("");
  const [actionLoading, setActionLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const activeConv = conversations.find((c) => c.id === activeId);

  const handleConfirmDelete = async () => {
    if (!deleteTarget) return;
    setActionLoading(true);
    try {
      await api.deleteConversation(deleteTarget.id);
      const remaining = conversations.filter((c) => c.id !== deleteTarget.id);
      setConversations(remaining);
      toast.success("Conversation deleted");

      if (activeId === deleteTarget.id) {
        if (remaining.length > 0) {
          setActiveId(remaining[0].id);
        } else {
          setActiveId(null);
          setMessages([]);
        }
      }
    } catch {
      toast.error("Failed to delete conversation");
    } finally {
      setActionLoading(false);
      setDeleteTarget(null);
    }
  };

  const handleConfirmRename = async () => {
    if (!renameTarget || !renameTitleInput.trim()) return;
    setActionLoading(true);
    try {
      const updated = await api.updateConversation(renameTarget.id, renameTitleInput.trim());
      setConversations((prev) =>
        prev.map((c) => (c.id === renameTarget.id ? { ...c, title: updated.title } : c))
      );
      toast.success("Conversation renamed");
    } catch {
      toast.error("Failed to rename conversation");
    } finally {
      setActionLoading(false);
      setRenameTarget(null);
    }
  };

  const fetchConversations = async (selectFirst = false) => {
    try {
      const data = await api.getConversations();
      setConversations(data);
      if (search.activeId) {
        setActiveId(search.activeId);
      } else if (data.length > 0) {
        if (selectFirst && !activeId) {
          setActiveId(data[0].id);
        }
      } else {
        const newConv = await api.createConversation({ title: "FinSarthi Advisor" });
        setConversations([newConv]);
        setActiveId(newConv.id);
      }
    } catch {
      toast.error("Failed to load chats");
    }
  };

  useEffect(() => {
    fetchConversations(true);
  }, [search.activeId]);

  // Handle prefilled prompt from query params
  useEffect(() => {
    if (search.prompt && activeId) {
      setInputText(search.prompt);
    }
  }, [search.prompt, activeId]);

  // Load messages when active conversation changes
  useEffect(() => {
    if (!activeId) return;

    const loadMessages = async () => {
      setLoading(true);
      try {
        const data = await api.getMessages(activeId);
        setMessages(data);
      } catch {
        toast.error("Failed to load messages");
      } finally {
        setLoading(false);
      }
    };

    loadMessages();
  }, [activeId]);

  // Auto scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, sending]);

  const handleCreateChat = async () => {
    try {
      const newConv = await api.createConversation("New Conversation");
      setConversations(prev => [newConv, ...prev]);
      setActiveId(newConv.id);
      setInputText("");
    } catch {
      toast.error("Failed to create new chat");
    }
  };

  const handleSendMessage = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!activeId || !inputText.trim() || sending) return;

    const content = inputText;
    setInputText("");
    setSending(true);

    try {
      const updatedMessages = await api.sendMessage(activeId, content);
      setMessages(updatedMessages);
      // Refresh list to pick up possible title changes
      fetchConversations(false);
    } catch (err: any) {
      toast.error(err.message || "Failed to send message");
    } finally {
      setSending(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const agentStarters = [
    { label: "📊 Planner", prompt: "How much did I spend this month?" },
    { label: "🎯 Coach", prompt: "Am I overspending?" },
    { label: "🛡️ Guardian", prompt: "Is this payment link safe?" },
    { label: "💡 Learn", prompt: "Explain SIP and Mutual Funds" },
    { label: "🧭 Navigator", prompt: "Can I afford a ₹1.8 lakh bike?" },
  ];

  const handleSelectStarter = (promptText: string) => {
    setInputText(promptText);
  };

  const renderMessageContent = (m: any) => {
    if (m.role === "user") return m.content;

    const badgeMatch = m.content.match(/^\[(.*?)\]\s*/);
    let badgeText = null;
    let bodyText = m.content;

    if (badgeMatch) {
      badgeText = badgeMatch[1];
      bodyText = m.content.slice(badgeMatch[0].length);
    }

    return (
      <div className="space-y-1.5">
        {badgeText && (
          <div className="inline-flex items-center gap-1 rounded-full bg-primary/10 px-2.5 py-0.5 text-xs font-semibold text-primary">
            {badgeText}
          </div>
        )}
        <div>{bodyText}</div>
      </div>
    );
  };

  const filteredConversations = conversations.filter((c) =>
    (c.title || "").toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="grid h-[calc(100dvh-4rem)] grid-cols-1 md:grid-cols-[280px_1fr]">
      {/* Conversation list */}
      <aside className="hidden border-r border-border md:flex md:flex-col">
        <div className="border-b border-border p-3">
          <Button className="w-full justify-start gap-2" size="sm" onClick={handleCreateChat}>
            <Plus className="h-4 w-4" /> New chat
          </Button>
          <div className="relative mt-3">
            <Search className="pointer-events-none absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input 
              placeholder="Search chats" 
              className="h-9 pl-8" 
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
        </div>
        <div className="flex-1 overflow-y-auto p-2 space-y-1">
          {filteredConversations.map((c) => (
            <div
              key={c.id}
              className={cn(
                "group relative flex w-full items-center justify-between rounded-lg px-3 py-2 text-left transition-colors",
                activeId === c.id
                  ? "bg-secondary text-secondary-foreground font-semibold"
                  : "hover:bg-secondary/60 text-muted-foreground hover:text-foreground"
              )}
            >
              <button
                onClick={() => setActiveId(c.id)}
                className="flex flex-1 flex-col items-start min-w-0 pr-2 text-left"
              >
                <p className="truncate w-full text-sm font-medium">
                  {c.icon ? `${c.icon} ` : ""}{c.title || "New Chat"}
                </p>
                <p className="text-[10px] opacity-70">
                  {new Date(c.created_at).toLocaleDateString(undefined, { month: "short", day: "numeric" })}
                </p>
              </button>

              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-7 w-7 opacity-0 group-hover:opacity-100 transition-opacity data-[state=open]:opacity-100 shrink-0"
                    onClick={(e) => e.stopPropagation()}
                  >
                    <MoreVertical className="h-4 w-4" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="w-40">
                  <DropdownMenuItem
                    onClick={(e) => {
                      e.stopPropagation();
                      setRenameTarget(c);
                      setRenameTitleInput(c.title || "");
                    }}
                  >
                    <Pencil className="mr-2 h-4 w-4" /> Rename
                  </DropdownMenuItem>
                  <DropdownMenuItem
                    className="text-destructive focus:text-destructive"
                    onClick={(e) => {
                      e.stopPropagation();
                      setDeleteTarget(c);
                    }}
                  >
                    <Trash2 className="mr-2 h-4 w-4" /> Delete
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          ))}
        </div>
      </aside>

      {/* Chat */}
      <section className="flex min-h-0 flex-col bg-background">
        {activeConv?.primary_agent && (
          <div className="flex items-center justify-between border-b border-border bg-secondary/20 px-6 py-2 text-xs">
            <div className="flex items-center gap-2">
              <span className="font-semibold text-foreground">{activeConv.icon || "✨"} {activeConv.title}</span>
              <span className="rounded-full bg-primary/10 px-2 py-0.5 font-semibold text-primary uppercase text-[10px]">
                {activeConv.primary_agent}
              </span>
            </div>
            {activeConv.supporting_agents && (
              <span className="text-muted-foreground hidden sm:inline">
                Powered by {activeConv.primary_agent} {Array.isArray(activeConv.supporting_agents) ? `+ ${activeConv.supporting_agents.join(", ")}` : ""}
              </span>
            )}
          </div>
        )}
        <div className="flex-1 overflow-y-auto">
          <div className="mx-auto w-full max-w-3xl px-4 py-8 sm:px-6">
            {loading ? (
              <div className="flex justify-center py-12">
                <span className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
              </div>
            ) : messages.length === 0 ? (
              <div className="text-center py-12 space-y-4">
                <Sparkles className="mx-auto h-12 w-12 text-primary/40" />
                <h3 className="text-lg font-semibold">FinSarthi AI Financial Copilot Workspace</h3>
                <p className="text-sm text-muted-foreground max-w-md mx-auto">
                  Ask Planner (Analytics), Coach (Habits), Guardian (Safety), Learn (Education), or Navigator (Decision Planning).
                </p>
                <div className="flex flex-wrap justify-center gap-2 pt-4">
                  {agentStarters.map((s, idx) => (
                    <Button
                      key={idx}
                      variant="outline"
                      size="sm"
                      className="rounded-full text-xs hover:bg-primary-soft hover:text-primary transition-all"
                      onClick={() => handleSelectStarter(s.prompt)}
                    >
                      {s.label}
                    </Button>
                  ))}
                </div>
              </div>
            ) : (
              messages.map((m) => (
                <div key={m.id} className={cn("mb-6 flex gap-3", m.role === "user" ? "justify-end" : "justify-start")}>
                  {m.role !== "user" && (
                    <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary-soft text-primary">
                      <Sparkles className="h-4 w-4" />
                    </div>
                  )}
                  <div className={cn(
                    "max-w-[85%] rounded-2xl px-4 py-3 text-sm shadow-soft leading-relaxed whitespace-pre-wrap",
                    m.role === "user" 
                      ? "rounded-tr-md bg-primary text-primary-foreground" 
                      : "rounded-tl-md bg-secondary text-secondary-foreground border border-border"
                  )}>
                    {renderMessageContent(m)}
                  </div>
                  {m.role === "user" && (
                    <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-secondary text-xs font-semibold">
                      U
                    </div>
                  )}
                </div>
              ))
            )}
            {sending && (
              <div className="flex items-center gap-2 text-xs text-muted-foreground py-2">
                <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary-soft text-primary animate-pulse">
                  <Sparkles className="h-4 w-4" />
                </div>
                <span>FinSarthi AI Copilot is reasoning...</span>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* Quick Agent Starter Chips */}
        <div className="border-t border-border bg-background px-3 py-2">
          <div className="mx-auto flex max-w-3xl gap-2 overflow-x-auto no-scrollbar py-1">
            {agentStarters.map((s, idx) => (
              <Button
                key={idx}
                variant="outline"
                size="sm"
                className="shrink-0 rounded-full text-xs h-7 px-3 hover:bg-primary-soft hover:text-primary"
                onClick={() => handleSelectStarter(s.prompt)}
              >
                {s.label}
              </Button>
            ))}
          </div>
        </div>

        {/* Sticky input */}
        <div className="border-t border-border bg-background/80 p-3 backdrop-blur sm:p-4">
          <div className="mx-auto w-full max-w-3xl">
            <form onSubmit={handleSendMessage} className="rounded-2xl border border-border bg-card p-2 shadow-soft">
              <Textarea
                placeholder="Ask Planner, Coach, Guardian, Learn, or Navigator…"
                className="min-h-14 resize-none border-0 bg-transparent p-2 text-base shadow-none focus-visible:ring-0"
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                onKeyDown={handleKeyDown}
                disabled={sending}
              />
              <div className="flex items-center gap-1 border-t border-border pt-2">
                <Button type="button" variant="ghost" size="icon" aria-label="Attach">
                  <Paperclip className="h-4 w-4" />
                </Button>
                <Button type="button" variant="ghost" size="icon" aria-label="Voice">
                  <Mic className="h-4 w-4" />
                </Button>
                <p className="ml-1 hidden text-xs text-muted-foreground sm:block">
                  Press Enter to send · Shift+Enter for new line
                </p>
                <Button type="submit" size="icon" className="ml-auto" aria-label="Send" disabled={sending || !inputText.trim()}>
                  <ArrowUp className="h-4 w-4" />
                </Button>
              </div>
            </form>
          </div>
        </div>
      </section>

      {/* Delete Confirmation Modal */}
      <Dialog open={!!deleteTarget} onOpenChange={(open) => !open && setDeleteTarget(null)}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Delete Conversation?</DialogTitle>
            <DialogDescription>
              Are you sure you want to permanently delete{" "}
              <span className="font-semibold text-foreground">
                "{deleteTarget?.title || "this conversation"}"
              </span>
              ? This action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter className="gap-2 sm:gap-0">
            <Button variant="outline" onClick={() => setDeleteTarget(null)} disabled={actionLoading}>
              Cancel
            </Button>
            <Button variant="destructive" onClick={handleConfirmDelete} disabled={actionLoading}>
              {actionLoading ? "Deleting..." : "Delete"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Rename Modal */}
      <Dialog open={!!renameTarget} onOpenChange={(open) => !open && setRenameTarget(null)}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Rename Conversation</DialogTitle>
            <DialogDescription>
              Enter a new title for this conversation session.
            </DialogDescription>
          </DialogHeader>
          <div className="py-2">
            <Input
              value={renameTitleInput}
              onChange={(e) => setRenameTitleInput(e.target.value)}
              placeholder="Conversation title"
              onKeyDown={(e) => {
                if (e.key === "Enter") handleConfirmRename();
              }}
            />
          </div>
          <DialogFooter className="gap-2 sm:gap-0">
            <Button variant="outline" onClick={() => setRenameTarget(null)} disabled={actionLoading}>
              Cancel
            </Button>
            <Button onClick={handleConfirmRename} disabled={actionLoading || !renameTitleInput.trim()}>
              {actionLoading ? "Saving..." : "Save"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
