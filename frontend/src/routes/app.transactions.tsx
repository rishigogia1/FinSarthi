import { createFileRoute } from "@tanstack/react-router";
import { useState, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Search,
  Plus,
  Edit2,
  Trash2,
  Filter,
  ArrowUpDown,
  ChevronLeft,
  ChevronRight,
  TrendingDown,
  TrendingUp,
  Receipt,
  RotateCcw,
  Sparkles,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogDescription,
} from "@/components/ui/dialog";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { api } from "@/lib/api-client";
import { currency } from "@/lib/mock-data";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/app/transactions")({
  component: TransactionsPage,
});

const BUILTIN_CATEGORIES = [
  "Food",
  "Shopping",
  "Transport",
  "Bills",
  "Utilities",
  "Entertainment",
  "Healthcare",
  "Education",
  "Travel",
  "Salary",
  "Investment",
  "Other",
];

interface Transaction {
  id: string;
  type: "income" | "expense";
  amount: number;
  currency: string;
  category: string;
  occurred_on: string;
  note: string | null;
  source: string;
  created_at?: string;
  updated_at?: string;
}

function TransactionsPage() {
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(1);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters state
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState<string>("");
  const [type, setType] = useState<string>("");
  const [sortBy, setSortBy] = useState<string>("occurred_on");
  const [order, setOrder] = useState<"asc" | "desc">("desc");
  const [minAmount, setMinAmount] = useState<string>("");
  const [maxAmount, setMaxAmount] = useState<string>("");

  // Modal states
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [editTx, setEditTx] = useState<Transaction | null>(null);
  const [deleteTx, setDeleteTx] = useState<Transaction | null>(null);

  // Form inputs
  const [formData, setFormData] = useState({
    type: "expense" as "income" | "expense",
    amount: "",
    category: "Food",
    occurred_on: new Date().toISOString().split("T")[0],
    note: "",
  });

  const fetchTransactions = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.getTransactionsPaginated({
        page,
        page_size: 15,
        search: search || undefined,
        category: category || undefined,
        type: type || undefined,
        sort_by: sortBy,
        order,
        min_amount: minAmount ? parseFloat(minAmount) : undefined,
        max_amount: maxAmount ? parseFloat(maxAmount) : undefined,
      });
      setTransactions(res.items || []);
      setTotal(res.total || 0);
      setTotalPages(res.total_pages || 1);
    } catch (err: any) {
      setError(err?.message || "Failed to load transactions.");
    } finally {
      setLoading(false);
    }
  }, [page, search, category, type, sortBy, order, minAmount, maxAmount]);

  useEffect(() => {
    fetchTransactions();
  }, [fetchTransactions]);

  const handleOpenCreate = () => {
    setFormData({
      type: "expense",
      amount: "",
      category: "Food",
      occurred_on: new Date().toISOString().split("T")[0],
      note: "",
    });
    setIsCreateOpen(true);
  };

  const handleOpenEdit = (tx: Transaction) => {
    setEditTx(tx);
    setFormData({
      type: tx.type,
      amount: String(tx.amount),
      category: tx.category,
      occurred_on: tx.occurred_on,
      note: tx.note || "",
    });
  };

  const handleSaveTransaction = async () => {
    if (!formData.amount || parseFloat(formData.amount) <= 0) {
      alert("Please enter a valid amount greater than 0");
      return;
    }

    const payload = {
      type: formData.type,
      amount: parseFloat(formData.amount),
      category: formData.category,
      occurred_on: formData.occurred_on,
      note: formData.note ? formData.note.trim() : null,
    };

    if (editTx) {
      // Optimistic update
      const prev = [...transactions];
      setTransactions((list) =>
        list.map((t) => (t.id === editTx.id ? { ...t, ...payload } : t))
      );
      setEditTx(null);
      try {
        await api.updateTransaction(editTx.id, payload);
        fetchTransactions();
      } catch (err: any) {
        setTransactions(prev); // Rollback
        alert(err?.message || "Failed to update transaction");
      }
    } else {
      setIsCreateOpen(false);
      try {
        const newTx = await api.createTransaction(payload);
        // Clear active filters so user can see the new item clearly
        setSearch("");
        setCategory("");
        setType("");
        setMinAmount("");
        setMaxAmount("");
        setSortBy("occurred_on");
        setOrder("desc");
        setPage(1);

        // Prepend newTx immediately to transaction list
        setTransactions((list) => [newTx, ...list.filter((t) => t.id !== newTx.id)]);
        setTotal((t) => t + 1);
      } catch (err: any) {
        alert(err?.message || "Failed to create transaction");
      }
    }
  };

  const handleDeleteConfirm = async () => {
    if (!deleteTx) return;
    const targetId = deleteTx.id;
    setDeleteTx(null);

    // Optimistic remove
    const prev = [...transactions];
    setTransactions((list) => list.filter((t) => t.id !== targetId));
    setTotal((t) => Math.max(0, t - 1));

    try {
      await api.deleteTransaction(targetId);
      fetchTransactions();
    } catch (err: any) {
      setTransactions(prev); // Rollback
      alert(err?.message || "Failed to delete transaction");
    }
  };

  const clearFilters = () => {
    setSearch("");
    setCategory("");
    setType("");
    setSortBy("occurred_on");
    setOrder("desc");
    setMinAmount("");
    setMaxAmount("");
    setPage(1);
  };

  return (
    <div className="mx-auto w-full max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
      {/* Top Header */}
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between"
      >
        <div>
          <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">
            Transactions
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Manage your daily cashflow, filter records, and track real-time analytics.
          </p>
        </div>
        <Button onClick={handleOpenCreate} className="gap-2 rounded-xl">
          <Plus className="h-4 w-4" /> Add Transaction
        </Button>
      </motion.div>

      {/* Filter Toolbar */}
      <div className="mt-6 flex flex-col gap-3 rounded-2xl border border-border bg-card p-4 shadow-soft">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
          {/* Search bar */}
          <div className="relative flex-1">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search by note, category, or amount…"
              value={search}
              onChange={(e) => {
                setSearch(e.target.value);
                setPage(1);
              }}
              className="pl-9 bg-background"
            />
          </div>

          {/* Quick Filter Selects */}
          <div className="flex flex-wrap items-center gap-2">
            <select
              value={type}
              onChange={(e) => {
                setType(e.target.value);
                setPage(1);
              }}
              className="h-10 rounded-lg border border-input bg-background px-3 py-1 text-sm ring-offset-background focus:outline-none focus:ring-2 focus:ring-ring"
            >
              <option value="">All Types</option>
              <option value="expense">Expenses Only</option>
              <option value="income">Income Only</option>
            </select>

            <select
              value={category}
              onChange={(e) => {
                setCategory(e.target.value);
                setPage(1);
              }}
              className="h-10 rounded-lg border border-input bg-background px-3 py-1 text-sm ring-offset-background focus:outline-none focus:ring-2 focus:ring-ring"
            >
              <option value="">All Categories</option>
              {BUILTIN_CATEGORIES.map((cat) => (
                <option key={cat} value={cat}>
                  {cat}
                </option>
              ))}
            </select>

            <select
              value={`${sortBy}:${order}`}
              onChange={(e) => {
                const [sb, ord] = e.target.value.split(":");
                setSortBy(sb);
                setOrder(ord as "asc" | "desc");
                setPage(1);
              }}
              className="h-10 rounded-lg border border-input bg-background px-3 py-1 text-sm ring-offset-background focus:outline-none focus:ring-2 focus:ring-ring"
            >
              <option value="occurred_on:desc">Newest First</option>
              <option value="occurred_on:asc">Oldest First</option>
              <option value="amount:desc">Highest Amount</option>
              <option value="amount:asc">Lowest Amount</option>
              <option value="category:asc">Category A-Z</option>
            </select>

            {(search || category || type || minAmount || maxAmount || sortBy !== "occurred_on") && (
              <Button
                variant="ghost"
                size="sm"
                onClick={clearFilters}
                className="gap-1.5 text-xs text-muted-foreground hover:text-foreground"
              >
                <RotateCcw className="h-3.5 w-3.5" /> Clear
              </Button>
            )}
          </div>
        </div>

        {/* Min/Max Amount Row */}
        <div className="flex flex-wrap items-center gap-2 border-t border-border pt-3">
          <span className="text-xs text-muted-foreground">Amount Range:</span>
          <Input
            type="number"
            placeholder="Min ₹"
            value={minAmount}
            onChange={(e) => {
              setMinAmount(e.target.value);
              setPage(1);
            }}
            className="h-8 w-24 text-xs bg-background"
          />
          <span className="text-xs text-muted-foreground">to</span>
          <Input
            type="number"
            placeholder="Max ₹"
            value={maxAmount}
            onChange={(e) => {
              setMaxAmount(e.target.value);
              setPage(1);
            }}
            className="h-8 w-24 text-xs bg-background"
          />
        </div>
      </div>

      {/* Main List / Table Section */}
      <div className="mt-6">
        {loading ? (
          <div className="flex h-48 w-full items-center justify-center rounded-2xl border border-border bg-card">
            <div className="flex flex-col items-center gap-2">
              <span className="h-6 w-6 animate-spin rounded-full border-2 border-primary border-t-transparent" />
              <p className="text-xs text-muted-foreground">Loading transactions…</p>
            </div>
          </div>
        ) : error ? (
          <div className="rounded-2xl border border-destructive/20 bg-destructive/5 p-6 text-center text-destructive">
            <p className="text-sm font-medium">{error}</p>
            <Button variant="outline" size="sm" onClick={fetchTransactions} className="mt-3">
              Retry
            </Button>
          </div>
        ) : transactions.length === 0 ? (
          <div className="flex h-64 w-full flex-col items-center justify-center rounded-2xl border border-dashed border-border bg-card p-6 text-center">
            <div className="flex h-12 w-12 items-center justify-center rounded-full bg-primary-soft text-primary">
              <Receipt className="h-6 w-6" />
            </div>
            <h3 className="mt-3 font-semibold">No transactions found</h3>
            <p className="mt-1 text-sm text-muted-foreground">
              Try clearing your search filters or add a new transaction to start tracking.
            </p>
            <Button onClick={handleOpenCreate} size="sm" className="mt-4 gap-2">
              <Plus className="h-4 w-4" /> Add Transaction
            </Button>
          </div>
        ) : (
          <>
            {/* Desktop Table View */}
            <div className="hidden overflow-hidden rounded-2xl border border-border bg-card shadow-soft md:block">
              <table className="w-full text-left text-sm">
                <thead className="border-b border-border bg-muted/50 text-xs font-medium text-muted-foreground uppercase tracking-wider">
                  <tr>
                    <th className="px-6 py-3.5">Date</th>
                    <th className="px-6 py-3.5">Category</th>
                    <th className="px-6 py-3.5">Note & Source</th>
                    <th className="px-6 py-3.5 text-right">Amount</th>
                    <th className="px-6 py-3.5 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {transactions.map((tx) => (
                    <tr key={tx.id} className="transition-colors hover:bg-muted/30">
                      <td className="px-6 py-4 font-medium whitespace-nowrap">
                        {new Date(tx.occurred_on).toLocaleDateString("en-IN", {
                          day: "numeric",
                          month: "short",
                          year: "numeric",
                        })}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <Badge
                          variant="secondary"
                          className={cn(
                            "rounded-md font-medium",
                            tx.type === "income"
                              ? "bg-success/10 text-success"
                              : "bg-primary-soft text-primary"
                          )}
                        >
                          {tx.category}
                        </Badge>
                      </td>
                      <td className="px-6 py-4 max-w-xs truncate">
                        <p className="truncate font-medium">{tx.note || "No memo"}</p>
                        <span className="text-[10px] text-muted-foreground uppercase tracking-wider">
                          Source: {tx.source}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-right whitespace-nowrap font-semibold">
                        <span
                          className={cn(
                            "inline-flex items-center gap-1",
                            tx.type === "income" ? "text-success" : "text-foreground"
                          )}
                        >
                          {tx.type === "income" ? (
                            <TrendingUp className="h-3.5 w-3.5" />
                          ) : (
                            <TrendingDown className="h-3.5 w-3.5 text-muted-foreground" />
                          )}
                          {tx.type === "income" ? "+" : "-"}
                          {currency(tx.amount)}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-right whitespace-nowrap">
                        <div className="flex items-center justify-end gap-1">
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => handleOpenEdit(tx)}
                            title="Edit transaction"
                            className="h-8 w-8 text-muted-foreground hover:text-foreground"
                          >
                            <Edit2 className="h-3.5 w-3.5" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => setDeleteTx(tx)}
                            title="Delete transaction"
                            className="h-8 w-8 text-muted-foreground hover:text-destructive"
                          >
                            <Trash2 className="h-3.5 w-3.5" />
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Mobile Card View */}
            <div className="grid gap-3 md:hidden">
              {transactions.map((tx) => (
                <div
                  key={tx.id}
                  className="card-soft flex flex-col justify-between p-4 gap-3"
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <div className="flex items-center gap-2">
                        <Badge
                          variant="secondary"
                          className={cn(
                            "rounded-md text-xs font-medium",
                            tx.type === "income"
                              ? "bg-success/10 text-success"
                              : "bg-primary-soft text-primary"
                          )}
                        >
                          {tx.category}
                        </Badge>
                        <span className="text-xs text-muted-foreground">
                          {tx.occurred_on}
                        </span>
                      </div>
                      <p className="mt-1 font-medium text-sm">{tx.note || "No memo"}</p>
                    </div>
                    <span
                      className={cn(
                        "text-base font-semibold",
                        tx.type === "income" ? "text-success" : "text-foreground"
                      )}
                    >
                      {tx.type === "income" ? "+" : "-"}
                      {currency(tx.amount)}
                    </span>
                  </div>
                  <div className="flex items-center justify-between border-t border-border pt-2 text-xs text-muted-foreground">
                    <span>Source: {tx.source}</span>
                    <div className="flex gap-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleOpenEdit(tx)}
                        className="h-7 px-2 text-xs"
                      >
                        Edit
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setDeleteTx(tx)}
                        className="h-7 px-2 text-xs text-destructive"
                      >
                        Delete
                      </Button>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* Pagination Controls */}
            <div className="mt-6 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between border-t border-border pt-4 text-xs text-muted-foreground">
              <p>
                Showing Page <span className="font-semibold text-foreground">{page}</span> of{" "}
                <span className="font-semibold text-foreground">{totalPages}</span> ({total} total transactions)
              </p>
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  disabled={page <= 1}
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  className="gap-1 text-xs"
                >
                  <ChevronLeft className="h-3.5 w-3.5" /> Previous
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  disabled={page >= totalPages}
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  className="gap-1 text-xs"
                >
                  Next <ChevronRight className="h-3.5 w-3.5" />
                </Button>
              </div>
            </div>
          </>
        )}
      </div>

      {/* Create / Edit Modal Dialog */}
      <Dialog
        open={isCreateOpen || !!editTx}
        onOpenChange={(open) => {
          if (!open) {
            setIsCreateOpen(false);
            setEditTx(null);
          }
        }}
      >
        <DialogContent className="sm:max-w-md rounded-2xl">
          <DialogHeader>
            <DialogTitle>
              {editTx ? "Edit Transaction" : "Add New Transaction"}
            </DialogTitle>
            <DialogDescription>
              {editTx
                ? "Update your transaction details below."
                : "Record a new income or expense item."}
            </DialogDescription>
          </DialogHeader>

          <div className="grid gap-4 py-3">
            {/* Type selector tabs */}
            <div className="grid grid-cols-2 gap-2 rounded-xl bg-muted p-1 text-xs font-medium">
              <button
                type="button"
                onClick={() => setFormData((f) => ({ ...f, type: "expense" }))}
                className={cn(
                  "rounded-lg py-2 transition-all",
                  formData.type === "expense"
                    ? "bg-card text-foreground shadow-sm font-semibold"
                    : "text-muted-foreground hover:text-foreground"
                )}
              >
                Expense
              </button>
              <button
                type="button"
                onClick={() => setFormData((f) => ({ ...f, type: "income" }))}
                className={cn(
                  "rounded-lg py-2 transition-all",
                  formData.type === "income"
                    ? "bg-card text-success font-semibold shadow-sm"
                    : "text-muted-foreground hover:text-foreground"
                )}
              >
                Income
              </button>
            </div>

            {/* Amount */}
            <div>
              <label className="text-xs font-medium text-muted-foreground">Amount (₹)</label>
              <Input
                type="number"
                step="0.01"
                placeholder="e.g. 450"
                value={formData.amount}
                onChange={(e) => setFormData((f) => ({ ...f, amount: e.target.value }))}
                className="mt-1"
              />
            </div>

            {/* Category Dropdown */}
            <div>
              <label className="text-xs font-medium text-muted-foreground">Category</label>
              <select
                value={formData.category}
                onChange={(e) => setFormData((f) => ({ ...f, category: e.target.value }))}
                className="mt-1 w-full h-10 rounded-lg border border-input bg-background px-3 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
              >
                {BUILTIN_CATEGORIES.map((cat) => (
                  <option key={cat} value={cat}>
                    {cat}
                  </option>
                ))}
              </select>
            </div>

            {/* Date */}
            <div>
              <label className="text-xs font-medium text-muted-foreground">Occurred Date</label>
              <Input
                type="date"
                value={formData.occurred_on}
                onChange={(e) => setFormData((f) => ({ ...f, occurred_on: e.target.value }))}
                className="mt-1"
              />
            </div>

            {/* Note Memo */}
            <div>
              <label className="text-xs font-medium text-muted-foreground">Note / Memo (Optional)</label>
              <Input
                placeholder="e.g. Dinner with team"
                value={formData.note}
                onChange={(e) => setFormData((f) => ({ ...f, note: e.target.value }))}
                className="mt-1"
              />
            </div>
          </div>

          <DialogFooter className="gap-2 sm:gap-0">
            <Button
              variant="outline"
              onClick={() => {
                setIsCreateOpen(false);
                setEditTx(null);
              }}
            >
              Cancel
            </Button>
            <Button onClick={handleSaveTransaction}>
              {editTx ? "Save Changes" : "Create Transaction"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Alert Dialog */}
      <AlertDialog
        open={!!deleteTx}
        onOpenChange={(open) => {
          if (!open) setDeleteTx(null);
        }}
      >
        <AlertDialogContent className="rounded-2xl">
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Transaction?</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to remove this record (
              <span className="font-semibold text-foreground">
                {deleteTx ? currency(deleteTx.amount) : ""} - {deleteTx?.category}
              </span>
              )? This item will be soft-deleted and your analytics updated.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDeleteConfirm}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
