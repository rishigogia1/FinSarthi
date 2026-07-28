import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { AuthShell } from "@/components/auth/auth-shell";
import { Button } from "@/components/ui/button";
import { InputOTP, InputOTPGroup, InputOTPSlot } from "@/components/ui/input-otp";

export const Route = createFileRoute("/auth/otp")({
  component: OtpPage,
  head: () => ({ meta: [{ title: "Verify — FinSarthi" }] }),
});

function OtpPage() {
  const navigate = useNavigate();
  return (
    <AuthShell
      title="Enter verification code"
      subtitle="We sent a 6-digit code to your email."
      footer={
        <>
          Didn't get it?{" "}
          <Link to="#" className="font-medium text-primary hover:underline">
            Resend
          </Link>
        </>
      }
    >
      <form
        onSubmit={(e) => {
          e.preventDefault();
          navigate({ to: "/app" });
        }}
        className="space-y-6"
      >
        <div className="flex justify-center">
          <InputOTP maxLength={6}>
            <InputOTPGroup>
              {[0, 1, 2, 3, 4, 5].map((i) => (
                <InputOTPSlot key={i} index={i} />
              ))}
            </InputOTPGroup>
          </InputOTP>
        </div>
        <Button type="submit" className="h-11 w-full">Verify & continue</Button>
      </form>
    </AuthShell>
  );
}
