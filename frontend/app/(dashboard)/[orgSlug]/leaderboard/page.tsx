"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { getModelLeaderboard } from "@/lib/api";
import { cn, formatCurrency, formatPercent, formatNumber } from "@/lib/utils";
import {
  Activity,
  Trophy,
  ArrowUpDown,
  Clock,
  Database,
  DollarSign,
  TrendingUp,
  AlertTriangle,
} from "lucide-react";

const PERIODS = [
  { label: "7d", value: "7d" },
  { label: "30d", value: "30d" },
  { label: "90d", value: "90d" },
] as const;

const SORT_OPTIONS = [
  { label: "Requests", value: "request_count" },
  { label: "Latency", value: "avg_latency_ms" },
  { label: "Cache Hit %", value: "cache_hit_rate" },
  { label: "Cost", value: "total_cost_usd" },
  { label: "Savings %", value: "avg_savings_pct" },
  { label: "Hallucination", value: "hallucination_rate" },
] as const;

function RankBadge({ rank }: { rank: number }) {
  if (rank === 1) {
    return (
      <span className="inline-flex h-7 w-7 items-center justify-center rounded-full bg-yellow-500/20 text-sm font-bold text-yellow-400">
        1
      </span>
    );
  }
  if (rank === 2) {
    return (
      <span className="inline-flex h-7 w-7 items-center justify-center rounded-full bg-gray-400/20 text-sm font-bold text-gray-300">
        2
      </span>
    );
  }
  if (rank === 3) {
    return (
      <span className="inline-flex h-7 w-7 items-center justify-center rounded-full bg-amber-700/20 text-sm font-bold text-amber-600">
        3
      </span>
    );
  }
  return (
    <span className="inline-flex h-7 w-7 items-center justify-center text-sm font-medium text-muted-foreground">
      {rank}
    </span>
  );
}

function RateBadge({ rate, inverted = false }: { rate: number; inverted?: boolean }) {
  // inverted: lower is better (e.g., hallucination rate)
  const pct = rate * 100;
  let color: string;
  if (inverted) {
    color = pct <= 2 ? "text-emerald-400 bg-emerald-500/10" : pct <= 10 ? "text-yellow-400 bg-yellow-500/10" : "text-red-400 bg-red-500/10";
  } else {
    color = pct >= 50 ? "text-emerald-400 bg-emerald-500/10" : pct >= 20 ? "text-yellow-400 bg-yellow-500/10" : "text-red-400 bg-red-500/10";
  }
  return (
    <span className={cn("inline-flex rounded-full px-2 py-0.5 text-xs font-medium", color)}>
      {formatPercent(pct)}
    </span>
  );
}

export default function LeaderboardPage() {
  const params = useParams();
  const orgSlug = typeof params?.orgSlug === "string" ? params.orgSlug : "";
  const [period, setPeriod] = useState("30d");
  const [sortBy, setSortBy] = useState("request_count");

  const { data, isLoading, error } = useQuery({
    queryKey: ["leaderboard", orgSlug, period, sortBy],
    queryFn: () => getModelLeaderboard(period, sortBy, undefined, orgSlug),
    enabled: !!orgSlug,
  });

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Model Leaderboard</h1>
          <p className="text-sm text-muted-foreground">
            Compare model performance across requests, latency, cost, and quality.
          </p>
        </div>

        <div className="flex items-center gap-3">
          {/* Sort selector */}
          <div className="flex items-center gap-2">
            <ArrowUpDown className="h-4 w-4 text-muted-foreground" />
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="rounded-md border border-border bg-background px-3 py-1.5 text-sm text-foreground focus:outline-none focus:ring-1 focus:ring-asahio"
            >
              {SORT_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </div>

          {/* Period selector */}
          <div className="flex items-center gap-1 rounded-md border border-border bg-background p-1">
            {PERIODS.map((p) => (
              <button
                key={p.value}
                onClick={() => setPeriod(p.value)}
                className={cn(
                  "rounded-md px-3 py-1.5 text-sm font-medium transition-colors",
                  period === p.value
                    ? "bg-asahio text-white"
                    : "text-muted-foreground hover:text-foreground"
                )}
              >
                {p.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Loading state */}
      {isLoading && (
        <div className="space-y-3">
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="h-16 w-full animate-pulse rounded-lg bg-muted" />
          ))}
        </div>
      )}

      {/* Error state */}
      {error && (
        <div className="flex flex-col items-center justify-center rounded-lg border border-dashed border-border py-12">
          <AlertTriangle className="h-12 w-12 text-red-400/50 mb-4" />
          <p className="text-sm text-muted-foreground">Failed to load leaderboard data.</p>
        </div>
      )}

      {/* Empty state */}
      {data && data.entries.length === 0 && (
        <div className="flex flex-col items-center justify-center rounded-lg border border-dashed border-border py-12">
          <Trophy className="h-12 w-12 text-muted-foreground/50 mb-4" />
          <p className="text-sm text-muted-foreground">No model usage data for this period.</p>
          <p className="text-xs text-muted-foreground mt-1">
            Send requests through ASAHIO to populate the leaderboard.
          </p>
        </div>
      )}

      {/* Leaderboard table */}
      {data && data.entries.length > 0 && (
        <div className="overflow-x-auto rounded-lg border border-border">
          <table className="w-full">
            <thead>
              <tr className="border-b border-border bg-muted/30">
                <th className="px-4 py-3 text-left text-xs font-medium uppercase text-muted-foreground">
                  Rank
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium uppercase text-muted-foreground">
                  Model
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium uppercase text-muted-foreground">
                  Provider
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium uppercase text-muted-foreground">
                  <span className="inline-flex items-center gap-1">
                    <Activity className="h-3 w-3" />
                    Requests
                  </span>
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium uppercase text-muted-foreground">
                  <span className="inline-flex items-center gap-1">
                    <Clock className="h-3 w-3" />
                    Avg Latency
                  </span>
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium uppercase text-muted-foreground">
                  <span className="inline-flex items-center gap-1">
                    <Database className="h-3 w-3" />
                    Cache Hit
                  </span>
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium uppercase text-muted-foreground">
                  <span className="inline-flex items-center gap-1">
                    <DollarSign className="h-3 w-3" />
                    Cost
                  </span>
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium uppercase text-muted-foreground">
                  <span className="inline-flex items-center gap-1">
                    <TrendingUp className="h-3 w-3" />
                    Savings
                  </span>
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium uppercase text-muted-foreground">
                  <span className="inline-flex items-center gap-1">
                    <AlertTriangle className="h-3 w-3" />
                    Hallucination
                  </span>
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium uppercase text-muted-foreground">
                  Tokens
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {data.entries.map((entry) => (
                <tr
                  key={`${entry.model}-${entry.provider}`}
                  className="transition-colors hover:bg-muted/20"
                >
                  <td className="px-4 py-3">
                    <RankBadge rank={entry.rank} />
                  </td>
                  <td className="px-4 py-3">
                    <span className="text-sm font-medium text-foreground">
                      {entry.model}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <span className="text-sm capitalize text-muted-foreground">
                      {entry.provider || "unknown"}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <span className="text-sm font-mono text-foreground">
                      {formatNumber(entry.request_count)}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <span className="text-sm font-mono text-foreground">
                      {entry.avg_latency_ms.toFixed(0)}ms
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <RateBadge rate={entry.cache_hit_rate} />
                  </td>
                  <td className="px-4 py-3 text-right">
                    <span className="text-sm font-mono text-foreground">
                      {formatCurrency(entry.total_cost_usd)}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <RateBadge rate={entry.avg_savings_pct / 100} />
                  </td>
                  <td className="px-4 py-3 text-right">
                    <RateBadge rate={entry.hallucination_rate} inverted />
                  </td>
                  <td className="px-4 py-3 text-right">
                    <div className="text-xs text-muted-foreground">
                      <span className="font-mono">{formatNumber(entry.total_input_tokens)}</span> in
                      <br />
                      <span className="font-mono">{formatNumber(entry.total_output_tokens)}</span> out
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <div className="rounded-lg border border-border bg-muted/30 p-4 text-xs text-muted-foreground">
        <p className="flex items-center gap-2">
          <Trophy className="h-3 w-3" />
          <span>
            Leaderboard aggregates data from all requests in the selected period.
            Sorted by {SORT_OPTIONS.find((o) => o.value === sortBy)?.label || sortBy}.
          </span>
        </p>
      </div>
    </div>
  );
}
