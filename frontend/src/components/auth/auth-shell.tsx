import { Link } from "@tanstack/react-router";
import { Logo } from "@/components/logo";
import type { ReactNode } from "react";

export function AuthShell({
  title,
  subtitle,
  children,
  footer,
}: {
  title: string;
  subtitle: string;
  children: ReactNode;
  footer?: ReactNode;
}) {
  return (
    <div className="min-h-dvh bg-background">
      <div className="mx-auto grid min-h-dvh w-full max-w-7xl grid-cols-1 lg:grid-cols-2">
        <div className="hidden lg:flex flex-col justify-between bg-gradient-to-br from-primary to-[oklch(0.45_0.22_285)] p-12 text-primary-foreground">
          <Logo className="text-primary-foreground [&>span:last-child]:text-primary-foreground" />
          <div>
            <p className="text-3xl font-semibold leading-snug">
              “Money is quiet again. My AI team keeps things on track.”
            </p>
            <p className="mt-4 text-sm text-primary-foreground/70">— Ananya, FinSarthi user</p>
          </div>
          <div className="text-xs text-primary-foreground/60">© 2026 FinSarthi</div>
        </div>
        <div className="flex flex-col p-6 sm:p-10">
          <div className="lg:hidden">
            <Logo />
          </div>
          <div className="mx-auto flex w-full max-w-md flex-1 flex-col justify-center">
            <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">{title}</h1>
            <p className="mt-2 text-sm text-muted-foreground">{subtitle}</p>
            <div className="mt-8">{children}</div>
            {footer && <div className="mt-6 text-center text-sm text-muted-foreground">{footer}</div>}
          </div>
          <div className="mt-6 text-xs text-muted-foreground">
            <Link to="/" className="hover:text-foreground">← Back to home</Link>
          </div>
        </div>
      </div>
    </div>
  );
}
