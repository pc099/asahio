"use client";

import { useEffect, useRef } from "react";
import { UserButton } from "@clerk/nextjs";
import { useQuery } from "@tanstack/react-query";
import { Menu } from "lucide-react";
import { getAnalyticsOverview, getOrgUsage } from "@/lib/api";
import { cn, formatCurrency } from "@/lib/utils";
import { fireConfetti } from "@/lib/confetti";
import { toast } from "sonner";

interface DashboardHeaderProps {
  orgSlug: string;
  onMenuToggle?: () => void;
}

export function DashboardHeader({
  orgSlug,
  onMenuToggle,
}: DashboardHeaderProps) {
  const prevRequests = useRef<number | null>(null);
  const confettiFired = useRef(false);

  const { data: overview } = useQuery({
    queryKey: ["overview", orgSlug, "header"],
    queryFn: () => getAnalyticsOverview("30d", undefined, orgSlug),
    refetchInterval: 30_000,
  });

  const { data: usage } = useQuery({
    queryKey: ["usage", orgSlug, "header"],
    queryFn: () => getOrgUsage(orgSlug),
    refetchInterval: 60_000,
  });

  useEffect(() => {
    if (!overview || confettiFired.current) return;
    const total = overview.total_requests;
    if (prevRequests.current !== null && prevRequests.current === 0 && total > 0) {
      confettiFired.current = true;
      fireConfetti();
      toast.success("First request detected. ASAHIO is now tracking savings.");
    }
    prevRequests.current = total;
  }, [overview]);

  return (
    <header className="flex h-14 items-center justify-between border-b border-border bg-background px-6">
      <div className="flex items-center gap-4">
        {onMenuToggle && (
          <button
            type="button"
            aria-label="Open sidebar"
            className="flex h-8 w-8 items-center justify-center rounded-md border border-border bg-background text-muted-foreground hover:bg-muted md:hidden"
            onClick={onMenuToggle}
          >
            <Menu className="h-4 w-4" />
          </button>
        )}
        <h2 className="text-sm font-medium text-muted-foreground">{orgSlug}</h2>
        <span className="text-sm font-semibold text-asahio">
          {formatCurrency(overview?.total_savings_usd ?? 0)} saved in 30d
        </span>
        {usage && (
          <div className="hidden items-center gap-3 sm:flex">
            <UsagePill label="Req" pct={usage.requests_pct} />
            <UsagePill label="Tok" pct={usage.tokens_pct} />
          </div>
        )}
      </div>
      <div className="flex items-center gap-4">
        <kbd className="hidden items-center gap-0.5 rounded border border-border bg-muted px-1.5 py-0.5 text-[10px] font-medium text-muted-foreground sm:flex">
          <span className="text-xs">&#8984;</span>K
        </kbd>
        <UserButton afterSignOutUrl="/sign-in" />
      </div>
    </header>
  );
}

function UsagePill({ label, pct }: { label: string; pct: number }) {
  const barColor =
    pct >= 95 ? "bg-red-500" : pct >= 80 ? "bg-orange-500" : pct >= 60 ? "bg-yellow-500" : "bg-asahio";
  return (
    <div className="flex items-center gap-1.5">
      <span className="text-[10px] text-muted-foreground">{label}</span>
      <div className="h-1.5 w-12 overflow-hidden rounded-full bg-muted">
        <div
          className={cn("h-full rounded-full transition-all", barColor)}
          style={{ width: `${Math.min(100, pct)}%` }}
        />
      </div>
      <span className="text-[10px] tabular-nums text-muted-foreground">{pct.toFixed(0)}%</span>
    </div>
  );
}
