import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { motion } from "framer-motion";
import {
  Mic,
  ArrowUp,
  Paperclip,
  Sparkles,
  PiggyBank,
  Landmark,
  ShieldCheck,
  Target,
  TrendingUp,
  BookOpen,
  ArrowRight,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { promptCards, suggestedPrompts, agents, insights as mockInsights, currency } from "@/lib/mock-data";
import { cn } from "@/lib/utils";
import { useUser } from "./app";
import { useEffect, useState } from "react";
import { api } from "@/lib/api-client";
import { toast } from "sonner";

export const Route = createFileRoute("/app/")({
  component: WorkspacePage,
});

const iconMap = {
  PiggyBank,
  Landmark,
  ShieldCheck,
  Target,
  TrendingUp,
  BookOpen,
} as const;

function WorkspacePage() {
  const navigate = useNavigate();
  const { user } = useUser();
  const hour = new Date().getHours();
  const greeting = hour < 12 ? "Good morning" : hour < 18 ? "Good afternoon" : "Good evening";
  const [plannerSummary, setPlannerSummary] = useState<any>(null);
  const [prompt, setPrompt] = useState("");
  const [launching, setLaunching] = useState<string | null>(null);

  const handleLaunchWorkflow = async (workflowType: string) => {
    try {
      setLaunching(workflowType);
      const res = await api.launchWorkflow(workflowType);
      navigate({ to: "/app/chat", search: { activeId: res.conversation.id } });
    } catch {
      toast.error("Failed to launch workflow");
    } finally {
      setLaunching(null);
    }
  };

  useEffect(() => {
    api.getPlannerSummary()
      .then(setPlannerSummary)
      .catch(() => {});
  }, []);

  const displayInsights = plannerSummary ? [
    { title: "Monthly Expense", value: currency(plannerSummary.overview.monthly_expense), trend: `Top: ${plannerSummary.analytics.largest_category || "None"}`, tone: "primary" },
    { title: "Monthly Income", value: currency(plannerSummary.overview.monthly_income), trend: "Credited", tone: "success" },
    { title: "Net Cashflow", value: currency(plannerSummary.overview.net_cashflow), trend: `Txs: ${plannerSummary.analytics.total_transactions}`, tone: "success" },
  ] : mockInsights.slice(0, 3);

  return (
    <div className="mx-auto w-full max-w-6xl px-4 py-8 sm:px-6 sm:py-12 lg:px-8">
      <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}>
        <p className="text-sm font-medium text-primary">{greeting}</p>
        <h1 className="mt-1 text-3xl font-semibold tracking-tight sm:text-4xl">
          Hello {user?.name} <span aria-hidden>👋</span>
        </h1>
        <p className="mt-2 text-muted-foreground">What would you like help with today?</p>
      </motion.div>

      {/* Prompt input */}
      <div className="mt-8 rounded-2xl border border-border bg-card p-3 shadow-soft">
        <Textarea
          placeholder="Ask anything about your money — saving, planning, schemes, safety…"
          className="min-h-24 resize-none border-0 bg-transparent p-3 text-base shadow-none focus-visible:ring-0"
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
        />
        <div className="flex items-center gap-2 border-t border-border pt-2">
          <Button variant="ghost" size="icon" aria-label="Attach file">
            <Paperclip className="h-4 w-4" />
          </Button>
          <Button variant="ghost" size="icon" aria-label="Voice input">
            <Mic className="h-4 w-4" />
          </Button>
          <p className="ml-1 hidden text-xs text-muted-foreground sm:block">
            Your AI team responds in seconds.
          </p>
          <Button asChild size="icon" className="ml-auto rounded-lg" aria-label="Send">
            <Link to="/app/chat" search={{ prompt: prompt }}>
              <ArrowUp className="h-4 w-4" />
            </Link>
          </Button>
        </div>
      </div>

      {/* Suggested prompts */}
      <div className="mt-4 flex flex-wrap gap-2">
        {suggestedPrompts.map((p) => (
          <Link
            key={p}
            to="/app/chat"
            search={{ prompt: p }}
            className="rounded-full border border-border bg-card px-3 py-1.5 text-xs text-muted-foreground transition-colors hover:border-primary/40 hover:text-foreground"
          >
            {p}
          </Link>
        ))}
      </div>


      {/* Prompt cards */}
      <section className="mt-10">
        <div className="flex items-end justify-between">
          <h2 className="text-lg font-semibold">Start with</h2>
          <Link to="/app/knowledge" className="text-sm text-primary hover:underline">
            Explore all
          </Link>
        </div>
        <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {promptCards.map((card, i) => {
            const Icon = iconMap[card.icon as keyof typeof iconMap];
            return (
              <motion.div
                key={card.title}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.04 }}
              >
                <button
                  onClick={() => handleLaunchWorkflow(card.workflowType)}
                  disabled={launching === card.workflowType}
                  className="card-soft group flex h-full w-full flex-col text-left p-5 transition-all hover:-translate-y-0.5 hover:shadow-elevated cursor-pointer disabled:opacity-50"
                >
                  <div
                    className={cn(
                      "flex h-10 w-10 items-center justify-center rounded-lg",
                      card.color === "primary" && "bg-primary-soft text-primary",
                      card.color === "success" && "bg-success/10 text-success",
                      card.color === "warning" && "bg-warning/10 text-warning-foreground",
                      card.color === "accent" && "bg-accent text-accent-foreground",
                      card.color === "secondary" && "bg-secondary text-secondary-foreground",
                    )}
                  >
                    <Icon className="h-5 w-5" />
                  </div>
                  <p className="mt-4 font-semibold">{card.title}</p>
                  <p className="mt-1 flex-1 text-sm text-muted-foreground">{card.desc}</p>
                  <span className="mt-4 inline-flex items-center text-sm font-medium text-primary opacity-0 transition-opacity group-hover:opacity-100">
                    {launching === card.workflowType ? "Launching…" : "Start"} <ArrowRight className="ml-1 h-4 w-4" />
                  </span>
                </button>
              </motion.div>
            );
          })}
        </div>
      </section>

      {/* Quick glance */}
      <section className="mt-12 grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <div className="flex items-end justify-between">
            <h2 className="text-lg font-semibold">Your team is on it</h2>
            <Link to="/app/team" className="text-sm text-primary hover:underline">
              View team
            </Link>
          </div>
          <div className="mt-4 grid gap-3 sm:grid-cols-2">
            {agents.slice(0, 4).map((a) => (
              <div key={a.id} className="card-soft flex items-center gap-3 p-4">
                <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary-soft font-semibold text-primary">
                  {a.name[0]}
                </div>
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <p className="truncate text-sm font-medium">{a.name}</p>
                    <span className="inline-flex items-center gap-1 rounded-full bg-secondary px-2 py-0.5 text-[10px] text-muted-foreground">
                      <span className="h-1.5 w-1.5 animate-pulse-dot rounded-full bg-primary" /> Working
                    </span>
                  </div>
                  <p className="truncate text-xs text-muted-foreground">{a.status}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div>
          <div className="flex items-end justify-between">
            <h2 className="text-lg font-semibold">At a glance</h2>
            <Link to="/app/insights" className="text-sm text-primary hover:underline">
              Insights
            </Link>
          </div>
          <div className="mt-4 space-y-3">
            {displayInsights.map((i) => (
              <div key={i.title} className="card-soft flex items-center justify-between p-4">
                <div>
                  <p className="text-xs text-muted-foreground">{i.title}</p>
                  <p className="mt-0.5 text-lg font-semibold">{i.value}</p>
                </div>
                <span
                  className={cn(
                    "rounded-full px-2 py-0.5 text-xs",
                    i.tone === "success" && "bg-success/10 text-success",
                    i.tone === "primary" && "bg-primary-soft text-primary",
                    i.tone === "warning" && "bg-warning/10 text-warning-foreground",
                  )}
                >
                  {i.trend}
                </span>
              </div>
            ))}
          </div>
        </div>
      </section>

      <div className="mt-16 flex items-center gap-2 text-xs text-muted-foreground">
        <Sparkles className="h-3.5 w-3.5 text-primary" />
        FinSarthi gives educational information, not personal financial advice.
      </div>
    </div>
  );
}
