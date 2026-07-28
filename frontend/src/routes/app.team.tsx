import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { cn } from "@/lib/utils";
import { api } from "@/lib/api-client";
import { Loader2, CheckCircle2, Circle, XCircle } from "lucide-react";

export const Route = createFileRoute("/app/team")({
  component: TeamPage,
});

type AgentRequirement = {
  name: string;
  met: boolean;
};

type Agent = {
  id: string;
  name: string;
  role: string;
  description: string;
  implementation_status: "Available" | "Waiting" | "Planned" | "Coming Soon" | "Unavailable";
  current_phase: string;
  requirements: AgentRequirement[];
  activities: string[];
};

function TeamPage() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadDashboard() {
      try {
        const data = await api.getTeamDashboard();
        setAgents(data.agents);
      } catch (err: any) {
        setError(err.message || "Failed to load AI team dashboard");
      } finally {
        setLoading(false);
      }
    }
    loadDashboard();
  }, []);

  if (loading) {
    return (
      <div className="flex h-[50vh] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex h-[50vh] flex-col items-center justify-center">
        <p className="text-destructive">{error}</p>
      </div>
    );
  }

  const getColor = (id: string) => {
    switch (id) {
      case "planner": return "primary";
      case "coach": return "success";
      case "guardian": return "warning";
      case "navigator": return "chart-5";
      case "learn": return "accent";
      default: return "primary";
    }
  };

  const getStatusColor = (status: Agent["implementation_status"]) => {
    if (status === "Available") return "text-success";
    if (status === "Waiting") return "text-warning-foreground";
    return "text-muted-foreground";
  };

  return (
    <div className="mx-auto w-full max-w-6xl px-4 py-8 sm:px-6 sm:py-10 lg:px-8">
      <div className="max-w-2xl">
        <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">Your AI team</h1>
        <p className="mt-2 text-muted-foreground">
          Five specialized agents. See what's active today and what's coming next.
        </p>
      </div>

      <div className="mt-8 grid gap-5 md:grid-cols-2 xl:grid-cols-3">
        {agents.map((a) => {
          const color = getColor(a.id);
          const isAvailable = a.implementation_status === "Available";

          return (
            <article key={a.id} className="card-soft flex flex-col p-6">
              <div className="flex items-center gap-3">
                <div
                  className={cn(
                    "flex h-11 w-11 items-center justify-center rounded-full font-semibold",
                    color === "primary" && "bg-primary-soft text-primary",
                    color === "success" && "bg-success/10 text-success",
                    color === "warning" && "bg-warning/10 text-warning-foreground",
                    color === "accent" && "bg-accent text-accent-foreground",
                    color === "chart-5" && "bg-secondary text-secondary-foreground",
                    !isAvailable && "opacity-50 grayscale"
                  )}
                >
                  {a.name[0]}
                </div>
                <div>
                  <p className="text-base font-semibold">{a.name}</p>
                  <p className="text-xs text-muted-foreground">{a.role}</p>
                </div>
                {isAvailable && (
                  <span className="ml-auto inline-flex items-center gap-1.5 rounded-full bg-success/10 px-2 py-0.5 text-[10px] text-success">
                    <span className="h-1.5 w-1.5 animate-pulse-dot rounded-full bg-success" />
                    Ready
                  </span>
                )}
              </div>
              
              <p className="mt-4 text-sm text-muted-foreground">{a.description}</p>

              <div className="mt-5 rounded-md bg-secondary/50 p-3">
                <div className="flex items-center justify-between text-xs mb-2">
                  <span className="text-muted-foreground font-medium">Status</span>
                  <span className={cn("font-medium", getStatusColor(a.implementation_status))}>
                    {a.implementation_status}
                  </span>
                </div>
                <div className="flex items-center justify-between text-xs">
                  <span className="text-muted-foreground font-medium">Phase</span>
                  <span className="font-medium">{a.current_phase}</span>
                </div>
              </div>

              <div className="mt-5 border-t border-border pt-4 flex-1">
                {a.id === "coach" ? (
                  a.metrics?.status === "Learning" ? (
                    <div>
                      <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-2">Coach Learning Mode</p>
                      <p className="text-xs text-muted-foreground mb-3">
                        Collecting spending history to build your behavioral habit profile.
                      </p>
                      <div className="rounded-md bg-secondary/40 p-3">
                        <div className="flex justify-between items-center text-xs mb-1.5 font-medium">
                          <span>Data Progress</span>
                          <span className="text-primary font-semibold">{a.metrics?.txCount || 0} / {a.metrics?.requiredTx || 20} transactions</span>
                        </div>
                        <div className="h-2 w-full bg-secondary rounded-full overflow-hidden">
                          <div 
                            className="h-full bg-primary transition-all duration-300" 
                            style={{ width: `${Math.min(100, Number(a.metrics?.progressPercentage || 0))}%` }} 
                          />
                        </div>
                      </div>
                      {a.activities && a.activities.length > 0 && (
                        <p className="mt-3 text-xs italic text-muted-foreground bg-secondary/20 p-2 rounded">
                          "{a.activities[0]}"
                        </p>
                      )}
                    </div>
                  ) : (
                    <div>
                      <div className="flex items-center justify-between mb-3">
                        <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Coach Habit Analysis</p>
                        {a.metrics?.coachScore !== undefined && a.metrics?.coachScore !== null && (
                          <span className="inline-flex items-center gap-1 rounded-full bg-success/15 px-2.5 py-0.5 text-xs font-semibold text-success">
                            Score: {a.metrics.coachScore}/100 ({a.metrics.coachRating || 'Active'})
                          </span>
                        )}
                      </div>
                      <div className="grid grid-cols-2 gap-2 text-xs">
                        <div className="rounded-md bg-secondary/40 p-2.5">
                          <span className="text-muted-foreground block text-[11px]">Top Category</span>
                          <span className="font-semibold text-sm text-foreground truncate block">{a.metrics?.biggestHabit || 'None'}</span>
                        </div>
                        <div className="rounded-md bg-secondary/40 p-2.5">
                          <span className="text-muted-foreground block text-[11px]">Frequent Category</span>
                          <span className="font-semibold text-sm text-foreground truncate block">{a.metrics?.mostFrequentCategory || 'None'}</span>
                        </div>
                        <div className="rounded-md bg-secondary/40 p-2.5">
                          <span className="text-muted-foreground block text-[11px]">Avg Daily Spend</span>
                          <span className="font-semibold text-sm text-foreground">₹{Number(a.metrics?.avgDailySpend || 0).toLocaleString()}</span>
                        </div>
                        <div className="rounded-md bg-secondary/40 p-2.5">
                          <span className="text-muted-foreground block text-[11px]">Weekly Spend</span>
                          <span className="font-semibold text-sm text-foreground">₹{Number(a.metrics?.avgWeeklySpend || 0).toLocaleString()}</span>
                        </div>
                      </div>
                      {a.activities && a.activities.length > 0 && (
                        <p className="mt-3 text-xs text-foreground bg-secondary/30 p-2 rounded">
                          💡 {a.activities[0]}
                        </p>
                      )}
                    </div>
                  )
                ) : a.metrics && Object.keys(a.metrics).length > 0 ? (
                  <div>
                    <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-3">Planner Analytics Summary</p>
                    <div className="grid grid-cols-2 gap-2 text-xs">
                      <div className="rounded-md bg-secondary/40 p-2.5">
                        <span className="text-muted-foreground block text-[11px]">Monthly Spending</span>
                        <span className="font-semibold text-sm text-foreground">₹{Number(a.metrics.monthlyExpense || 0).toLocaleString()}</span>
                      </div>
                      <div className="rounded-md bg-secondary/40 p-2.5">
                        <span className="text-muted-foreground block text-[11px]">Monthly Income</span>
                        <span className="font-semibold text-sm text-success">₹{Number(a.metrics.monthlyIncome || 0).toLocaleString()}</span>
                      </div>
                      <div className="rounded-md bg-secondary/40 p-2.5">
                        <span className="text-muted-foreground block text-[11px]">Net Cashflow</span>
                        <span className={`font-semibold text-sm ${Number(a.metrics.netCashflow || 0) >= 0 ? 'text-success' : 'text-destructive'}`}>
                          ₹{Number(a.metrics.netCashflow || 0).toLocaleString()}
                        </span>
                      </div>
                      <div className="rounded-md bg-secondary/40 p-2.5">
                        <span className="text-muted-foreground block text-[11px]">Largest Category</span>
                        <span className="font-semibold text-sm text-foreground truncate block">{a.metrics.largestCategory || 'None'}</span>
                      </div>
                    </div>
                    <div className="mt-3 flex items-center justify-between text-xs text-muted-foreground">
                      <span>Transactions: <strong className="text-foreground">{a.metrics.totalTransactions || 0}</strong></span>
                      <span>Updated: <strong className="text-foreground">Just now</strong></span>
                    </div>
                  </div>
                ) : a.requirements && a.requirements.length > 0 ? (
                  <>
                    <p className="text-xs font-medium text-muted-foreground">Requirements</p>
                    <ul className="mt-3 space-y-2">
                      {a.requirements.map((req, i) => (
                        <li key={i} className="flex items-start gap-2 text-sm">
                          {req.met ? (
                            <CheckCircle2 className="mt-0.5 h-4 w-4 text-success shrink-0" />
                          ) : (
                            <XCircle className="mt-0.5 h-4 w-4 text-muted-foreground/50 shrink-0" />
                          )}
                          <span className={cn(req.met ? "text-foreground" : "text-muted-foreground")}>
                            {req.name}
                          </span>
                        </li>
                      ))}
                    </ul>
                  </>
                ) : isAvailable ? (
                  <>
                    <p className="text-xs font-medium text-muted-foreground">Try asking in Chat:</p>
                    <ul className="mt-3 space-y-2">
                      {a.activities.map((prompt, i) => (
                        <li key={i} className="flex gap-2 text-sm">
                          <Circle className="mt-1 h-3 w-3 text-primary shrink-0" />
                          <span className="text-foreground">{prompt}</span>
                        </li>
                      ))}
                    </ul>
                  </>
                ) : null}
              </div>
            </article>
          );
        })}
      </div>
    </div>
  );
}
