import { createFileRoute } from "@tanstack/react-router";
import { useMemo, useState } from "react";
import { Search } from "lucide-react";
import { Input } from "@/components/ui/input";
import { knowledgeTopics } from "@/lib/mock-data";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/app/knowledge")({
  component: KnowledgePage,
});

const categories = ["All", "Scheme", "Investing", "Credit", "Insurance", "Tax", "Loans", "Safety"];

function KnowledgePage() {
  const [q, setQ] = useState("");
  const [cat, setCat] = useState<string>("All");

  const filtered = useMemo(() => {
    return knowledgeTopics.filter((t) => {
      const okCat = cat === "All" || t.tag === cat;
      const okQ = !q || (t.title + t.desc).toLowerCase().includes(q.toLowerCase());
      return okCat && okQ;
    });
  }, [q, cat]);

  return (
    <div className="mx-auto w-full max-w-6xl px-4 py-8 sm:px-6 sm:py-10 lg:px-8">
      <div className="max-w-2xl">
        <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">Knowledge Hub</h1>
        <p className="mt-2 text-muted-foreground">
          Schemes, guides, and how-tos — simple explanations, no jargon.
        </p>
      </div>

      <div className="mt-6 flex flex-col gap-4 md:flex-row md:items-center">
        <div className="relative flex-1">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Search PM Kisan, SIP, credit score…"
            className="h-11 pl-9"
          />
        </div>
      </div>

      <div className="mt-4 flex flex-wrap gap-2">
        {categories.map((c) => (
          <button
            key={c}
            onClick={() => setCat(c)}
            className={cn(
              "rounded-full border px-3 py-1.5 text-xs transition-colors",
              cat === c
                ? "border-primary bg-primary-soft text-primary"
                : "border-border bg-card text-muted-foreground hover:border-primary/40 hover:text-foreground",
            )}
          >
            {c}
          </button>
        ))}
      </div>

      {filtered.length > 0 ? (
        <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {filtered.map((t) => (
            <article
              key={t.title}
              className="card-soft group flex h-full flex-col p-5 transition-all hover:-translate-y-0.5 hover:shadow-elevated"
            >
              <span className="w-fit rounded-full bg-primary-soft px-2 py-0.5 text-xs font-medium text-primary">
                {t.tag}
              </span>
              <h3 className="mt-3 text-base font-semibold">{t.title}</h3>
              <p className="mt-1 flex-1 text-sm text-muted-foreground">{t.desc}</p>
              <button className="mt-4 w-fit text-sm font-medium text-primary hover:underline">
                Read more →
              </button>
            </article>
          ))}
        </div>
      ) : (
        <div className="card-soft mt-10 flex flex-col items-center p-12 text-center">
          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-primary-soft text-primary">
            <Search className="h-5 w-5" />
          </div>
          <p className="mt-4 font-semibold">No results</p>
          <p className="mt-1 text-sm text-muted-foreground">Try different words or clear the filter.</p>
        </div>
      )}
    </div>
  );
}
