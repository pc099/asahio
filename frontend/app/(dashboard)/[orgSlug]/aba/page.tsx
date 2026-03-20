"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import {
  Activity,
  AlertTriangle,
  Brain,
  Eye,
  Fingerprint,
  Search,
  Shield,
  Zap,
} from "lucide-react";
import { KpiCard } from "@/components/charts/kpi-card";
import {
  getABAFingerprints,
  getABAAnomalies,
  getABAOrgOverview,
  type ABAFingerprint,
  type ABAAnomaly,
  type ABAOrgOverview,
} from "@/lib/api";
import { formatPercent } from "@/lib/utils";

const SEVERITY_COLORS: Record<string, string> = {
  high: "bg-red-500/10 text-red-400 border-red-500/30",
  medium: "bg-amber-500/10 text-amber-400 border-amber-500/30",
  low: "bg-blue-500/10 text-blue-400 border-blue-500/30",
};

const ANOMALY_LABELS: Record<string, string> = {
  hallucination_spike: "Hallucination Spike",
  complexity_shift: "Complexity Shift",
  model_drift: "Model Drift",
  cache_degradation: "Cache Degradation",
};

export default function ABAOverviewPage() {
  const params = useParams();
  const router = useRouter();
  const orgSlug = typeof params?.orgSlug === "string" ? params.orgSlug : "";
  const [search, setSearch] = useState("");

  const { data: fpData, isLoading: fpLoading } = useQuery({
    queryKey: ["aba-fingerprints", orgSlug],
    queryFn: () => getABAFingerprints({ limit: 100 }, undefined, orgSlug),
    enabled: !!orgSlug,
  });

  const { data: anomalyData, isLoading: anomalyLoading } = useQuery({
    queryKey: ["aba-anomalies", orgSlug],
    queryFn: () => getABAAnomalies({}, undefined, orgSlug),
    enabled: !!orgSlug,
  });

  const { data: overview, isLoading: overviewLoading } = useQuery({
    queryKey: ["aba-org-overview", orgSlug],
    queryFn: () => getABAOrgOverview(undefined, orgSlug),
    enabled: !!orgSlug,
  });

  const fingerprints = fpData?.data ?? [];
  const anomalies = anomalyData?.data ?? [];

  const totalAgents = overview?.total_agents ?? fingerprints.length;
  const totalObservations = overview?.total_observations ?? fingerprints.reduce((s, f) => s + f.total_observations, 0);
  const avgHallucinationRate = overview?.avg_hallucination_rate ?? 0;
  const avgCacheHitRate = overview?.avg_cache_hit_rate ?? 0;
  const hallucinationDist = overview?.hallucination_distribution ?? {};

  const filtered = fingerprints.filter(
    (fp) =>
      !search ||
      fp.agent_id.toLowerCase().includes(search.toLowerCase())
  );

  const isLoading = fpLoading || anomalyLoading || overviewLoading;

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-foreground">Agent Behavioral Analytics</h1>
        <p className="text-sm text-muted-foreground">
          Behavioral fingerprints, anomaly detection, and risk priors across your agents
        </p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <KpiCard
          title="Tracked Agents"
          value={totalAgents}
          format="number"
          icon={Fingerprint}
          loading={isLoading}
        />
        <KpiCard
          title="Total Observations"
          value={totalObservations}
          format="number"
          icon={Eye}
          loading={isLoading}
        />
        <KpiCard
          title="Avg Hallucination Rate"
          value={avgHallucinationRate * 100}
          format="percentage"
          icon={AlertTriangle}
          loading={isLoading}
          highlight={avgHallucinationRate > 0.1}
        />
        <KpiCard
          title="Avg Cache Hit Rate"
          value={avgCacheHitRate * 100}
          format="percentage"
          icon={Zap}
          loading={isLoading}
        />
      </div>

      {/* Hallucination Distribution + Cold Start */}
      {overview && (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div className="rounded-lg border border-border bg-card p-6">
            <h2 className="text-sm font-semibold text-foreground mb-3">Hallucination Distribution</h2>
            <div className="space-y-2">
              {(["clean", "low", "medium", "high"] as const).map((bucket) => {
                const count = hallucinationDist[bucket] ?? 0;
                const pct = totalAgents > 0 ? (count / totalAgents) * 100 : 0;
                const colors: Record<string, string> = {
                  clean: "bg-emerald-400",
                  low: "bg-blue-400",
                  medium: "bg-amber-400",
                  high: "bg-red-400",
                };
                const labels: Record<string, string> = {
                  clean: "Clean (0%)",
                  low: "Low (<5%)",
                  medium: "Medium (5-15%)",
                  high: "High (>15%)",
                };
                return (
                  <div key={bucket} className="flex items-center gap-3">
                    <span className="w-24 text-xs text-muted-foreground">{labels[bucket]}</span>
                    <div className="h-2 flex-1 overflow-hidden rounded-full bg-muted">
                      <div
                        className={`h-full rounded-full ${colors[bucket]}`}
                        style={{ width: `${pct}%` }}
                      />
                    </div>
                    <span className="w-6 text-right text-xs font-mono text-muted-foreground">{count}</span>
                  </div>
                );
              })}
            </div>
          </div>
          <div className="rounded-lg border border-border bg-card p-6">
            <h2 className="text-sm font-semibold text-foreground mb-3">Fleet Health</h2>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs text-muted-foreground">Cold Start Agents</span>
                <span className="text-sm font-medium text-foreground">{overview.cold_start_agents}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-xs text-muted-foreground">Active Anomalies</span>
                <span className={`text-sm font-medium ${overview.anomaly_count > 0 ? "text-amber-400" : "text-foreground"}`}>
                  {overview.anomaly_count}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-xs text-muted-foreground">Avg Confidence</span>
                <span className="text-sm font-medium text-foreground">
                  {(overview.avg_baseline_confidence * 100).toFixed(1)}%
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-xs text-muted-foreground">Total Observations</span>
                <span className="text-sm font-medium text-foreground">
                  {overview.total_observations.toLocaleString()}
                </span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Anomaly Feed */}
      {anomalies.length > 0 && (
        <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
          <h2 className="mb-4 text-lg font-semibold text-foreground">Active Anomalies</h2>
          <div className="space-y-3">
            {anomalies.slice(0, 10).map((a, i) => (
              <div
                key={`${a.agent_id}-${a.anomaly_type}-${i}`}
                className={`flex items-center justify-between rounded-md border px-4 py-3 ${SEVERITY_COLORS[a.severity] || ""}`}
              >
                <div className="flex items-center gap-3">
                  <Shield className="h-4 w-4" />
                  <div>
                    <span className="text-sm font-medium">
                      {ANOMALY_LABELS[a.anomaly_type] || a.anomaly_type}
                    </span>
                    <span className="ml-2 text-xs opacity-70">
                      Agent {a.agent_id.slice(0, 8)}...
                    </span>
                  </div>
                </div>
                <div className="text-right text-xs">
                  <div>{a.deviation_pct.toFixed(1)}% deviation</div>
                  <div className="opacity-70">
                    {a.current_value.toFixed(3)} vs {a.baseline_value.toFixed(3)}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Fingerprint Table */}
      <div className="rounded-lg border border-border bg-card shadow-sm">
        <div className="flex items-center justify-between border-b border-border px-6 py-4">
          <h2 className="text-lg font-semibold text-foreground">Agent Fingerprints</h2>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Filter by agent ID..."
              className="rounded-md border border-border bg-background py-1.5 pl-9 pr-3 text-sm outline-none focus:border-asahio"
            />
          </div>
        </div>

        {isLoading ? (
          <div className="p-6">
            <div className="animate-pulse space-y-3">
              {Array.from({ length: 5 }).map((_, i) => (
                <div key={i} className="h-10 rounded bg-muted" />
              ))}
            </div>
          </div>
        ) : filtered.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16 text-center">
            <Brain className="mb-3 h-10 w-10 text-muted-foreground/50" />
            <p className="text-sm text-muted-foreground">
              No agent fingerprints yet. Send requests through agents to start building behavioral profiles.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-border text-left text-xs font-medium uppercase text-muted-foreground">
                  <th className="px-6 py-3">Agent</th>
                  <th className="px-6 py-3">Observations</th>
                  <th className="px-6 py-3">Complexity</th>
                  <th className="px-6 py-3">Hallucination</th>
                  <th className="px-6 py-3">Cache Hit</th>
                  <th className="px-6 py-3">Confidence</th>
                  <th className="px-6 py-3">Models</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {filtered.map((fp) => (
                  <tr
                    key={fp.id}
                    className="cursor-pointer hover:bg-muted/30 transition-colors"
                    onClick={() => router.push(`/${orgSlug}/aba/${fp.agent_id}`)}
                  >
                    <td className="px-6 py-3 text-sm font-mono text-foreground">
                      {fp.agent_id.slice(0, 12)}...
                    </td>
                    <td className="px-6 py-3 text-sm text-foreground">
                      {fp.total_observations}
                    </td>
                    <td className="px-6 py-3 text-sm">
                      <ComplexityBar value={fp.avg_complexity} />
                    </td>
                    <td className="px-6 py-3 text-sm">
                      <span
                        className={
                          fp.hallucination_rate > 0.1
                            ? "text-red-400"
                            : "text-foreground"
                        }
                      >
                        {formatPercent(fp.hallucination_rate * 100)}
                      </span>
                    </td>
                    <td className="px-6 py-3 text-sm text-foreground">
                      {formatPercent(fp.cache_hit_rate * 100)}
                    </td>
                    <td className="px-6 py-3 text-sm">
                      <ConfidenceDot value={fp.baseline_confidence} />
                    </td>
                    <td className="px-6 py-3 text-sm text-muted-foreground">
                      {Object.keys(fp.model_distribution).length} model
                      {Object.keys(fp.model_distribution).length !== 1 ? "s" : ""}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

function ComplexityBar({ value }: { value: number }) {
  const pct = Math.round(value * 100);
  const color =
    value > 0.7 ? "bg-red-400" : value > 0.4 ? "bg-amber-400" : "bg-emerald-400";
  return (
    <div className="flex items-center gap-2">
      <div className="h-1.5 w-16 rounded-full bg-muted">
        <div
          className={`h-1.5 rounded-full ${color}`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="text-xs text-muted-foreground">{value.toFixed(2)}</span>
    </div>
  );
}

function ConfidenceDot({ value }: { value: number }) {
  const color =
    value > 0.7 ? "bg-emerald-400" : value > 0.4 ? "bg-amber-400" : "bg-red-400";
  return (
    <div className="flex items-center gap-2">
      <div className={`h-2 w-2 rounded-full ${color}`} />
      <span className="text-xs text-muted-foreground">{(value * 100).toFixed(0)}%</span>
    </div>
  );
}
