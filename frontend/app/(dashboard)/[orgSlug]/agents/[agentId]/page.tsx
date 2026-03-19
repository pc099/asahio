"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  ArrowLeft,
  Bot,
  CheckCircle2,
  Clock,
  GitBranch,
  Shield,
  ShieldAlert,
  XCircle,
} from "lucide-react";
import Link from "next/link";
import {
  getModeEligibility,
  getModeHistory,
  transitionMode,
  type ModeEligibility,
  type ModeTransitionEntry,
} from "@/lib/api";

const MODE_COLORS: Record<string, string> = {
  OBSERVE: "bg-gray-500/10 text-gray-400 border-gray-500/30",
  ASSISTED: "bg-blue-500/10 text-blue-400 border-blue-500/30",
  AUTONOMOUS: "bg-purple-500/10 text-purple-400 border-purple-500/30",
};

function ModeBadge({ mode }: { mode: string }) {
  const color = MODE_COLORS[mode] ?? "bg-gray-500/10 text-gray-400";
  return (
    <span className={`inline-flex items-center rounded-full border px-3 py-1 text-xs font-medium ${color}`}>
      {mode}
    </span>
  );
}

function ConfidenceMeter({ confidence, thresholds }: { confidence: number; thresholds: { assisted: number; autonomous: number } }) {
  const pct = Math.min(100, Math.max(0, confidence * 100));
  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between text-xs text-muted-foreground">
        <span>Baseline Confidence</span>
        <span className="font-mono">{confidence.toFixed(4)}</span>
      </div>
      <div className="relative h-3 w-full rounded-full bg-muted/50 overflow-hidden">
        <div
          className="absolute inset-y-0 left-0 rounded-full bg-asahio transition-all duration-500"
          style={{ width: `${pct}%` }}
        />
        {/* Threshold markers */}
        <div
          className="absolute inset-y-0 w-px bg-yellow-400"
          style={{ left: `${thresholds.assisted * 100}%` }}
          title={`ASSISTED threshold: ${thresholds.assisted}`}
        />
        <div
          className="absolute inset-y-0 w-px bg-purple-400"
          style={{ left: `${thresholds.autonomous * 100}%` }}
          title={`AUTONOMOUS threshold: ${thresholds.autonomous}`}
        />
      </div>
      <div className="flex justify-between text-[10px] text-muted-foreground">
        <span>0.0</span>
        <span className="text-yellow-400">{thresholds.assisted} (ASSISTED)</span>
        <span className="text-purple-400">{thresholds.autonomous} (AUTONOMOUS)</span>
        <span>1.0</span>
      </div>
    </div>
  );
}

export default function AgentDetailPage() {
  const params = useParams();
  const router = useRouter();
  const queryClient = useQueryClient();
  const orgSlug = typeof params?.orgSlug === "string" ? params.orgSlug : "";
  const agentId = typeof params?.agentId === "string" ? params.agentId : "";
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [targetMode, setTargetMode] = useState<string | null>(null);

  const { data: eligibility, isLoading: eligLoading } = useQuery({
    queryKey: ["mode-eligibility", orgSlug, agentId],
    queryFn: () => getModeEligibility(agentId, undefined, orgSlug),
    enabled: !!orgSlug && !!agentId,
  });

  const { data: history, isLoading: histLoading } = useQuery({
    queryKey: ["mode-history", orgSlug, agentId],
    queryFn: () => getModeHistory(agentId, { limit: 20 }, undefined, orgSlug),
    enabled: !!orgSlug && !!agentId,
  });

  const transitionMutation = useMutation({
    mutationFn: (data: { target_mode: string; operator_authorized: boolean }) =>
      transitionMode(agentId, data, undefined, orgSlug),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["mode-eligibility", orgSlug, agentId] });
      queryClient.invalidateQueries({ queryKey: ["mode-history", orgSlug, agentId] });
      setShowAuthModal(false);
      setTargetMode(null);
    },
  });

  const currentMode = eligibility?.current_mode ?? "OBSERVE";
  const confidence = (eligibility?.evidence?.baseline_confidence as number) ?? 0;
  const transitions = history?.data ?? [];

  const handleTransition = (mode: string) => {
    if (mode === "AUTONOMOUS") {
      setTargetMode(mode);
      setShowAuthModal(true);
    } else {
      transitionMutation.mutate({ target_mode: mode, operator_authorized: false });
    }
  };

  const confirmAutonomous = () => {
    if (targetMode) {
      transitionMutation.mutate({ target_mode: targetMode, operator_authorized: true });
    }
  };

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Link
          href={`/${orgSlug}/agents`}
          className="flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
        >
          <ArrowLeft className="h-4 w-4" />
          Agents
        </Link>
      </div>

      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground flex items-center gap-2">
            <Bot className="h-6 w-6 text-asahio" />
            Agent Detail
          </h1>
          <p className="text-sm text-muted-foreground mt-1 font-mono">{agentId}</p>
        </div>
        <ModeBadge mode={currentMode} />
      </div>

      {/* Eligibility Banner */}
      {eligibility?.eligible && (
        <div className="rounded-lg border border-asahio/30 bg-asahio/5 p-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <CheckCircle2 className="h-5 w-5 text-asahio" />
            <div>
              <p className="text-sm font-medium text-foreground">
                Upgrade to {eligibility.suggested_mode} available
              </p>
              <p className="text-xs text-muted-foreground">{eligibility.reason}</p>
            </div>
          </div>
          <button
            onClick={() => handleTransition(eligibility.suggested_mode!)}
            disabled={transitionMutation.isPending}
            className="rounded-md bg-asahio px-4 py-2 text-sm font-medium text-white hover:bg-asahio/90 disabled:opacity-50"
          >
            {transitionMutation.isPending ? "Transitioning..." : `Upgrade to ${eligibility.suggested_mode}`}
          </button>
        </div>
      )}

      {/* Confidence Meter */}
      <div className="rounded-lg border border-border bg-card p-6">
        <h2 className="text-lg font-semibold text-foreground mb-4 flex items-center gap-2">
          <Shield className="h-5 w-5" />
          Baseline Confidence
        </h2>
        <ConfidenceMeter
          confidence={confidence}
          thresholds={{ assisted: 0.65, autonomous: 0.82 }}
        />
        {!eligibility?.eligible && eligibility?.reason && (
          <p className="mt-3 text-xs text-muted-foreground flex items-center gap-1">
            <XCircle className="h-3 w-3" />
            {eligibility.reason}
          </p>
        )}
      </div>

      {/* Mode Switcher */}
      <div className="rounded-lg border border-border bg-card p-6">
        <h2 className="text-lg font-semibold text-foreground mb-4">Mode Control</h2>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          {(["OBSERVE", "ASSISTED", "AUTONOMOUS"] as const).map((mode) => {
            const isCurrent = currentMode === mode;
            return (
              <button
                key={mode}
                disabled={isCurrent || transitionMutation.isPending}
                onClick={() => handleTransition(mode)}
                className={`rounded-lg border p-4 text-left transition-all ${
                  isCurrent
                    ? "border-asahio bg-asahio/10"
                    : "border-border hover:border-asahio/50 hover:bg-muted/30"
                } disabled:cursor-not-allowed`}
              >
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-foreground">{mode}</span>
                  {isCurrent && (
                    <span className="text-xs text-asahio font-medium">Current</span>
                  )}
                </div>
                <p className="text-xs text-muted-foreground mt-1">
                  {mode === "OBSERVE" && "Watch only, never modify calls"}
                  {mode === "ASSISTED" && "Cache hits, augment, reroute on high risk"}
                  {mode === "AUTONOMOUS" && "Full intervention including blocking"}
                </p>
              </button>
            );
          })}
        </div>
      </div>

      {/* Mode History */}
      <div className="rounded-lg border border-border bg-card">
        <div className="p-6 border-b border-border">
          <h2 className="text-lg font-semibold text-foreground flex items-center gap-2">
            <Clock className="h-5 w-5" />
            Mode History
          </h2>
        </div>
        <div className="divide-y divide-border/50">
          {transitions.map((t) => (
            <div key={t.id} className="px-6 py-4 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <ModeBadge mode={t.previous_mode} />
                <GitBranch className="h-4 w-4 text-muted-foreground" />
                <ModeBadge mode={t.new_mode} />
              </div>
              <div className="text-right">
                <p className="text-xs text-muted-foreground">{t.trigger}</p>
                {t.baseline_confidence != null && (
                  <p className="text-xs text-muted-foreground">
                    Confidence: {t.baseline_confidence.toFixed(4)}
                  </p>
                )}
                <p className="text-xs text-muted-foreground">
                  {t.created_at ? new Date(t.created_at).toLocaleString() : ""}
                </p>
              </div>
            </div>
          ))}
          {transitions.length === 0 && !histLoading && (
            <div className="px-6 py-8 text-center text-muted-foreground text-sm">
              No mode transitions recorded yet.
            </div>
          )}
        </div>
      </div>

      {/* Autonomous Authorization Modal */}
      {showAuthModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="rounded-lg border border-border bg-card p-6 max-w-md w-full mx-4 shadow-xl">
            <div className="flex items-center gap-3 mb-4">
              <ShieldAlert className="h-6 w-6 text-red-400" />
              <h3 className="text-lg font-semibold text-foreground">
                Authorize AUTONOMOUS Mode
              </h3>
            </div>
            <p className="text-sm text-muted-foreground mb-4">
              AUTONOMOUS mode allows ASAHIO to <strong>block requests</strong> that exceed
              the risk threshold. This action requires explicit operator authorization.
            </p>
            <div className="rounded-md border border-border bg-muted/50 p-3 mb-4">
              <p className="text-xs text-muted-foreground">
                Baseline confidence: <span className="font-mono">{confidence.toFixed(4)}</span>
              </p>
              <p className="text-xs text-muted-foreground">
                Current mode: <span className="font-medium">{currentMode}</span>
              </p>
            </div>
            <div className="flex gap-3 justify-end">
              <button
                onClick={() => setShowAuthModal(false)}
                className="rounded-md border border-border px-4 py-2 text-sm text-muted-foreground hover:bg-muted"
              >
                Cancel
              </button>
              <button
                onClick={confirmAutonomous}
                disabled={transitionMutation.isPending}
                className="rounded-md bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700 disabled:opacity-50"
              >
                {transitionMutation.isPending ? "Authorizing..." : "Authorize AUTONOMOUS"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
