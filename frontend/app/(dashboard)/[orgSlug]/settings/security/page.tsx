"use client";

import Link from "next/link";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useParams } from "next/navigation";
import { Shield } from "lucide-react";
import { getAuditLog } from "@/lib/api";

export default function SecurityPage() {
  const params = useParams();
  const orgSlug = typeof params?.orgSlug === "string" ? params.orgSlug : "";
  const [page, setPage] = useState(1);

  const { data, isLoading } = useQuery({
    queryKey: ["audit-log", orgSlug, page],
    queryFn: () => getAuditLog({ page, limit: 25 }, undefined, orgSlug),
    enabled: Boolean(orgSlug),
  });

  const entries = data?.data ?? [];
  const pagination = data?.pagination;

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Security</h1>
        <p className="text-sm text-muted-foreground">Audit log and security events</p>
      </div>

      <div className="flex gap-4 border-b border-border">
        <Link
          href={`/${orgSlug}/settings`}
          className="px-4 py-2 text-sm font-medium text-muted-foreground transition-colors hover:text-foreground"
        >
          General
        </Link>
        <Link
          href={`/${orgSlug}/settings/team`}
          className="px-4 py-2 text-sm font-medium text-muted-foreground transition-colors hover:text-foreground"
        >
          Team
        </Link>
        <div className="border-b-2 border-asahio px-4 py-2 text-sm font-medium text-asahio">
          Security
        </div>
      </div>

      <div className="rounded-lg border border-border bg-card shadow-sm">
        <div className="flex items-center gap-3 border-b border-border px-4 py-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-asahio/20">
            <Shield className="h-4 w-4 text-asahio" />
          </div>
          <h2 className="text-sm font-semibold text-foreground">Audit Log</h2>
        </div>

        {isLoading ? (
          <div className="animate-pulse space-y-4 p-6">
            {[1, 2, 3, 4, 5].map((item) => (
              <div key={item} className="h-10 rounded bg-muted" />
            ))}
          </div>
        ) : entries.length === 0 ? (
          <div className="flex h-48 flex-col items-center justify-center gap-3">
            <Shield className="h-8 w-8 text-muted-foreground" />
            <p className="text-sm text-muted-foreground">No audit log entries yet.</p>
          </div>
        ) : (
          <>
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border text-left text-xs text-muted-foreground">
                  <th className="px-4 py-3">Time</th>
                  <th className="px-4 py-3">Actor</th>
                  <th className="px-4 py-3">Action</th>
                  <th className="px-4 py-3">Resource</th>
                  <th className="px-4 py-3">IP</th>
                </tr>
              </thead>
              <tbody>
                {entries.map((entry) => (
                  <tr
                    key={entry.id}
                    className="border-b border-border transition-colors last:border-0 hover:bg-muted/50"
                  >
                    <td className="whitespace-nowrap px-4 py-3 text-muted-foreground">
                      {new Date(entry.timestamp).toLocaleString()}
                    </td>
                    <td className="px-4 py-3 font-medium text-foreground">{entry.actor}</td>
                    <td className="px-4 py-3">
                      <span className="inline-flex items-center rounded-full bg-muted px-2 py-0.5 text-xs font-medium text-muted-foreground">
                        {entry.action}
                      </span>
                    </td>
                    <td className="px-4 py-3 font-mono text-xs text-muted-foreground">
                      {entry.resource}
                    </td>
                    <td className="px-4 py-3 font-mono text-xs text-muted-foreground">
                      {entry.ip_address || "-"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            {pagination && pagination.pages > 1 && (
              <div className="flex items-center justify-between border-t border-border px-4 py-3">
                <p className="text-xs text-muted-foreground">
                  Page {pagination.page} of {pagination.pages} ({pagination.total} entries)
                </p>
                <div className="flex gap-2">
                  <button
                    onClick={() => setPage((current) => Math.max(1, current - 1))}
                    disabled={page <= 1}
                    className="rounded-md border border-border px-3 py-1 text-xs font-medium text-foreground transition-colors hover:bg-muted disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    Previous
                  </button>
                  <button
                    onClick={() => setPage((current) => Math.min(pagination.pages, current + 1))}
                    disabled={page >= pagination.pages}
                    className="rounded-md border border-border px-3 py-1 text-xs font-medium text-foreground transition-colors hover:bg-muted disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    Next
                  </button>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
