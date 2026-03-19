"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { getRequestLogs, type RequestLogEntry } from "@/lib/api";
import { Activity, ChevronDown, ChevronRight, Database, Shield, Zap } from "lucide-react";
import { cn, formatCurrency } from "@/lib/utils";

const INTERVENTION_LABELS: Record<number, string> = {
  0: "LOG",
  1: "FLAG",
  2: "AUGMENT",
  3: "REROUTE",
  4: "BLOCK",
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

function InterventionLabel({ level }: { level: number }) {
  const label = INTERVENTION_LABELS[level] ?? `L${level}`;
  const colors: Record<number, string> = {
    1: "text-yellow-400",
    2: "text-blue-400",
    3: "text-orange-400",
    4: "text-red-400",
  };
  return <span className={`text-xs font-medium ${colors[level] ?? "text-muted-foreground"}`}>{label}</span>;
}

export default function TracesPage() {
  const params = useParams();
  const orgSlug = typeof params?.orgSlug === "string" ? params.orgSlug : "";

  const [page, setPage] = useState(1);
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [filterCacheHit, setFilterCacheHit] = useState<boolean | undefined>(undefined);

  const { data, isLoading } = useQuery({
    queryKey: ["traces", orgSlug, page, filterCacheHit],
    queryFn: () =>
      getRequestLogs(
        { page, limit: 25, cache_hit: filterCacheHit },
        undefined,
        orgSlug,
      ),
    enabled: !!orgSlug,
  });

  const logs = data?.data ?? [];
  const pagination = data?.pagination;

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Traces & Sessions</h1>
          <p className="text-sm text-muted-foreground">
            Inspect individual inference calls, latency, cost, and cache behavior.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <select
            value={filterCacheHit === undefined ? "all" : filterCacheHit ? "hits" : "misses"}
            onChange={(e) => {
              const v = e.target.value;
              setFilterCacheHit(v === "all" ? undefined : v === "hits");
              setPage(1);
            }}
            className="rounded-md border border-border bg-background px-3 py-1.5 text-sm text-foreground"
          >
            <option value="all">All requests</option>
            <option value="hits">Cache hits</option>
            <option value="misses">Cache misses</option>
          </select>
        </div>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center py-12 text-muted-foreground">Loading traces...</div>
      ) : logs.length === 0 ? (
        <div className="flex flex-col items-center justify-center rounded-lg border border-dashed border-border py-12">
          <Activity className="h-12 w-12 text-muted-foreground/50" />
          <p className="mt-4 text-sm text-muted-foreground">No traces found.</p>
        </div>
      ) : (
        <>
          <div className="overflow-x-auto rounded-lg border border-border">
            <table className="w-full text-left text-sm">
              <thead className="border-b border-border bg-muted/50">
                <tr>
                  <th className="w-8 px-2 py-3"></th>
                  <th className="px-4 py-3 font-medium text-muted-foreground">Time</th>
                  <th className="px-4 py-3 font-medium text-muted-foreground">Model</th>
                  <th className="px-4 py-3 font-medium text-muted-foreground">Provider</th>
                  <th className="px-4 py-3 font-medium text-muted-foreground">Routing</th>
                  <th className="px-4 py-3 font-medium text-muted-foreground">Tokens</th>
                  <th className="px-4 py-3 font-medium text-muted-foreground">Latency</th>
                  <th className="px-4 py-3 font-medium text-muted-foreground">Cache</th>
                  <th className="px-4 py-3 font-medium text-muted-foreground">Risk</th>
                  <th className="px-4 py-3 font-medium text-muted-foreground">Intervention</th>
                  <th className="px-4 py-3 font-medium text-muted-foreground">Savings</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {logs.map((log) => (
                  <TraceRow
                    key={log.id}
                    log={log}
                    expanded={expandedId === log.id}
                    onToggle={() => setExpandedId(expandedId === log.id ? null : log.id)}
                  />
                ))}
              </tbody>
            </table>
          </div>

          {pagination && pagination.pages > 1 && (
            <div className="flex items-center justify-between text-sm text-muted-foreground">
              <span>
                Page {pagination.page} of {pagination.pages} ({pagination.total} total)
              </span>
              <div className="flex gap-2">
                <button
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page <= 1}
                  className="rounded-md border border-border px-3 py-1 text-foreground transition-colors hover:bg-muted disabled:opacity-50"
                >
                  Previous
                </button>
                <button
                  onClick={() => setPage((p) => p + 1)}
                  disabled={page >= pagination.pages}
                  className="rounded-md border border-border px-3 py-1 text-foreground transition-colors hover:bg-muted disabled:opacity-50"
                >
                  Next
                </button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}

function TraceRow({
  log,
  expanded,
  onToggle,
}: {
  log: RequestLogEntry;
  expanded: boolean;
  onToggle: () => void;
}) {
  return (
    <>
      <tr
        onClick={onToggle}
        className="cursor-pointer hover:bg-muted/30 transition-colors"
      >
        <td className="px-2 py-3 text-muted-foreground">
          {expanded ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
        </td>
        <td className="px-4 py-3 text-muted-foreground whitespace-nowrap">
          {new Date(log.created_at).toLocaleString()}
        </td>
        <td className="px-4 py-3 font-mono text-xs text-foreground">{log.model_used}</td>
        <td className="px-4 py-3 text-muted-foreground">{log.provider ?? "-"}</td>
        <td className="px-4 py-3 text-muted-foreground">{log.routing_mode ?? "-"}</td>
        <td className="px-4 py-3 text-muted-foreground">
          {log.input_tokens + log.output_tokens}
        </td>
        <td className="px-4 py-3 text-muted-foreground">
          {log.latency_ms != null ? `${log.latency_ms}ms` : "-"}
        </td>
        <td className="px-4 py-3">
          {log.cache_hit ? (
            <span className="flex items-center gap-1 text-emerald-400">
              <Database className="h-3 w-3" />
              {log.cache_tier ?? "hit"}
            </span>
          ) : (
            <span className="flex items-center gap-1 text-muted-foreground">
              <Zap className="h-3 w-3" /> miss
            </span>
          )}
        </td>
        <td className="px-4 py-3">
          {log.risk_score != null ? (
            <RiskBadge score={log.risk_score} />
          ) : (
            <span className="text-muted-foreground">-</span>
          )}
        </td>
        <td className="px-4 py-3">
          {log.intervention_level != null && log.intervention_level > 0 ? (
            <InterventionLabel level={log.intervention_level} />
          ) : (
            <span className="text-muted-foreground">-</span>
          )}
        </td>
        <td className="px-4 py-3">
          {log.savings_usd > 0 ? (
            <span className="text-emerald-400">{formatCurrency(log.savings_usd)}</span>
          ) : (
            <span className="text-muted-foreground">-</span>
          )}
        </td>
      </tr>
      {expanded && (
        <tr className="bg-muted/20">
          <td colSpan={11} className="px-8 py-4">
            <div className="grid grid-cols-2 gap-4 text-sm md:grid-cols-4">
              <div>
                <span className="text-muted-foreground">Request ID</span>
                <p className="font-mono text-xs text-foreground">{log.request_id ?? log.id}</p>
              </div>
              <div>
                <span className="text-muted-foreground">Model Requested</span>
                <p className="text-foreground">{log.model_requested ?? "auto"}</p>
              </div>
              <div>
                <span className="text-muted-foreground">Input Tokens</span>
                <p className="text-foreground">{log.input_tokens}</p>
              </div>
              <div>
                <span className="text-muted-foreground">Output Tokens</span>
                <p className="text-foreground">{log.output_tokens}</p>
              </div>
              <div>
                <span className="text-muted-foreground">Cost (without ASAHIO)</span>
                <p className="text-foreground">{formatCurrency(log.cost_without_asahi)}</p>
              </div>
              <div>
                <span className="text-muted-foreground">Cost (with ASAHIO)</span>
                <p className="text-foreground">{formatCurrency(log.cost_with_asahi)}</p>
              </div>
              <div>
                <span className="text-muted-foreground">Savings %</span>
                <p className="text-foreground">{log.savings_pct != null ? `${log.savings_pct.toFixed(1)}%` : "-"}</p>
              </div>
              <div>
                <span className="text-muted-foreground">Status</span>
                <p className="text-foreground">{log.status_code}</p>
              </div>
              {log.risk_score != null && (
                <div>
                  <span className="text-muted-foreground">Risk Score</span>
                  <p className="text-foreground">{log.risk_score.toFixed(4)}</p>
                </div>
              )}
              {log.intervention_level != null && (
                <div>
                  <span className="text-muted-foreground">Intervention Level</span>
                  <p className="text-foreground">{INTERVENTION_LABELS[log.intervention_level] ?? `L${log.intervention_level}`}</p>
                </div>
              )}
            </div>
            {log.risk_factors && Object.keys(log.risk_factors).length > 0 && (
              <div className="mt-4 border-t border-border/50 pt-3">
                <span className="text-muted-foreground text-xs flex items-center gap-1 mb-2">
                  <Shield className="h-3 w-3" /> Risk Factors
                </span>
                <div className="flex flex-wrap gap-3">
                  {Object.entries(log.risk_factors).map(([factor, score]) => (
                    <div key={factor} className="text-xs">
                      <span className="text-muted-foreground">{factor}:</span>{" "}
                      <span className="font-mono text-foreground">{(score as number).toFixed(3)}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </td>
        </tr>
      )}
    </>
  );
}
