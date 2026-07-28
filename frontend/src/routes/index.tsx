import { createFileRoute, Link } from "@tanstack/react-router";
import { motion } from "framer-motion";
import {
  ArrowRight,
  Sparkles,
  ShieldCheck,
  Target,
  BookOpen,
  TrendingUp,
  Landmark,
  MessagesSquare,
  Accessibility,
  Languages,
  Ear,
  Type,
  CheckCircle2,
} from "lucide-react";

import { LandingNav } from "@/components/landing/nav";
import { LandingFooter } from "@/components/landing/footer";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { agents, currency } from "@/lib/mock-data";

export const Route = createFileRoute("/")({
  component: Landing,
});

function Landing() {
  return (
    <div className="min-h-dvh bg-background text-foreground">
      <LandingNav />
      <Hero />
      <TrustedBy />
      <Features />
      <HowItWorks />
      <AgentsSection />
      <AccessibilitySection />
      <Testimonials />
      <CTA />
      <LandingFooter />
    </div>
  );
}

function Hero() {
  return (
    <section className="relative overflow-hidden">
      <div
        aria-hidden
        className="pointer-events-none absolute inset-x-0 top-0 h-[520px] bg-grid-soft [mask-image:radial-gradient(60%_50%_at_50%_0%,black,transparent)]"
      />
      <div
        aria-hidden
        className="pointer-events-none absolute left-1/2 top-24 -z-0 h-[400px] w-[900px] -translate-x-1/2 rounded-full bg-primary/10 blur-3xl"
      />
      <div className="relative mx-auto grid w-full max-w-7xl gap-12 px-4 pb-16 pt-16 sm:px-6 lg:grid-cols-12 lg:gap-8 lg:px-8 lg:pb-24 lg:pt-24">
        <div className="lg:col-span-7">
          <Badge variant="secondary" className="rounded-full border border-border bg-card px-3 py-1 text-xs font-medium">
            <span className="mr-2 inline-block h-1.5 w-1.5 rounded-full bg-success" />
            New · AI Team now works together
          </Badge>
          <motion.h1
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="mt-5 text-4xl font-semibold tracking-tight text-foreground sm:text-5xl lg:text-6xl"
          >
            Know Your Money.
            <br />
            <span className="text-primary">Plan With AI.</span>
          </motion.h1>
          <p className="mt-5 max-w-xl text-base text-muted-foreground sm:text-lg">
            FinSarthi is a calm AI workspace where a team of agents helps you save more, plan goals,
            find government schemes, and stay safe from fraud — in plain language.
          </p>
          <div className="mt-8 flex flex-wrap items-center gap-3">
            <Button asChild size="lg" className="h-12 rounded-xl px-6">
              <Link to="/auth/signup">
                Start Free <ArrowRight className="ml-2 h-4 w-4" />
              </Link>
            </Button>
            <Button asChild variant="outline" size="lg" className="h-12 rounded-xl px-6">
              <Link to="/app">Explore Workspace</Link>
            </Button>
          </div>
          <div className="mt-6 flex flex-wrap items-center gap-x-6 gap-y-2 text-sm text-muted-foreground">
            {[
              "Free to start",
              "No card required",
              "Private by design",
            ].map((t) => (
              <span key={t} className="inline-flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-success" /> {t}
              </span>
            ))}
          </div>
        </div>

        <div className="relative lg:col-span-5">
          <HeroCards />
        </div>
      </div>
    </section>
  );
}

function HeroCards() {
  return (
    <div className="relative mx-auto h-[420px] w-full max-w-md">
      <motion.div
        className="card-soft absolute left-0 top-4 w-72 p-5"
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
      >
        <div className="flex items-center justify-between">
          <p className="text-xs font-medium text-muted-foreground">Financial Health</p>
          <TrendingUp className="h-4 w-4 text-success" />
        </div>
        <p className="mt-2 text-3xl font-semibold">78<span className="text-base text-muted-foreground">/100</span></p>
        <div className="mt-3 h-2 w-full rounded-full bg-secondary">
          <div className="h-2 rounded-full bg-primary" style={{ width: "78%" }} />
        </div>
        <p className="mt-2 text-xs text-success">+4 this month</p>
      </motion.div>

      <motion.div
        className="card-soft absolute right-0 top-28 w-72 p-5 animate-float"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.25 }}
      >
        <div className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary-soft text-primary">
            <Sparkles className="h-4 w-4" />
          </div>
          <p className="text-sm font-medium">Planner</p>
          <span className="ml-auto inline-flex items-center gap-1 text-xs text-muted-foreground">
            <span className="h-1.5 w-1.5 animate-pulse-dot rounded-full bg-primary" /> Working
          </span>
        </div>
        <p className="mt-3 text-sm text-muted-foreground">
          Draft budget ready. Essentials 55%, savings 25%, wants 20%.
        </p>
      </motion.div>

      <motion.div
        className="card-soft absolute left-6 bottom-4 w-80 p-5"
        initial={{ opacity: 0, y: 24 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
      >
        <p className="text-xs font-medium text-muted-foreground">This month you could save</p>
        <p className="mt-1 text-2xl font-semibold text-foreground">{currency(5000)} more</p>
        <div className="mt-3 grid grid-cols-3 gap-2 text-center text-xs">
          {[
            { l: "Subscriptions", v: "₹1,100" },
            { l: "Food orders", v: "₹1,800" },
            { l: "Auto-sweep", v: "₹2,100" },
          ].map((x) => (
            <div key={x.l} className="rounded-lg bg-secondary px-2 py-2">
              <p className="font-semibold text-foreground">{x.v}</p>
              <p className="mt-0.5 text-muted-foreground">{x.l}</p>
            </div>
          ))}
        </div>
      </motion.div>
    </div>
  );
}

function TrustedBy() {
  const items = ["Notion", "Perplexity", "Linear", "Vercel", "Ramp", "Loom"];
  return (
    <section className="border-y border-border bg-card/50">
      <div className="mx-auto flex w-full max-w-7xl flex-wrap items-center justify-between gap-6 px-4 py-8 sm:px-6 lg:px-8">
        <p className="text-xs uppercase tracking-widest text-muted-foreground">
          Loved by people who love good software
        </p>
        <div className="flex flex-wrap items-center gap-x-8 gap-y-3 opacity-70">
          {items.map((i) => (
            <span key={i} className="text-sm font-semibold text-muted-foreground">{i}</span>
          ))}
        </div>
      </div>
    </section>
  );
}

const features = [
  { icon: MessagesSquare, title: "One place to think about money", desc: "Chat, plan, and organize — like Notion for your finances." },
  { icon: Sparkles, title: "A team of AI agents", desc: "Planner, Coach, Guardian, Navigator, Learn — working together for you." },
  { icon: ShieldCheck, title: "Fraud & scam protection", desc: "Guardian checks suspicious links, UPI requests, and messages." },
  { icon: Landmark, title: "Government schemes, found for you", desc: "Navigator matches you to schemes you actually qualify for." },
  { icon: Target, title: "Goals that stick", desc: "Realistic plans with progress you can feel." },
  { icon: BookOpen, title: "Learn without jargon", desc: "Simple explanations, in your language, at your pace." },
];

function Features() {
  return (
    <section id="features" className="mx-auto w-full max-w-7xl px-4 py-20 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-2xl text-center">
        <p className="text-sm font-medium text-primary">Why FinSarthi</p>
        <h2 className="mt-2 text-3xl font-semibold tracking-tight sm:text-4xl">
          Everything you need. Nothing you don't.
        </h2>
        <p className="mt-3 text-muted-foreground">
          A workspace designed for real people making real financial decisions.
        </p>
      </div>
      <div className="mt-14 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
        {features.map((f, i) => (
          <motion.div
            key={f.title}
            initial={{ opacity: 0, y: 12 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: i * 0.05 }}
            className="card-soft p-6"
          >
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary-soft text-primary">
              <f.icon className="h-5 w-5" />
            </div>
            <h3 className="mt-4 text-base font-semibold">{f.title}</h3>
            <p className="mt-1.5 text-sm text-muted-foreground">{f.desc}</p>
          </motion.div>
        ))}
      </div>
    </section>
  );
}

function HowItWorks() {
  const steps = [
    { n: "01", title: "Tell FinSarthi what you want", desc: "Type or speak. \"Save more\", \"buy a car\", \"is this UPI safe?\"" },
    { n: "02", title: "Your AI team gets to work", desc: "Agents collaborate — planning, checking, teaching — in the background." },
    { n: "03", title: "You decide, calmly", desc: "Get clear next steps with sources and a plan that fits your life." },
  ];
  return (
    <section id="how" className="border-y border-border bg-card/40">
      <div className="mx-auto w-full max-w-7xl px-4 py-20 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-2xl text-center">
          <p className="text-sm font-medium text-primary">How it works</p>
          <h2 className="mt-2 text-3xl font-semibold tracking-tight sm:text-4xl">
            Three steps. That's it.
          </h2>
        </div>
        <div className="mt-14 grid gap-6 md:grid-cols-3">
          {steps.map((s) => (
            <div key={s.n} className="card-soft p-6">
              <p className="font-mono text-xs text-primary">{s.n}</p>
              <h3 className="mt-3 text-lg font-semibold">{s.title}</h3>
              <p className="mt-1.5 text-sm text-muted-foreground">{s.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function AgentsSection() {
  return (
    <section id="agents" className="mx-auto w-full max-w-7xl px-4 py-20 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-2xl text-center">
        <p className="text-sm font-medium text-primary">Your AI team</p>
        <h2 className="mt-2 text-3xl font-semibold tracking-tight sm:text-4xl">
          Five agents. One workspace.
        </h2>
        <p className="mt-3 text-muted-foreground">
          Each agent has a job. They talk to each other so you don't have to.
        </p>
      </div>
      <div className="mt-14 grid gap-5 sm:grid-cols-2 lg:grid-cols-5">
        {agents.map((a) => (
          <div key={a.id} className="card-soft flex flex-col p-5">
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary-soft font-semibold text-primary">
              {a.name[0]}
            </div>
            <p className="mt-4 text-base font-semibold">{a.name}</p>
            <p className="text-xs text-muted-foreground">{a.role}</p>
            <p className="mt-3 flex-1 text-sm text-muted-foreground">{a.desc}</p>
          </div>
        ))}
      </div>
    </section>
  );
}

function AccessibilitySection() {
  const items = [
    { icon: Type, title: "Large text mode" },
    { icon: Ear, title: "Screen reader friendly" },
    { icon: Accessibility, title: "High contrast" },
    { icon: Languages, title: "Multilingual" },
  ];
  return (
    <section id="accessibility" className="border-y border-border bg-card/40">
      <div className="mx-auto grid w-full max-w-7xl gap-10 px-4 py-20 sm:px-6 lg:grid-cols-2 lg:px-8">
        <div>
          <p className="text-sm font-medium text-primary">Built for everyone</p>
          <h2 className="mt-2 text-3xl font-semibold tracking-tight sm:text-4xl">
            Accessibility isn't a setting. It's the design.
          </h2>
          <p className="mt-3 max-w-lg text-muted-foreground">
            Students, professionals, small business owners, elderly users, users with low vision.
            FinSarthi is calm, keyboard-first, and speaks your language.
          </p>
        </div>
        <div className="grid grid-cols-2 gap-4">
          {items.map((i) => (
            <div key={i.title} className="card-soft flex items-center gap-3 p-5">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary-soft text-primary">
                <i.icon className="h-5 w-5" />
              </div>
              <p className="text-sm font-medium">{i.title}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function Testimonials() {
  const items = [
    {
      q: "I finally understand where my money goes. FinSarthi feels like a calm friend, not a bank app.",
      n: "Ananya",
      r: "Designer, Bengaluru",
    },
    {
      q: "The Guardian caught a phishing UPI request before I did. That alone paid for the year.",
      n: "Vikram",
      r: "Shop owner, Pune",
    },
    {
      q: "My father uses it in Hindi. Large text, simple answers. First fintech he actually likes.",
      n: "Priya",
      r: "PM, Delhi",
    },
  ];
  return (
    <section className="mx-auto w-full max-w-7xl px-4 py-20 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-2xl text-center">
        <p className="text-sm font-medium text-primary">People</p>
        <h2 className="mt-2 text-3xl font-semibold tracking-tight sm:text-4xl">
          Quiet software. Loud results.
        </h2>
      </div>
      <div className="mt-14 grid gap-5 md:grid-cols-3">
        {items.map((t) => (
          <figure key={t.n} className="card-soft flex h-full flex-col p-6">
            <blockquote className="flex-1 text-sm leading-relaxed text-foreground">
              “{t.q}”
            </blockquote>
            <figcaption className="mt-6 flex items-center gap-3">
              <div className="flex h-9 w-9 items-center justify-center rounded-full bg-primary-soft text-sm font-semibold text-primary">
                {t.n[0]}
              </div>
              <div>
                <p className="text-sm font-medium">{t.n}</p>
                <p className="text-xs text-muted-foreground">{t.r}</p>
              </div>
            </figcaption>
          </figure>
        ))}
      </div>
    </section>
  );
}

function CTA() {
  return (
    <section className="mx-auto w-full max-w-7xl px-4 pb-20 sm:px-6 lg:px-8">
      <div className="relative overflow-hidden rounded-3xl border border-border bg-gradient-to-br from-primary to-[oklch(0.45_0.22_285)] p-10 text-primary-foreground sm:p-14">
        <div className="relative z-10 max-w-2xl">
          <h2 className="text-3xl font-semibold tracking-tight sm:text-4xl">
            Your money deserves a calmer place.
          </h2>
          <p className="mt-3 max-w-lg text-primary-foreground/80">
            Start free in less than a minute. No card. No noise.
          </p>
          <div className="mt-6 flex flex-wrap gap-3">
            <Button asChild size="lg" variant="secondary" className="h-12 rounded-xl px-6">
              <Link to="/auth/signup">
                Start Free <ArrowRight className="ml-2 h-4 w-4" />
              </Link>
            </Button>
            <Button
              asChild
              size="lg"
              variant="outline"
              className="h-12 rounded-xl border-white/30 bg-white/10 px-6 text-primary-foreground hover:bg-white/20 hover:text-primary-foreground"
            >
              <Link to="/app">Explore Workspace</Link>
            </Button>
          </div>
        </div>
        <div
          aria-hidden
          className="pointer-events-none absolute -right-10 -top-10 h-72 w-72 rounded-full bg-white/10 blur-3xl"
        />
      </div>
    </section>
  );
}
