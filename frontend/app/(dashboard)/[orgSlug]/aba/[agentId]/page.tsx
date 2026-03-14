"use client";

import { useParams, useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import {
  Activity,
  AlertTriangle,
  ArrowLeft,
  Brain,
  Database,
  Eye,
  Fingerprint,
  Shield,
  Zap,
} from "lucide-react";
import { KpiCard } from "@/components/charts/kpi-card";
import {
  getABAFingerprint,
  getABAStructuralRecords,
  getABAAnomalies,
  getABAColdStartStatus,
  type ABAFingerprint,
  type ABAStructuralRecord,
  type ABAAnomaly,
  type ABAColdStartStatus,
} from "@/lib/api";
import { formatPercent } from "@/lib/utils";

const SEVERITY_COLORS: Record<string, string> = {
  high: "bg-red-500/10 text-red-400 border-red-500/30",
  medium: "bg-amber-500/10 text-amber-400 border-amber-500/30",
  low: "bg-blue-500/10 text-blue-400 border-blue-500/30",
};

export default function ABAAgentDetailPage() {
  const params = useParams();
  const router = useRouter();
  const orgSlug = typeof params?.orgSlug === "string" ? params.orgSlug : "";
  const agentId = typeof params?.agentId === "string" ? params.agentId : "";

  const { data: fingerprint, isLoading: fpLoading } = useQuery({
    queryKey: ["aba-fingerprint", orgSlug, agentId],
    queryFn: () => getABAFingerprint(agentId, undefined, orgSlug),
    enabled: !!orgSlug && !!agentId,
  });

  const { data: recordsData, isLoading: recordsLoading } = useQuery({
    queryKey: ["aba-records", orgSlug, agentId],
    queryFn: () => getABAStructuralRecords({ agent_id: agentId, limit: 50 }, undefined, orgSlug),
    enabled: !!orgSlug && !!agentId,
  });

  const { data: anomalyData } = useQuery({
    queryKey: ["aba-anomalies", orgSlug, agentId],
    queryFn: () => getABAAnomalies({ agent_id: agentId }, undefined, orgSlug),
    enabled: !!orgSlug && !!agentId,
  });

  const { data: coldStart } = useQuery({
    queryKey: ["aba-cold-start", orgSlug, agentId],
    queryFn: () => getABAColdStartStatus(agentId, undefined, orgSlug),
    enabled: !!orgSlug && !!agentId,
  });

  const records = recordsData?.data ?? [];
  const anomalies = anomalyData?.data ?? [];
  const isLoading = fpLoading || recordsLoading;

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center gap-4">
        <button
          onClick={() => router.push(`/${orgSlug}/aba`)}
          className="rounded-md p-1.5 hover:bg-muted transition-colors"
        >
          <ArrowLeft className="h-5 w-5 text-muted-foreground" />
        </button>
        <div>
          <h1 className="text-2xl font-bold text-foreground">Agent Detail</h1>
          <p className="font-mono text-sm text-muted-foreground">{agentId}</p>
        </div>
      </div>

      {/* Cold Start Banner */}
      {coldStart?.is_cold_start && (
        <div className="rounded-lg border border-amber-500/30 bg-amber-500/10 px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Brain className="h-5 w-5 text-amber-400" />
              <div>
                <p className="text-sm font-medium text-amber-400">Cold Start Active</p>
                <p className="text-xs text-amber-400/70">
                  {coldStart.total_observations} / {coldStart.cold_start_threshold} observations
                  {coldStart.bootstrap_source && ` — bootstrapped from ${coldStart.bootstrap_source}`}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <div className="h-2 w-32 rounded-full bg-amber-500/20">
                <div
                  className="h-2 rounded-full bg-amber-400"
                  style={{ width: `${coldStart.progress_pct}%` }}
                />
              </div>
              <span className="text-xs text-amber-400">{coldStart.progress_pct}%</span>
            </div>
          </div>
        </div>
      )}

      {/* KPI Cards */}
      {fingerprint && (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <KpiCard
            title="Observations"
            value={fingerprint.total_observations}
            format="number"
            icon={Eye}
            loading={isLoading}
          />
          <KpiCard
            title="Avg Complexity"
            value={fingerprint.avg_complexity * 100}
            format="percentage"
            icon={Activity}
            loading={isLoading}
          />
          <KpiCard
            title="Hallucination Rate"
            value={fingerprint.hallucination_rate * 100}
            format="percentage"
            icon={AlertTriangle}
            loading={isLoading}
            highlight={fingerprint.hallucination_rate > 0.1}
          />
          <KpiCard
            title="Cache Hit Rate"
            value={fingerprint.cache_hit_rate * 100}
            format="percentage"
            icon={Zap}
            loading={isLoading}
          />
        </div>
      )}

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Model Distribution */}
        {fingerprint && (
          <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
            <h2 className="mb-4 text-lg font-semibold text-foreground">Model Distribution</h2>
            <ModelDistributionChart distribution={fingerprint.model_distribution} />
          </div>
        )}

        {/* Anomalies */}
        <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
          <h2 className="mb-4 text-lg font-semibold text-foreground">Anomalies</h2>
          {anomalies.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-8 text-center">
              <Shield className="mb-2 h-8 w-8 text-emerald-400/50" />
              <p className="text-sm text-muted-foreground">No anomalies detected</p>
            </div>
          ) : (
            <div className="space-y-2">
              {anomalies.map((a, i) => (
                <div
                  key={`${a.anomaly_type}-${i}`}
                  className={`rounded-md border px-4 py-2 text-sm ${SEVERITY_COLORS[a.severity] || ""}`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-medium">{a.anomaly_type.replace(/_/g, " ")}</span>
                    <span className="text-xs uppercase">{a.severity}</span>
                  </div>
                  <div className="mt-1 text-xs opacity-70">
                    {a.current_value.toFixed(3)} vs baseline {a.baseline_value.toFixed(3)} ({a.deviation_pct.toFixed(1)}% deviation)
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Structural Records Table */}
      <div className="rounded-lg border border-border bg-card shadow-sm">
        <div className="border-b border-border px-6 py-4">
          <h2 className="text-lg font-semibold text-foreground">Structural Records</h2>
          <p className="text-xs text-muted-foreground">
            Recent structural analysis records for this agent
          </p>
        </div>

        {isLoading ? (
          <div className="p-6">
            <div className="animate-pulse space-y-3">
              {Array.from({ length: 5 }).map((_, i) => (
                <div key={i} className="h-10 rounded bg-muted" />
              ))}
            </div>
          </div>
        ) : records.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <Database className="mb-2 h-8 w-8 text-muted-foreground/50" />
            <p className="text-sm text-muted-foreground">No structural records yet</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-border text-left text-xs font-medium uppercase text-muted-foreground">
                  <th className="px-6 py-3">Time</th>
                  <th className="px-6 py-3">Agent Type</th>
                  <th className="px-6 py-3">Output Type</th>
                  <th className="px-6 py-3">Complexity</th>
                  <th className="px-6 py-3">Model</th>
                  <th className="px-6 py-3">Tokens</th>
                  <th className="px-6 py-3">Latency</th>
                  <th className="px-6 py-3">Cache</th>
                  <th className="px-6 py-3">Halluc.</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {records.map((r) => (
                  <tr key={r.id} className="hover:bg-muted/30 transition-colors">
                    <td className="whitespace-nowrap px-6 py-3 text-xs text-muted-foreground">
                      {new Date(r.created_at).toLocaleString()}
                    </td>
                    <td className="px-6 py-3 text-sm">
                      <span className="rounded bg-muted px-2 py-0.5 text-xs font-medium">
                        {r.agent_type_classification}
                      </span>
                    </td>
                    <td className="px-6 py-3 text-sm">
                      <span className="rounded bg-muted px-2 py-0.5 text-xs font-medium">
                        {r.output_type_classification}
                      </span>
                    </td>
                    <td className="px-6 py-3 text-sm text-foreground">
                      {r.query_complexity_score.toFixed(2)}
                    </td>
                    <td className="px-6 py-3 text-sm font-mono text-foreground">
                      {r.model_used}
                    </td>
                    <td className="px-6 py-3 text-sm text-foreground">
                      {r.token_count.toLocaleString()}
                    </td>
                    <td className="px-6 py-3 text-sm text-foreground">
                      {r.latency_ms != null ? `${r.latency_ms}ms` : "—"}
                    </td>
                    <td className="px-6 py-3 text-sm">
                      {r.cache_hit ? (
                        <span className="text-emerald-400">hit</span>
                      ) : (
                        <span className="text-muted-foreground">miss</span>
                      )}
                    </td>
                    <td className="px-6 py-3 text-sm">
                      {r.hallucination_detected ? (
                        <span className="text-red-400">yes</span>
                      ) : (
                        <span className="text-muted-foreground">no</span>
                      )}
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

function ModelDistributionChart({ distribution }: { distribution: Record<string, number> }) {
  const entries = Object.entries(distribution).sort((a, b) => b[1] - a[1]);
  const total = entries.reduce((s, [, v]) => s + v, 0);
  if (total === 0) {
    return <p className="text-sm text-muted-foreground">No model usage data</p>;
  }

  const COLORS = [
    "bg-asahio",
    "bg-emerald-400",
    "bg-amber-400",
    "bg-purple-400",
    "bg-rose-400",
  ];

  return (
    <div className="space-y-3">
      {entries.map(([model, count], i) => {
        const pct = (count / total) * 100;
        return (
          <div key={model}>
            <div className="mb-1 flex items-center justify-between text-sm">
              <span className="font-mono text-foreground">{model}</span>
              <span className="text-muted-foreground">
                {count} ({pct.toFixed(1)}%)
              </span>
            </div>
            <div className="h-2 w-full rounded-full bg-muted">
              <div
                className={`h-2 rounded-full ${COLORS[i % COLORS.length]}`}
                style={{ width: `${pct}%` }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
}
