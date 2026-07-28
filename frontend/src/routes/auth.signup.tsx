import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { AuthShell } from "@/components/auth/auth-shell";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { api } from "@/lib/api-client";
import { toast } from "sonner";
import { useState } from "react";

export const Route = createFileRoute("/auth/signup")({
  component: SignupPage,
  head: () => ({ meta: [{ title: "Create account — FinSarthi" }] }),
});

import { useAuth } from "@/context/auth-context";

function SignupPage() {
  const navigate = useNavigate();
  const { register } = useAuth();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await register({ name, email, password });
      toast.success("Account created successfully!");
      navigate({ to: "/app" });
    } catch (err: any) {
      toast.error(err.message || "Failed to create account");
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthShell
      title="Create your workspace"
      subtitle="A calmer place for your money. Free to start."
      footer={
        <>
          Already have an account?{" "}
          <Link to="/auth/login" className="font-medium text-primary hover:underline">
            Log in
          </Link>
        </>
      }
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-2 gap-3">
          <Button type="button" variant="outline" className="h-11">Google</Button>
          <Button type="button" variant="outline" className="h-11">Apple</Button>
        </div>
        <div className="relative">
          <Separator />
          <span className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 bg-background px-2 text-xs text-muted-foreground">
            or with email
          </span>
        </div>
        <div className="space-y-2">
          <Label htmlFor="name">Full name</Label>
          <Input
            id="name"
            placeholder="Rishi Sharma"
            required
            className="h-11"
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="email">Email</Label>
          <Input
            id="email"
            type="email"
            placeholder="you@example.com"
            required
            className="h-11"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="password">Password</Label>
          <Input
            id="password"
            type="password"
            required
            className="h-11"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
          <p className="text-xs text-muted-foreground">At least 8 characters.</p>
        </div>
        <Button type="submit" className="h-11 w-full" disabled={loading}>
          {loading ? "Creating..." : "Create account"}
        </Button>
        <p className="text-center text-xs text-muted-foreground">
          By continuing you agree to the Terms and Privacy Policy.
        </p>
      </form>
    </AuthShell>
  );
}

