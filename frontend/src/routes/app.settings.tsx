import { createFileRoute } from "@tanstack/react-router";
import {
  Accessibility,
  Type,
  Contrast,
  Zap,
  Ear,
  Keyboard,
  Languages,
  Mic,
  Sparkles,
} from "lucide-react";
import { Switch } from "@/components/ui/switch";
import { Slider } from "@/components/ui/slider";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Label } from "@/components/ui/label";

export const Route = createFileRoute("/app/settings")({
  component: SettingsPage,
});

function SettingsPage() {
  return (
    <div className="mx-auto w-full max-w-4xl px-4 py-8 sm:px-6 sm:py-10 lg:px-8">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">Settings</h1>
        <p className="mt-2 text-muted-foreground">
          Accessibility is not an afterthought — it's the design. Tune FinSarthi to feel just right.
        </p>
      </div>

      <section className="card-soft mt-8 p-6">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary-soft text-primary">
            <Accessibility className="h-5 w-5" />
          </div>
          <div>
            <p className="text-base font-semibold">Accessibility</p>
            <p className="text-xs text-muted-foreground">Vision, motion, and interaction preferences</p>
          </div>
        </div>

        <div className="mt-6 space-y-1 divide-y divide-border">
          <Row icon={Contrast} title="High contrast mode" desc="Boost contrast for better readability">
            <Switch />
          </Row>
          <Row icon={Type} title="Large text" desc="Increase the base font size">
            <div className="flex items-center gap-3 sm:w-56">
              <Slider defaultValue={[16]} min={14} max={22} step={1} />
            </div>
          </Row>
          <Row icon={Zap} title="Reduced motion" desc="Fewer animations and transitions">
            <Switch />
          </Row>
          <Row icon={Keyboard} title="Keyboard navigation hints" desc="Show focus rings and shortcuts">
            <Switch defaultChecked />
          </Row>
          <Row icon={Ear} title="Screen reader optimizations" desc="Extra labels and landmarks">
            <Switch defaultChecked />
          </Row>
          <Row icon={Mic} title="Voice navigation" desc="Coming soon — control FinSarthi hands-free">
            <Switch disabled />
          </Row>
          <Row icon={Sparkles} title="Simple mode" desc="Hide advanced options and simplify language">
            <Switch />
          </Row>
        </div>
      </section>

      <section className="card-soft mt-6 p-6">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary-soft text-primary">
            <Languages className="h-5 w-5" />
          </div>
          <div>
            <p className="text-base font-semibold">Language & region</p>
            <p className="text-xs text-muted-foreground">FinSarthi speaks your language</p>
          </div>
        </div>

        <div className="mt-6 grid gap-4 sm:grid-cols-2">
          <div className="space-y-2">
            <Label>Language</Label>
            <Select defaultValue="en">
              <SelectTrigger><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="en">English</SelectItem>
                <SelectItem value="hi">हिन्दी (Hindi)</SelectItem>
                <SelectItem value="ta">தமிழ் (Tamil)</SelectItem>
                <SelectItem value="mr">मराठी (Marathi)</SelectItem>
                <SelectItem value="bn">বাংলা (Bengali)</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <Label>Currency</Label>
            <Select defaultValue="inr">
              <SelectTrigger><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="inr">₹ INR</SelectItem>
                <SelectItem value="usd">$ USD</SelectItem>
                <SelectItem value="eur">€ EUR</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
      </section>

      <section className="card-soft mt-6 p-6">
        <p className="text-base font-semibold">Theme</p>
        <p className="mt-1 text-xs text-muted-foreground">FinSarthi is designed light-first. Dark mode is available if you prefer.</p>
        <div className="mt-4 grid gap-3 sm:grid-cols-3">
          {[
            { id: "light", name: "Light", desc: "Default, calm" },
            { id: "system", name: "System", desc: "Match your device" },
            { id: "dark", name: "Dark", desc: "Low light" },
          ].map((t, i) => (
            <button
              key={t.id}
              className={
                "rounded-xl border p-4 text-left transition-colors " +
                (i === 0 ? "border-primary bg-primary-soft" : "border-border hover:border-primary/40")
              }
            >
              <p className="text-sm font-semibold">{t.name}</p>
              <p className="text-xs text-muted-foreground">{t.desc}</p>
            </button>
          ))}
        </div>
      </section>
    </div>
  );
}

function Row({
  icon: Icon,
  title,
  desc,
  children,
}: {
  icon: React.ComponentType<{ className?: string }>;
  title: string;
  desc: string;
  children: React.ReactNode;
}) {
  return (
    <div className="flex flex-wrap items-center justify-between gap-4 py-4">
      <div className="flex items-start gap-3">
        <div className="mt-0.5 flex h-8 w-8 items-center justify-center rounded-lg bg-secondary text-secondary-foreground">
          <Icon className="h-4 w-4" />
        </div>
        <div>
          <p className="text-sm font-medium">{title}</p>
          <p className="text-xs text-muted-foreground">{desc}</p>
        </div>
      </div>
      <div>{children}</div>
    </div>
  );
}
