import { createFileRoute } from "@tanstack/react-router";
import { user } from "@/lib/mock-data";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Separator } from "@/components/ui/separator";
import { CreditCard, ShieldCheck, Bell, KeyRound } from "lucide-react";
import type { ComponentType } from "react";

export const Route = createFileRoute("/app/profile")({
  component: ProfilePage,
});

function ProfilePage() {
  return (
    <div className="mx-auto w-full max-w-4xl px-4 py-8 sm:px-6 sm:py-10 lg:px-8">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">Profile</h1>
        <p className="mt-2 text-muted-foreground">Manage your account, security and notifications.</p>
      </div>

      <div className="card-soft mt-8 p-6">
        <div className="flex flex-wrap items-center gap-4">
          <div className="flex h-16 w-16 items-center justify-center rounded-full bg-primary text-lg font-semibold text-primary-foreground">
            {user.initials}
          </div>
          <div>
            <p className="text-lg font-semibold">{user.fullName}</p>
            <p className="text-sm text-muted-foreground">{user.email}</p>
          </div>
          <Button variant="outline" className="ml-auto">Change photo</Button>
        </div>
        <Separator className="my-6" />
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-2">
            <Label htmlFor="name">Full name</Label>
            <Input id="name" defaultValue={user.fullName} />
          </div>
          <div className="space-y-2">
            <Label htmlFor="email">Email</Label>
            <Input id="email" type="email" defaultValue={user.email} />
          </div>
          <div className="space-y-2">
            <Label htmlFor="phone">Phone</Label>
            <Input id="phone" placeholder="+91 98xxx xxxxx" />
          </div>
          <div className="space-y-2">
            <Label htmlFor="lang">Preferred language</Label>
            <Input id="lang" defaultValue="English" />
          </div>
        </div>
        <div className="mt-6 flex justify-end">
          <Button>Save changes</Button>
        </div>
      </div>

      <div className="mt-6 grid gap-6 md:grid-cols-2">
        <SettingCard
          icon={ShieldCheck}
          title="Security"
          desc="Two-factor auth, active sessions."
          rows={[
            { label: "Two-factor authentication", desc: "Extra layer on login", enabled: true },
            { label: "Login alerts", desc: "Email me on new devices", enabled: true },
          ]}
        />
        <SettingCard
          icon={Bell}
          title="Notifications"
          desc="What we ping you about."
          rows={[
            { label: "Weekly insights", desc: "Every Monday morning", enabled: true },
            { label: "Fraud alerts", desc: "Guardian pings you", enabled: true },
            { label: "Goal reminders", desc: "Gentle nudges", enabled: false },
          ]}
        />
        <SettingCard
          icon={CreditCard}
          title="Connected accounts"
          desc="Read-only, whenever you're ready."
          rows={[
            { label: "HDFC Bank ••• 4421", desc: "Connected 2 months ago", enabled: true },
            { label: "SBI Savings ••• 8890", desc: "Connect", enabled: false },
          ]}
        />
        <SettingCard
          icon={KeyRound}
          title="Password"
          desc="Change your password anytime."
          rows={[{ label: "Change password", desc: "Last updated 3 months ago", enabled: false }]}
        />
      </div>
    </div>
  );
}

function SettingCard({
  icon: Icon,
  title,
  desc,
  rows,
}: {
  icon: ComponentType<{ className?: string }>;
  title: string;
  desc: string;
  rows: { label: string; desc: string; enabled: boolean }[];
}) {
  return (
    <div className="card-soft p-6">
      <div className="flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary-soft text-primary">
          <Icon className="h-5 w-5" />
        </div>
        <div>
          <p className="text-base font-semibold">{title}</p>
          <p className="text-xs text-muted-foreground">{desc}</p>
        </div>
      </div>
      <div className="mt-4 divide-y divide-border">
        {rows.map((r) => (
          <div key={r.label} className="flex items-center justify-between gap-4 py-3">
            <div>
              <p className="text-sm font-medium">{r.label}</p>
              <p className="text-xs text-muted-foreground">{r.desc}</p>
            </div>
            <Switch defaultChecked={r.enabled} />
          </div>
        ))}
      </div>
    </div>
  );
}
