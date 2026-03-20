"use client";

import { useQuery } from "@tanstack/react-query";
import { useParams } from "next/navigation";
import { getCacheStats } from "@/lib/api";
import { cn } from "@/lib/utils";
import { GitBranch, Layers, Brain, ArrowRight, Database } from "lucide-react";

const classLabels: Record<string, { label: string; color: string; bg: string; description: string }> = {
  INDEPENDENT: {
    label: "Independent",
    color: "text-green-400",
    bg: "bg-green-500/20",
    description: "No dependencies on prior steps — safe for exact cache",
  },
  PARTIAL: {
    label: "Partial",
    color: "text-yellow-400",
    bg: "bg-yellow-500/20",
    description: "Depends on prior context — uses context-aware cache keys",
  },
  SEQUENTIAL: {
    label: "Sequential",
    color: "text-orange-400",
    bg: "bg-orange-500/20",
    description: "Strictly ordered dependency chain — semantic cache eligible",
  },
  CRITICAL: {
    label: "Critical",
    color: "text-red-400",
    bg: "bg-red-500/20",
    description: "Safety-critical — never served from cache, always live LLM call",
  },
};

export default function CacheDependenciesPage() {
  const params = useParams();
  const orgSlug = typeof params?.orgSlug === "string" ? params.orgSlug : "";

  const { data: stats, isLoading } = useQuery({
    queryKey: ["cache-stats", orgSlug],
    queryFn: () => getCacheStats(undefined, orgSlug),
    enabled: Boolean(orgSlug),
  });

  const metrics = stats?.metrics;

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Cache Dependencies</h1>
        <p className="text-sm text-muted-foreground">
          How dependency classification determines cache eligibility per request
        </p>
      </div>

      {/* Dependency class reference */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {Object.entries(classLabels).map(([key, cfg]) => (
          <div key={key} className="rounded-lg border border-border bg-card p-5 shadow-sm">
            <div className="flex items-center gap-2">
              <div className={cn("flex h-8 w-8 items-center justify-center rounded-md", cfg.bg)}>
                {key === "INDEPENDENT" ? (
                  <Layers className={cn("h-4 w-4", cfg.color)} />
                ) : key === "CRITICAL" ? (
                  <Database className={cn("h-4 w-4", cfg.color)} />
                ) : (
                  <GitBranch className={cn("h-4 w-4", cfg.color)} />
                )}
              </div>
              <h3 className={cn("text-sm font-semibold", cfg.color)}>{cfg.label}</h3>
            </div>
            <p className="mt-2 text-xs text-muted-foreground">{cfg.description}</p>
          </div>
        ))}
      </div>

      {/* Cache flow diagram */}
      <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
        <h2 className="mb-4 text-sm font-semibold text-foreground">Cache Lookup Flow</h2>
        <div className="flex flex-wrap items-center gap-3 text-xs">
          <div className="rounded-md border border-border bg-muted px-3 py-2 font-mono">
            Incoming Request
          </div>
          <ArrowRight className="h-4 w-4 text-muted-foreground" />
          <div className="rounded-md border border-border bg-muted px-3 py-2 font-mono">
            Classify Dependency
          </div>
          <ArrowRight className="h-4 w-4 text-muted-foreground" />
          <div className="flex flex-col gap-1">
            <span className="rounded bg-green-500/20 px-2 py-1 text-green-400">
              INDEPENDENT → Exact cache
            </span>
            <span className="rounded bg-yellow-500/20 px-2 py-1 text-yellow-400">
              PARTIAL → Context-aware key
            </span>
            <span className="rounded bg-orange-500/20 px-2 py-1 text-orange-400">
              SEQUENTIAL → Semantic cache
            </span>
            <span className="rounded bg-red-500/20 px-2 py-1 text-red-400">
              CRITICAL → Skip cache
            </span>
          </div>
          <ArrowRight className="h-4 w-4 text-muted-foreground" />
          <div className="rounded-md border border-border bg-muted px-3 py-2 font-mono">
            Response
          </div>
        </div>
      </div>

      {/* Live cache metrics */}
      <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
        <h2 className="mb-4 text-sm font-semibold text-foreground">Live Cache Metrics</h2>
        {isLoading ? (
          <div className="animate-pulse space-y-3">
            <div className="h-5 w-40 rounded bg-muted" />
            <div className="h-16 w-full rounded bg-muted" />
          </div>
        ) : !metrics ? (
          <p className="text-sm text-muted-foreground">
            No cache metrics available. Send requests through the gateway to start collecting data.
          </p>
        ) : (
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
            <div>
              <p className="text-xs text-muted-foreground">Exact Hits</p>
              <p className="text-2xl font-bold text-green-400">
                {metrics.exact_hits.toLocaleString()}
              </p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Semantic Hits</p>
              <p className="text-2xl font-bold text-blue-400">
                {metrics.semantic_hits.toLocaleString()}
              </p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Misses</p>
              <p className="text-2xl font-bold text-muted-foreground">
                {metrics.misses.toLocaleString()}
              </p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Hit Rate</p>
              <p className="text-2xl font-bold text-asahio">
                {(metrics.hit_rate * 100).toFixed(1)}%
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
