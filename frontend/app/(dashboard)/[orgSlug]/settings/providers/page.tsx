"use client";

import { useParams } from "next/navigation";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { Server } from "lucide-react";
import { getProviderHealth, type ProviderHealth } from "@/lib/api";

const STATUS_COLORS: Record<string, string> = {
  healthy: "bg-green-400",
  degraded: "bg-yellow-400",
  unreachable: "bg-red-400",
};

function StatusDot({ status }: { status: string }) {
  const color = STATUS_COLORS[status] ?? "bg-gray-400";
  return <span className={`inline-block h-2.5 w-2.5 rounded-full ${color}`} />;
}

export default function ProvidersPage() {
  const params = useParams();
  const orgSlug = typeof params?.orgSlug === "string" ? params.orgSlug : "";

  const { data, isLoading } = useQuery({
    queryKey: ["provider-health"],
    queryFn: () => getProviderHealth(),
    refetchInterval: 30_000,
  });

  const providers = data?.providers ?? [];

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Settings</h1>
        <p className="text-sm text-muted-foreground">
          Manage your organisation settings and preferences
        </p>
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
        <Link
          href={`/${orgSlug}/settings/security`}
          className="px-4 py-2 text-sm font-medium text-muted-foreground transition-colors hover:text-foreground"
        >
          Security
        </Link>
        <div className="border-b-2 border-asahio px-4 py-2 text-sm font-medium text-asahio">
          Providers
        </div>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center py-12 text-muted-foreground">
          Loading provider health...
        </div>
      ) : providers.length === 0 ? (
        <div className="rounded-lg border border-dashed border-border py-12 flex flex-col items-center">
          <Server className="h-12 w-12 text-muted-foreground/50" />
          <p className="mt-4 text-sm text-muted-foreground">
            No provider health data available. The health poller may not be running.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          {providers.map((p) => (
            <div
              key={p.provider}
              className="rounded-lg border border-border bg-card p-6 shadow-sm"
            >
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                  <Server className="h-5 w-5 text-asahio" />
                  <h3 className="text-lg font-semibold text-foreground capitalize">
                    {p.provider}
                  </h3>
                </div>
                <div className="flex items-center gap-2">
                  <StatusDot status={p.status} />
                  <span className="text-sm font-medium text-foreground capitalize">
                    {p.status}
                  </span>
                </div>
              </div>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Last checked</span>
                  <span className="text-foreground">
                    {p.last_checked
                      ? new Date(p.last_checked * 1000).toLocaleString()
                      : "-"}
                  </span>
                </div>
                {p.error && (
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Error</span>
                    <span className="text-red-400 text-xs">{p.error}</span>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
