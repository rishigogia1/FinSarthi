import { createFileRoute } from "@tanstack/react-router";
import { Plus, Target, Trash2, Edit2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { currency } from "@/lib/mock-data";
import { useEffect, useState } from "react";
import { api } from "@/lib/api-client";
import { toast } from "sonner";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export const Route = createFileRoute("/app/goals")({
  component: GoalsPage,
});

function GoalsPage() {
  const [goalsList, setGoalsList] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [open, setOpen] = useState(false);
  const [editGoal, setEditGoal] = useState<any>(null);

  // Form states
  const [name, setName] = useState("");
  const [target, setTarget] = useState("");
  const [current, setCurrent] = useState("");
  const [deadline, setDeadline] = useState("");

  const fetchGoals = async () => {
    setLoading(true);
    try {
      const data = await api.getGoals();
      setGoalsList(data);
    } catch (err: any) {
      toast.error("Failed to load goals");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchGoals();
  }, []);

  const handleOpenCreate = () => {
    setEditGoal(null);
    setName("");
    setTarget("");
    setCurrent("0");
    setDeadline("");
    setOpen(true);
  };

  const handleOpenEdit = (goal: any) => {
    setEditGoal(goal);
    setName(goal.goal_name);
    setTarget(goal.target_amount.toString());
    setCurrent(goal.current_amount.toString());
    setDeadline(goal.deadline || "");
    setOpen(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const payload = {
      goal_name: name,
      target_amount: parseFloat(target),
      current_amount: parseFloat(current || "0"),
      deadline: deadline || null,
    };

    try {
      if (editGoal) {
        await api.updateGoal(editGoal.id, payload);
        toast.success("Goal updated successfully!");
      } else {
        await api.createGoal(payload);
        toast.success("Goal created successfully!");
      }
      setOpen(false);
      fetchGoals();
    } catch (err: any) {
      toast.error(err.message || "Failed to save goal");
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Are you sure you want to delete this goal?")) return;
    try {
      await api.deleteGoal(id);
      toast.success("Goal deleted successfully!");
      fetchGoals();
    } catch (err: any) {
      toast.error("Failed to delete goal");
    }
  };

  const handleAddFunds = async (goal: any) => {
    const amountStr = prompt(`Enter amount to add to "${goal.goal_name}":`);
    if (!amountStr) return;
    const amount = parseFloat(amountStr);
    if (isNaN(amount) || amount <= 0) {
      toast.error("Please enter a valid positive number");
      return;
    }

    try {
      await api.updateGoal(goal.id, {
        current_amount: goal.current_amount + amount,
      });
      toast.success("Funds added successfully!");
      fetchGoals();
    } catch (err: any) {
      toast.error("Failed to add funds");
    }
  };

  return (
    <div className="mx-auto w-full max-w-6xl px-4 py-8 sm:px-6 sm:py-10 lg:px-8">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">Goals</h1>
          <p className="mt-2 text-muted-foreground">Plan it, fund it, feel the progress.</p>
        </div>
        <Button className="gap-2" onClick={handleOpenCreate}>
          <Plus className="h-4 w-4" /> New goal
        </Button>
      </div>

      {loading ? (
        <div className="mt-12 flex justify-center">
          <span className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
        </div>
      ) : goalsList.length === 0 ? (
        <div className="mt-12 rounded-2xl border border-dashed border-border p-12 text-center">
          <Target className="mx-auto h-12 w-12 text-muted-foreground" />
          <h3 className="mt-4 text-lg font-semibold">No goals set yet</h3>
          <p className="mt-2 text-sm text-muted-foreground">Create a goal to start saving calmly with AI.</p>
          <Button className="mt-6" onClick={handleOpenCreate}>Create your first goal</Button>
        </div>
      ) : (
        <div className="mt-8 grid gap-5 md:grid-cols-2 xl:grid-cols-3">
          {goalsList.map((g) => {
            const pct = Math.min(100, Math.round((g.current_amount / g.target_amount) * 100));
            return (
              <article key={g.id} className="card-soft flex flex-col p-6">
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary-soft text-primary">
                    <Target className="h-5 w-5" />
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-base font-semibold">{g.goal_name}</p>
                    <p className="text-xs text-muted-foreground">
                      {g.deadline ? `Target: ${g.deadline}` : "No deadline"}
                    </p>
                  </div>
                  <div className="flex gap-1">
                    <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => handleOpenEdit(g)}>
                      <Edit2 className="h-3.5 w-3.5" />
                    </Button>
                    <Button variant="ghost" size="icon" className="h-8 w-8 text-destructive" onClick={() => handleDelete(g.id)}>
                      <Trash2 className="h-3.5 w-3.5" />
                    </Button>
                  </div>
                </div>
                <div className="mt-5">
                  <div className="flex items-baseline justify-between">
                    <p className="text-2xl font-semibold">{currency(g.current_amount)}</p>
                    <p className="text-sm text-muted-foreground">of {currency(g.target_amount)}</p>
                  </div>
                  <Progress value={pct} className="mt-3 h-2" />
                  <div className="mt-2 flex items-center justify-between text-xs">
                    <span className="text-muted-foreground">{pct}% funded</span>
                    <span className="rounded-full bg-success/10 px-2 py-0.5 text-success">
                      {g.status || "active"}
                    </span>
                  </div>
                </div>
                <div className="mt-5 border-t border-border pt-4 flex-1 flex flex-col justify-end">
                  <p className="text-xs font-medium text-muted-foreground">AI recommendation</p>
                  <p className="mt-1 text-sm">
                    {pct >= 100
                      ? "Congratulations! You have fully funded this goal."
                      : `Automate ${currency(Math.round((g.target_amount - g.current_amount) / 12))}/month to reach this goal in 12 months.`}
                  </p>
                </div>
                <div className="mt-4 flex gap-2">
                  <Button variant="outline" className="flex-1" onClick={() => handleAddFunds(g)} disabled={pct >= 100}>
                    Add funds
                  </Button>
                </div>
              </article>
            );
          })}
        </div>
      )}

      {/* Goal Dialog */}
      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent className="sm:max-w-[425px]">
          <DialogHeader>
            <DialogTitle>{editGoal ? "Edit goal" : "Create goal"}</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleSubmit} className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="goal_name">Goal name</Label>
              <Input
                id="goal_name"
                required
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g., Emergency Fund"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="target_amount">Target amount (INR)</Label>
              <Input
                id="target_amount"
                type="number"
                required
                value={target}
                onChange={(e) => setTarget(e.target.value)}
                placeholder="e.g., 50000"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="current_amount">Current savings (INR)</Label>
              <Input
                id="current_amount"
                type="number"
                value={current}
                onChange={(e) => setCurrent(e.target.value)}
                placeholder="e.g., 0"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="deadline">Target deadline</Label>
              <Input
                id="deadline"
                type="date"
                value={deadline}
                onChange={(e) => setDeadline(e.target.value)}
              />
            </div>
            <DialogFooter>
              <Button type="submit">{editGoal ? "Save changes" : "Create goal"}</Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
