import { createFileRoute, Link } from "@tanstack/react-router";
import { AuthShell } from "@/components/auth/auth-shell";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export const Route = createFileRoute("/auth/forgot")({
  component: ForgotPage,
  head: () => ({ meta: [{ title: "Reset password — FinSarthi" }] }),
});

function ForgotPage() {
  return (
    <AuthShell
      title="Reset your password"
      subtitle="We'll send a secure link to your email."
      footer={
        <>
          Remembered it?{" "}
          <Link to="/auth/login" className="font-medium text-primary hover:underline">
            Log in
          </Link>
        </>
      }
    >
      <form className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="email">Email</Label>
          <Input id="email" type="email" placeholder="you@example.com" required className="h-11" />
        </div>
        <Button type="submit" className="h-11 w-full">Send reset link</Button>
      </form>
    </AuthShell>
  );
}
