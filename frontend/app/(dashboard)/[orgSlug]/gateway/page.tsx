"use client";

import { useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { getRequestLogs } from "@/lib/api";
import { cn, formatCurrency } from "@/lib/utils";

const tierColors: Record<string, string> = {
  exact: "bg-green-500/20 text-green-400",
  semantic: "bg-blue-500/20 text-blue-400",
  intermediate: "bg-purple-500/20 text-purple-400",
};

export default function GatewayPage() {
  const [page, setPage] = useState(1);
  const params = useParams();
  const orgSlug = typeof params?.orgSlug === "string" ? params.orgSlug : "";

  const { data, isLoading } = useQuery({
    queryKey: ["request-logs", orgSlug, page],
    queryFn: () => getRequestLogs({ page, limit: 25 }, undefined, orgSlug),
  });

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Gateway</h1>
          <p className="text-sm text-muted-foreground">Inspect request logs and verify the live control-plane response path.</p>
        </div>
        <Link href={`/${orgSlug}/gateway/playground`} className="rounded-md bg-asahio px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-asahio-dark">
          Open Playground
        </Link>
      </div>

      <div className="overflow-x-auto rounded-lg border border-border bg-card shadow-sm">
        {isLoading ? (
          <div className="space-y-3 p-6 animate-pulse">
            {[1, 2, 3, 4, 5].map((item) => (
              <div key={item} className="h-10 rounded bg-muted" />
            ))}
          </div>
        ) : !data || data.data.length === 0 ? (
          <div className="flex h-40 items-center justify-center text-sm text-muted-foreground">
            No requests yet. Use the playground or SDK to send your first request.
          </div>
        ) : (
          <>
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border text-left text-xs text-muted-foreground">
                  <th className="px-4 py-3">Time</th>
                  <th className="px-4 py-3">Model</th>
                  <th className="px-4 py-3">In/Out</th>
                  <th className="px-4 py-3">Without ASAHIO</th>
                  <th className="px-4 py-3">With ASAHIO</th>
                  <th className="px-4 py-3">Cache</th>
                  <th className="px-4 py-3">Savings</th>
                  <th className="px-4 py-3">Latency</th>
                </tr>
              </thead>
              <tbody>
                {data.data.map((row) => (
                  <tr key={row.id} className="border-b border-border last:border-0 transition-colors hover:bg-muted/50">
                    <td className="whitespace-nowrap px-4 py-3 text-muted-foreground">{new Date(row.created_at).toLocaleString()}</td>
                    <td className="px-4 py-3 font-mono text-xs text-foreground">{row.model_used}</td>
                    <td className="px-4 py-3 text-muted-foreground">{row.input_tokens}/{row.output_tokens}</td>
                    <td className="px-4 py-3 text-muted-foreground">{formatCurrency(row.cost_without_asahi)}</td>
                    <td className="px-4 py-3 text-foreground">{formatCurrency(row.cost_with_asahi)}</td>
                    <td className="px-4 py-3">
                      {row.cache_hit ? (
                        <span className={cn("rounded-full px-2 py-0.5 text-xs font-medium", tierColors[row.cache_tier || ""] || "bg-muted text-muted-foreground")}>
                          {row.cache_tier || "hit"}
                        </span>
                      ) : (
                        <span className="rounded-full bg-muted px-2 py-0.5 text-xs text-muted-foreground">miss</span>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      {row.savings_pct !== null && row.savings_pct > 0 ? (
                        <span className="text-xs font-medium text-green-400">{row.savings_pct.toFixed(0)}%</span>
                      ) : (
                        <span className="text-xs text-muted-foreground">-</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-muted-foreground">{row.latency_ms ? `${row.latency_ms}ms` : "-"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            {data.pagination.pages > 1 && (
              <div className="flex items-center justify-between border-t border-border px-4 py-3">
                <span className="text-xs text-muted-foreground">Page {data.pagination.page} of {data.pagination.pages} ({data.pagination.total} total)</span>
                <div className="flex gap-2">
                  <button onClick={() => setPage((current) => Math.max(1, current - 1))} disabled={page <= 1} className="rounded-md border border-border px-3 py-1 text-xs transition-colors hover:bg-muted disabled:opacity-50">Previous</button>
                  <button onClick={() => setPage((current) => current + 1)} disabled={page >= data.pagination.pages} className="rounded-md border border-border px-3 py-1 text-xs transition-colors hover:bg-muted disabled:opacity-50">Next</button>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
