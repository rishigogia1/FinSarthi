import { Link } from "@tanstack/react-router";
import { cn } from "@/lib/utils";

export function Logo({ className, showWord = true }: { className?: string; showWord?: boolean }) {
  return (
    <Link
      to="/"
      className={cn("inline-flex items-center gap-2 font-semibold tracking-tight", className)}
      aria-label="FinSarthi home"
    >
      <span className="relative inline-flex h-8 w-8 items-center justify-center overflow-hidden rounded-lg">
        <img
          src="/finsarthi-logo.svg"
          alt=""
          aria-hidden
          className="h-full w-full object-contain"
        />
      </span>
      {showWord && <span className="text-base">FinSarthi</span>}
    </Link>
  );
}

