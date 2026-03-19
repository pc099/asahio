"use client";

import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import {
  AlertTriangle,
  Ban,
  Eye,
  Flag,
  RefreshCw,
  Shield,
  ShieldAlert,
  Wand2,
} from "lucide-react";
import { KpiCard } from "@/components/charts/kpi-card";
import {
  getInterventions,
  getInterventionStats,
  getFleetModeOverview,
  type InterventionLogEntry,
  type FleetModeOverview,
} from "@/lib/api";

const LEVEL_LABELS: Record<number, string> = {
  0: "LOG",
  1: "FLAG",
  2: "AUGMENT",
  3: "REROUTE",
  4: "BLOCK",
};

const LEVEL_COLORS: Record<number, string> = {
  0: "bg-gray-500/10 text-gray-400",
  1: "bg-yellow-500/10 text-yellow-400",
  2: "bg-blue-500/10 text-blue-400",
  3: "bg-orange-500/10 text-orange-400",
  4: "bg-red-500/10 text-red-400",
};

const LEVEL_ICONS: Record<number, typeof Eye> = {
  0: Eye,
  1: Flag,
  2: Wand2,
  3: RefreshCw,
  4: Ban,
};

function RiskBadge({ score }: { score: number }) {
  let color = "bg-green-500/10 text-green-400";
  if (score >= 0.7) color = "bg-red-500/10 text-red-400";
  else if (score >= 0.5) color = "bg-orange-500/10 text-orange-400";
  else if (score >= 0.3) color = "bg-yellow-500/10 text-yellow-400";

  return (
    <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${color}`}>
      {score.toFixed(3)}
    </span>
  );
}

function InterventionBadge({ level }: { level: number }) {
  const label = LEVEL_LABELS[level] ?? `L${level}`;
  const color = LEVEL_COLORS[level] ?? "bg-gray-500/10 text-gray-400";
  const Icon = LEVEL_ICONS[level] ?? Eye;

  return (
    <span className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium ${color}`}>
      <Icon className="h-3 w-3" />
      {label}
    </span>
  );
}

export default function InterventionsPage() {
  const params = useParams();
  const orgSlug = typeof params?.orgSlug === "string" ? params.orgSlug : "";

  const { data: logs, isLoading: logsLoading } = useQuery({
    queryKey: ["interventions", orgSlug],
    queryFn: () => getInterventions({ limit: 100 }, undefined, orgSlug),
    enabled: !!orgSlug,
  });

  const { data: fleet, isLoading: fleetLoading } = useQuery({
    queryKey: ["fleet-overview", orgSlug],
    queryFn: () => getFleetModeOverview(undefined, orgSlug),
    enabled: !!orgSlug,
  });

  const entries = logs?.data ?? [];
  const summary = fleet?.intervention_summary;
  const modeDistribution = fleet?.mode_distribution ?? {};
  const isLoading = logsLoading || fleetLoading;

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground flex items-center gap-2">
            <ShieldAlert className="h-6 w-6 text-asahio" />
            Interventions
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            Risk-based intervention logs and fleet mode overview
          </p>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <KpiCard
          title="Total Interventions"
          value={summary?.total ?? 0}
          icon={Shield}
          loading={isLoading}
        />
        <KpiCard
          title="Blocked"
          value={summary?.blocked ?? 0}
          icon={Ban}
          loading={isLoading}
        />
        <KpiCard
          title="Rerouted"
          value={summary?.rerouted ?? 0}
          icon={RefreshCw}
          loading={isLoading}
        />
        <KpiCard
          title="Augmented"
          value={summary?.augmented ?? 0}
          icon={Wand2}
          loading={isLoading}
        />
      </div>

      {/* Fleet Mode Distribution */}
      <div className="rounded-lg border border-border bg-card p-6">
        <h2 className="text-lg font-semibold text-foreground mb-4">Fleet Mode Distribution</h2>
        <div className="flex gap-4 flex-wrap">
          {Object.entries(modeDistribution).map(([mode, count]) => (
            <div
              key={mode}
              className="flex items-center gap-2 rounded-lg border border-border px-4 py-3 bg-muted/50"
            >
              <span className="text-sm font-medium text-foreground">{mode}</span>
              <span className="text-lg font-bold text-asahio">{count}</span>
              <span className="text-xs text-muted-foreground">agents</span>
            </div>
          ))}
          {Object.keys(modeDistribution).length === 0 && !isLoading && (
            <p className="text-sm text-muted-foreground">No active agents</p>
          )}
        </div>
      </div>

      {/* Intervention Logs Table */}
      <div className="rounded-lg border border-border bg-card">
        <div className="p-6 border-b border-border">
          <h2 className="text-lg font-semibold text-foreground">Recent Intervention Logs</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border text-left">
                <th className="px-4 py-3 font-medium text-muted-foreground">Level</th>
                <th className="px-4 py-3 font-medium text-muted-foreground">Risk</th>
                <th className="px-4 py-3 font-medium text-muted-foreground">Action</th>
                <th className="px-4 py-3 font-medium text-muted-foreground">Mode</th>
                <th className="px-4 py-3 font-medium text-muted-foreground">Model</th>
                <th className="px-4 py-3 font-medium text-muted-foreground">Agent</th>
                <th className="px-4 py-3 font-medium text-muted-foreground">Time</th>
              </tr>
            </thead>
            <tbody>
              {entries.map((entry) => (
                <tr key={entry.id} className="border-b border-border/50 hover:bg-muted/30">
                  <td className="px-4 py-3">
                    <InterventionBadge level={entry.intervention_level} />
                  </td>
                  <td className="px-4 py-3">
                    <RiskBadge score={entry.risk_score} />
                  </td>
                  <td className="px-4 py-3 text-foreground capitalize">{entry.action_taken}</td>
                  <td className="px-4 py-3 text-muted-foreground">{entry.intervention_mode}</td>
                  <td className="px-4 py-3 text-muted-foreground font-mono text-xs">
                    {entry.final_model ?? entry.original_model ?? "-"}
                  </td>
                  <td className="px-4 py-3 text-muted-foreground font-mono text-xs">
                    {entry.agent_id ? entry.agent_id.slice(0, 8) + "..." : "-"}
                  </td>
                  <td className="px-4 py-3 text-muted-foreground text-xs">
                    {entry.created_at
                      ? new Date(entry.created_at).toLocaleString()
                      : "-"}
                  </td>
                </tr>
              ))}
              {entries.length === 0 && !isLoading && (
                <tr>
                  <td colSpan={7} className="px-4 py-8 text-center text-muted-foreground">
                    No intervention logs yet. Interventions are recorded when agents process requests.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
