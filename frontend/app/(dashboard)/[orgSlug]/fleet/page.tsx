"use client";

import { useParams, useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import {
  Bot,
  Eye,
  Loader2,
  Shield,
  ShieldAlert,
  Ban,
  RefreshCw,
  Wand2,
  Zap,
} from "lucide-react";
import { KpiCard } from "@/components/charts/kpi-card";
import {
  getFleetModeOverview,
  listAgents,
  type AgentItem,
  type FleetModeOverview,
} from "@/lib/api";
import { cn } from "@/lib/utils";

const MODE_COLORS: Record<string, { bg: string; border: string; text: string; ring: string }> = {
  OBSERVE: { bg: "bg-gray-500/10", border: "border-gray-500/30", text: "text-gray-400", ring: "ring-gray-400" },
  ASSISTED: { bg: "bg-blue-500/10", border: "border-blue-500/30", text: "text-blue-400", ring: "ring-blue-400" },
  AUTONOMOUS: { bg: "bg-purple-500/10", border: "border-purple-500/30", text: "text-purple-400", ring: "ring-purple-400" },
};

const ROUTING_BADGE: Record<string, string> = {
  AUTO: "bg-emerald-500/15 text-emerald-400",
  EXPLICIT: "bg-blue-500/15 text-blue-400",
  GUIDED: "bg-amber-500/15 text-amber-400",
};

export default function FleetOverviewPage() {
  const params = useParams();
  const router = useRouter();
  const orgSlug = typeof params?.orgSlug === "string" ? params.orgSlug : "";

  const { data: fleet, isLoading: fleetLoading } = useQuery({
    queryKey: ["fleet-overview", orgSlug],
    queryFn: () => getFleetModeOverview(undefined, orgSlug),
    enabled: !!orgSlug,
    refetchInterval: 30_000,
  });

  const { data: agentsData, isLoading: agentsLoading } = useQuery({
    queryKey: ["agents", orgSlug],
    queryFn: () => listAgents(undefined, orgSlug),
    enabled: !!orgSlug,
  });

  const agents = agentsData?.data ?? [];
  const summary = fleet?.intervention_summary;
  const modeDistribution = fleet?.mode_distribution ?? {};
  const isLoading = fleetLoading || agentsLoading;

  // Group agents by intervention mode
  const grouped: Record<string, AgentItem[]> = {};
  for (const agent of agents) {
    const mode = agent.intervention_mode || "OBSERVE";
    if (!grouped[mode]) grouped[mode] = [];
    grouped[mode].push(agent);
  }

  // Donut chart data
  const totalAgents = agents.length;
  const modeEntries = Object.entries(modeDistribution);
  const donutSegments = modeEntries.map(([mode, count]) => ({
    mode,
    count: count as number,
    pct: totalAgents > 0 ? ((count as number) / totalAgents) * 100 : 0,
  }));

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-foreground flex items-center gap-2">
          <Shield className="h-6 w-6 text-asahio" />
          Fleet Overview
        </h1>
        <p className="text-sm text-muted-foreground mt-1">
          Agent fleet status, intervention modes, and operational health
        </p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-5">
        <KpiCard
          title="Total Agents"
          value={totalAgents}
          format="number"
          icon={Bot}
          loading={isLoading}
        />
        <KpiCard
          title="Interventions (30d)"
          value={summary?.total ?? 0}
          format="number"
          icon={ShieldAlert}
          loading={isLoading}
        />
        <KpiCard
          title="Blocked"
          value={summary?.blocked ?? 0}
          format="number"
          icon={Ban}
          loading={isLoading}
          highlight={(summary?.blocked ?? 0) > 0}
        />
        <KpiCard
          title="Rerouted"
          value={summary?.rerouted ?? 0}
          format="number"
          icon={RefreshCw}
          loading={isLoading}
        />
        <KpiCard
          title="Augmented"
          value={summary?.augmented ?? 0}
          format="number"
          icon={Wand2}
          loading={isLoading}
        />
      </div>

      {/* Mode Distribution Visual */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Donut */}
        <div className="rounded-lg border border-border bg-card p-6">
          <h2 className="text-sm font-semibold text-foreground mb-4">Mode Distribution</h2>
          {isLoading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            </div>
          ) : totalAgents === 0 ? (
            <p className="text-sm text-muted-foreground text-center py-8">No agents registered</p>
          ) : (
            <div className="flex flex-col items-center gap-4">
              {/* Simple ring chart */}
              <DonutChart segments={donutSegments} total={totalAgents} />
              {/* Legend */}
              <div className="space-y-2 w-full">
                {(["OBSERVE", "ASSISTED", "AUTONOMOUS"] as const).map((mode) => {
                  const count = (modeDistribution[mode] as number) ?? 0;
                  const colors = MODE_COLORS[mode];
                  return (
                    <div key={mode} className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <div className={cn("h-3 w-3 rounded-full", colors.bg, "ring-2", colors.ring)} />
                        <span className="text-xs text-muted-foreground">{mode}</span>
                      </div>
                      <span className="text-sm font-medium text-foreground">{count}</span>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>

        {/* Agent Groups */}
        <div className="lg:col-span-2 space-y-4">
          {(["OBSERVE", "ASSISTED", "AUTONOMOUS"] as const).map((mode) => {
            const modeAgents = grouped[mode] ?? [];
            const colors = MODE_COLORS[mode];
            if (modeAgents.length === 0 && !isLoading) return null;

            return (
              <div key={mode} className={cn("rounded-lg border p-4", colors.border, colors.bg)}>
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    {mode === "OBSERVE" && <Eye className={cn("h-4 w-4", colors.text)} />}
                    {mode === "ASSISTED" && <Zap className={cn("h-4 w-4", colors.text)} />}
                    {mode === "AUTONOMOUS" && <ShieldAlert className={cn("h-4 w-4", colors.text)} />}
                    <span className={cn("text-sm font-semibold", colors.text)}>{mode}</span>
                  </div>
                  <span className="text-xs text-muted-foreground">
                    {modeAgents.length} agent{modeAgents.length !== 1 ? "s" : ""}
                  </span>
                </div>
                {modeAgents.length > 0 ? (
                  <div className="space-y-1">
                    {modeAgents.map((agent) => (
                      <button
                        key={agent.id}
                        type="button"
                        onClick={() => router.push(`/${orgSlug}/agents/${agent.id}`)}
                        className="flex w-full items-center justify-between rounded-md bg-background/50 px-3 py-2 text-left transition-colors hover:bg-background"
                      >
                        <div className="flex items-center gap-2">
                          <Bot className="h-3.5 w-3.5 text-muted-foreground" />
                          <span className="text-sm text-foreground">{agent.name}</span>
                          <span className="text-[10px] font-mono text-muted-foreground">
                            {agent.slug}
                          </span>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className={cn("rounded-full px-2 py-0.5 text-[10px] font-medium", ROUTING_BADGE[agent.routing_mode] ?? "bg-muted text-muted-foreground")}>
                            {agent.routing_mode}
                          </span>
                          {!agent.is_active && (
                            <span className="rounded-full bg-red-500/10 px-2 py-0.5 text-[10px] text-red-400">
                              Inactive
                            </span>
                          )}
                        </div>
                      </button>
                    ))}
                  </div>
                ) : isLoading ? (
                  <div className="h-8 animate-pulse rounded bg-muted" />
                ) : null}
              </div>
            );
          })}
          {!isLoading && agents.length === 0 && (
            <div className="flex flex-col items-center justify-center rounded-lg border border-dashed border-border py-12">
              <Bot className="h-12 w-12 text-muted-foreground/50" />
              <p className="mt-4 text-sm text-muted-foreground">
                No agents registered. Create agents to see fleet status.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Simple SVG donut chart
// ---------------------------------------------------------------------------

function DonutChart({
  segments,
  total,
}: {
  segments: Array<{ mode: string; count: number; pct: number }>;
  total: number;
}) {
  const size = 120;
  const strokeWidth = 16;
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const cx = size / 2;
  const cy = size / 2;

  const colorMap: Record<string, string> = {
    OBSERVE: "#6b7280",
    ASSISTED: "#3b82f6",
    AUTONOMOUS: "#a855f7",
  };

  let offset = 0;

  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
      {/* Background ring */}
      <circle
        cx={cx}
        cy={cy}
        r={radius}
        fill="none"
        stroke="currentColor"
        strokeWidth={strokeWidth}
        className="text-muted/30"
      />
      {segments.map((seg) => {
        const dashLen = (seg.count / total) * circumference;
        const dashOffset = circumference - offset;
        offset += dashLen;
        return (
          <circle
            key={seg.mode}
            cx={cx}
            cy={cy}
            r={radius}
            fill="none"
            stroke={colorMap[seg.mode] ?? "#6b7280"}
            strokeWidth={strokeWidth}
            strokeDasharray={`${dashLen} ${circumference - dashLen}`}
            strokeDashoffset={dashOffset}
            strokeLinecap="round"
            transform={`rotate(-90 ${cx} ${cy})`}
          />
        );
      })}
      <text x={cx} y={cy - 6} textAnchor="middle" className="fill-foreground text-xl font-bold">
        {total}
      </text>
      <text x={cx} y={cy + 10} textAnchor="middle" className="fill-muted-foreground text-[10px]">
        agents
      </text>
    </svg>
  );
}
