import { createFileRoute } from "@tanstack/react-router";
import { insights as mockInsights, spendingByCategory as mockSpending, savingsTrend as mockSavings, currency } from "@/lib/mock-data";
import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
} from "@/components/ui/chart";
import {
  Area,
  AreaChart,
  CartesianGrid,
  XAxis,
  YAxis,
  Cell,
  Pie,
  PieChart,
} from "recharts";
import { TrendingUp, TrendingDown, Sparkles } from "lucide-react";
import { cn } from "@/lib/utils";
import { useEffect, useState } from "react";
import { api } from "@/lib/api-client";

export const Route = createFileRoute("/app/insights")({
  component: InsightsPage,
});

const pieColors = [
  "var(--color-chart-1)",
  "var(--color-chart-2)",
  "var(--color-chart-3)",
  "var(--color-chart-4)",
  "var(--color-chart-5)",
  "var(--color-primary-soft)",
];

function InsightsPage() {
  const [loading, setLoading] = useState(true);
  const [overview, setOverview] = useState<any>(null);
  const [spendingTrends, setSpendingTrends] = useState<any[]>([]);
  const [monthlyTrends, setMonthlyTrends] = useState<any[]>([]);
  const [recommendations, setRecommendations] = useState<any[]>([]);

  useEffect(() => {
    const loadData = async () => {
      try {
        const [overviewData, trendsData, monthlyData, recsData] = await Promise.all([
          api.getInsightsOverview(),
          api.getSpendingTrends().catch(() => ({ trends: [] })),
          api.getIncomeExpenseTrends().catch(() => []),
          api.getRecommendations().catch(() => ({ recommendations: [] })),
        ]);

        setOverview(overviewData);
        setSpendingTrends(trendsData?.trends || []);
        setMonthlyTrends(monthlyData || []);
        setRecommendations(recsData?.recommendations || []);
      } catch (err) {
        // Fallback gracefully to mock data where required
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, []);

  const stats = overview ? [
    { title: "Savings Rate", value: `${Math.round(overview.savings_rate)}%`, trend: "Dynamic", tone: "success" },
    { title: "Monthly Savings", value: currency(overview.net_savings), trend: "Net this month", tone: "success" },
    { title: "Monthly Spending", value: currency(overview.total_expenses), trend: "Expenses", tone: "primary" },
    { title: "Total Income", value: currency(overview.total_income), trend: "Income", tone: "success" },
  ] : mockInsights;

  const pieData = spendingTrends.length > 0 
    ? spendingTrends.map(t => ({ name: t.category, value: t.total_amount }))
    : mockSpending;

  const areaData = monthlyTrends.length > 0
    ? monthlyTrends.map(pt => ({ m: pt.month, saved: pt.net }))
    : mockSavings;

  const recList = recommendations.length > 0
    ? recommendations.map(r => ({ t: r.title, s: r.description }))
    : [
        { t: "Move ₹2,100 to a liquid fund on payday", s: "Auto-sweep · Coach" },
        { t: "Cancel duplicate OTT — keep one", s: "Planner" },
        { t: "Increase emergency fund by ₹8k this quarter", s: "Planner + Guardian" },
      ];

  if (loading) {
    return (
      <div className="flex h-[calc(100dvh-4rem)] items-center justify-center bg-background">
        <span className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
      </div>
    );
  }

  return (
    <div className="mx-auto w-full max-w-6xl px-4 py-8 sm:px-6 sm:py-10 lg:px-8">
      <div className="max-w-2xl">
        <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">Insights</h1>
        <p className="mt-2 text-muted-foreground">
          A calm view of your financial health this month.
        </p>
      </div>

      {/* Stat cards */}
      <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {stats.map((s) => (
          <div key={s.title} className="card-soft p-5">
            <p className="text-xs text-muted-foreground">{s.title}</p>
            <p className="mt-1 text-2xl font-semibold">{s.value}</p>
            <div className="mt-2 flex items-center gap-1 text-xs">
              {s.trend.startsWith("-") ? (
                <TrendingDown className="h-3.5 w-3.5 text-primary" />
              ) : (
                <TrendingUp className="h-3.5 w-3.5 text-success" />
              )}
              <span
                className={cn(
                  s.tone === "success" && "text-success",
                  s.tone === "primary" && "text-primary",
                  s.tone === "warning" && "text-warning-foreground",
                )}
              >
                {s.trend}
              </span>
            </div>
          </div>
        ))}
      </div>

      {/* Charts */}
      <div className="mt-6 grid gap-6 lg:grid-cols-3">
        <div className="card-soft p-6 lg:col-span-2">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-semibold">Savings trend</p>
              <p className="text-xs text-muted-foreground">Chronological monthly net cashflow</p>
            </div>
            <span className="rounded-full bg-success/10 px-2 py-0.5 text-xs text-success">
              Live
            </span>
          </div>
          <ChartContainer
            className="mt-6 h-72 w-full"
            config={{ saved: { label: "Saved", color: "var(--color-primary)" } }}
          >
            <AreaChart data={areaData}>
              <defs>
                <linearGradient id="savedFill" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="var(--color-saved)" stopOpacity={0.35} />
                  <stop offset="100%" stopColor="var(--color-saved)" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid vertical={false} strokeDasharray="3 3" />
              <XAxis dataKey="m" tickLine={false} axisLine={false} />
              <YAxis tickLine={false} axisLine={false} width={45} tickFormatter={(v) => `${v / 1000}k`} />
              <ChartTooltip content={<ChartTooltipContent formatter={(v) => currency(Number(v))} />} />
              <Area
                type="monotone"
                dataKey="saved"
                stroke="var(--color-saved)"
                strokeWidth={2}
                fill="url(#savedFill)"
              />
            </AreaChart>
          </ChartContainer>
        </div>

        <div className="card-soft p-6">
          <p className="text-sm font-semibold">Spending by category</p>
          <p className="text-xs text-muted-foreground">This month</p>
          <ChartContainer
            className="mt-4 h-52 w-full"
            config={{ value: { label: "Amount" } }}
          >
            <PieChart>
              <ChartTooltip content={<ChartTooltipContent nameKey="name" formatter={(v) => currency(Number(v))} />} />
              <Pie data={pieData} dataKey="value" nameKey="name" innerRadius={48} outerRadius={80} paddingAngle={2}>
                {pieData.map((_, i) => (
                  <Cell key={i} fill={pieColors[i % pieColors.length]} />
                ))}
              </Pie>
            </PieChart>
          </ChartContainer>
          <ul className="mt-3 space-y-1.5 max-h-40 overflow-y-auto">
            {pieData.map((c, i) => (
              <li key={c.name} className="flex items-center justify-between text-xs">
                <span className="flex items-center gap-2">
                  <span className="h-2 w-2 rounded-sm" style={{ background: pieColors[i % pieColors.length] }} />
                  <span className="text-muted-foreground">{c.name}</span>
                </span>
                <span className="font-medium">{currency(c.value)}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>

      {/* AI Recommendations */}
      <div className="mt-6 card-soft p-6">
        <div className="flex items-center gap-2">
          <Sparkles className="h-4 w-4 text-primary" />
          <p className="text-sm font-semibold">AI recommendations</p>
        </div>
        <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {recList.map((r) => (
            <div key={r.t} className="rounded-xl border border-border bg-secondary/30 p-4">
              <p className="text-sm font-medium">{r.t}</p>
              <p className="mt-1 text-xs text-muted-foreground">{r.s}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
