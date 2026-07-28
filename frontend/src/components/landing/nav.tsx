import { Link } from "@tanstack/react-router";
import { Button } from "@/components/ui/button";
import { Logo } from "@/components/logo";
import { ArrowRight, Menu } from "lucide-react";
import { useState } from "react";
import { cn } from "@/lib/utils";

export function LandingNav() {
  const [open, setOpen] = useState(false);
  const links = [
    { to: "/#features", label: "Features" },
    { to: "/#how", label: "How it works" },
    { to: "/#agents", label: "AI Team" },
    { to: "/#accessibility", label: "Accessibility" },
  ];
  return (
    <header className="sticky top-0 z-40 border-b border-border/60 bg-background/80 backdrop-blur">
      <div className="mx-auto flex h-16 w-full max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        <Logo />
        <nav className="hidden items-center gap-8 md:flex">
          {links.map((l) => (
            <a
              key={l.to}
              href={l.to}
              className="text-sm text-muted-foreground transition-colors hover:text-foreground"
            >
              {l.label}
            </a>
          ))}
        </nav>
        <div className="hidden items-center gap-2 md:flex">
          <Button asChild variant="ghost">
            <Link to="/auth/login">Log in</Link>
          </Button>
          <Button asChild>
            <Link to="/auth/signup">
              Start free <ArrowRight className="ml-1 h-4 w-4" />
            </Link>
          </Button>
        </div>
        <button
          onClick={() => setOpen((o) => !o)}
          className="inline-flex h-10 w-10 items-center justify-center rounded-lg border border-border md:hidden"
          aria-label="Open menu"
          aria-expanded={open}
        >
          <Menu className="h-4 w-4" />
        </button>
      </div>
      <div className={cn("border-t border-border md:hidden", open ? "block" : "hidden")}>
        <div className="mx-auto flex max-w-7xl flex-col gap-1 px-4 py-3">
          {links.map((l) => (
            <a
              key={l.to}
              href={l.to}
              className="rounded-lg px-3 py-2 text-sm text-muted-foreground hover:bg-secondary"
              onClick={() => setOpen(false)}
            >
              {l.label}
            </a>
          ))}
          <div className="mt-2 flex gap-2">
            <Button asChild variant="outline" className="flex-1">
              <Link to="/auth/login">Log in</Link>
            </Button>
            <Button asChild className="flex-1">
              <Link to="/auth/signup">Start free</Link>
            </Button>
          </div>
        </div>
      </div>
    </header>
  );
}
