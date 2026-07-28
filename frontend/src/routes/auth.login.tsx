import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { AuthShell } from "@/components/auth/auth-shell";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { api } from "@/lib/api-client";
import { toast } from "sonner";
import { useState } from "react";

export const Route = createFileRoute("/auth/login")({
  component: LoginPage,
  head: () => ({ meta: [{ title: "Log in — FinSarthi" }] }),
});

import { useAuth } from "@/context/auth-context";

function LoginPage() {
  const navigate = useNavigate();
  const { login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await login({ email, password });
      toast.success("Welcome back!");
      const redirectUrl = sessionStorage.getItem("auth_redirect");
      if (redirectUrl) {
        sessionStorage.removeItem("auth_redirect");
        window.location.href = redirectUrl;
      } else {
        navigate({ to: "/app" });
      }
    } catch (err: any) {
      toast.error(err.message || "Failed to log in");
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthShell
      title="Welcome back"
      subtitle="Log in to your FinSarthi workspace."
      footer={
        <>
          New here?{" "}
          <Link to="/auth/signup" className="font-medium text-primary hover:underline">
            Create an account
          </Link>
        </>
      }
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-2 gap-3">
          <Button type="button" variant="outline" className="h-11">Continue with Google</Button>
          <Button type="button" variant="outline" className="h-11">Continue with Apple</Button>
        </div>
        <div className="relative">
          <Separator />
          <span className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 bg-background px-2 text-xs text-muted-foreground">
            or with email
          </span>
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
          <div className="flex items-center justify-between">
            <Label htmlFor="password">Password</Label>
            <Link to="/auth/forgot" className="text-xs text-primary hover:underline">
              Forgot?
            </Link>
          </div>
          <Input
            id="password"
            type="password"
            required
            className="h-11"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </div>
        <Button type="submit" className="h-11 w-full" disabled={loading}>
          {loading ? "Logging in..." : "Log in"}
        </Button>
      </form>
    </AuthShell>
  );
}

