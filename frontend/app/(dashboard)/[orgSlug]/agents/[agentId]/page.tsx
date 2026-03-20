"use client";

import { useCallback, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  ArrowLeft,
  Bot,
  CheckCircle2,
  Clock,
  FileBarChart,
  GitBranch,
  Shield,
  ShieldAlert,
  XCircle,
} from "lucide-react";
import Link from "next/link";
import {
  getABAFingerprint,
  getModeEligibility,
  getModeHistory,
  listAgents,
  transitionMode,
  updateAgent,
  type ABAFingerprint,
  type AgentItem,
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
  const [tab, setTab] = useState<"overview" | "evidence">("overview");

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

  const { data: fingerprint } = useQuery({
    queryKey: ["aba-fingerprint", orgSlug, agentId],
    queryFn: () => getABAFingerprint(agentId, undefined, orgSlug),
    enabled: !!orgSlug && !!agentId,
    retry: false,
  });

  const { data: agentsData } = useQuery({
    queryKey: ["agents", orgSlug],
    queryFn: () => listAgents(undefined, orgSlug),
    enabled: !!orgSlug,
  });
  const agent = agentsData?.data?.find((a) => a.id === agentId);

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

      {/* Tabs */}
      <div className="flex gap-1 border-b border-border">
        <button
          type="button"
          onClick={() => setTab("overview")}
          className={`flex items-center gap-2 border-b-2 px-4 py-2 text-sm font-medium transition-colors ${
            tab === "overview"
              ? "border-asahio text-asahio"
              : "border-transparent text-muted-foreground hover:text-foreground"
          }`}
        >
          <Shield className="h-4 w-4" />
          Mode Control
        </button>
        <button
          type="button"
          onClick={() => setTab("evidence")}
          className={`flex items-center gap-2 border-b-2 px-4 py-2 text-sm font-medium transition-colors ${
            tab === "evidence"
              ? "border-asahio text-asahio"
              : "border-transparent text-muted-foreground hover:text-foreground"
          }`}
        >
          <FileBarChart className="h-4 w-4" />
          Evidence
        </button>
      </div>

      {/* Evidence Tab */}
      {tab === "evidence" && (
        <EvidencePanel eligibility={eligibility} fingerprint={fingerprint} />
      )}

      {/* Overview Tab */}
      {tab === "overview" && (<>

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

      {/* Intervention Thresholds */}
      <ThresholdEditor agentId={agentId} orgSlug={orgSlug} agent={agent} />

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

      </>)}

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

// ---------------------------------------------------------------------------
// Intervention Threshold Editor (P1-4)
// ---------------------------------------------------------------------------

const DEFAULT_THRESHOLDS = { flag: 0.3, augment: 0.5, reroute: 0.7, block: 0.9 };
const THRESHOLD_KEYS = ["flag", "augment", "reroute", "block"] as const;
const THRESHOLD_COLORS: Record<string, string> = {
  flag: "accent-yellow-400",
  augment: "accent-blue-400",
  reroute: "accent-orange-400",
  block: "accent-red-400",
};
const THRESHOLD_LABELS: Record<string, string> = {
  flag: "Flag",
  augment: "Augment",
  reroute: "Reroute",
  block: "Block",
};

function ThresholdEditor({
  agentId,
  orgSlug,
  agent,
}: {
  agentId: string;
  orgSlug: string;
  agent?: AgentItem | null;
}) {
  const queryClient = useQueryClient();
  const overrides = agent?.risk_threshold_overrides ?? null;
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState<Record<string, number>>(
    overrides ?? { ...DEFAULT_THRESHOLDS }
  );
  const [saving, setSaving] = useState(false);

  const startEditing = useCallback(() => {
    setDraft(overrides ?? { ...DEFAULT_THRESHOLDS });
    setEditing(true);
  }, [overrides]);

  const save = async () => {
    setSaving(true);
    try {
      await updateAgent(agentId, { risk_threshold_overrides: draft }, undefined, orgSlug);
      queryClient.invalidateQueries({ queryKey: ["agents", orgSlug] });
      setEditing(false);
    } finally {
      setSaving(false);
    }
  };

  const reset = async () => {
    setSaving(true);
    try {
      await updateAgent(agentId, { risk_threshold_overrides: null as unknown as Record<string, number> }, undefined, orgSlug);
      queryClient.invalidateQueries({ queryKey: ["agents", orgSlug] });
      setEditing(false);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="rounded-lg border border-border bg-card p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-foreground flex items-center gap-2">
          <ShieldAlert className="h-5 w-5" />
          Intervention Thresholds
        </h2>
        {!editing && (
          <button
            onClick={startEditing}
            className="rounded-md border border-border px-3 py-1.5 text-xs font-medium text-muted-foreground hover:text-foreground transition-colors"
          >
            {overrides ? "Edit" : "Customize"}
          </button>
        )}
      </div>

      {overrides && !editing && (
        <p className="text-xs text-asahio mb-3">Custom thresholds active</p>
      )}
      {!overrides && !editing && (
        <p className="text-xs text-muted-foreground mb-3">Using default thresholds</p>
      )}

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {THRESHOLD_KEYS.map((key) => {
          const current = editing ? draft[key] : (overrides?.[key] ?? DEFAULT_THRESHOLDS[key]);
          const isCustom = overrides?.[key] != null && overrides[key] !== DEFAULT_THRESHOLDS[key];
          return (
            <div key={key} className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-muted-foreground">{THRESHOLD_LABELS[key]}</span>
                {isCustom && !editing && (
                  <span className="text-[10px] text-asahio">custom</span>
                )}
              </div>
              {editing ? (
                <div className="space-y-1">
                  <input
                    type="range"
                    min={0}
                    max={1}
                    step={0.01}
                    value={current ?? DEFAULT_THRESHOLDS[key]}
                    onChange={(e) =>
                      setDraft((prev) => ({ ...prev, [key]: parseFloat(e.target.value) }))
                    }
                    className={`w-full h-1.5 rounded-full appearance-none bg-muted cursor-pointer ${THRESHOLD_COLORS[key]}`}
                  />
                  <div className="flex items-center justify-between text-[10px] text-muted-foreground">
                    <span>0.0</span>
                    <span className="font-mono text-foreground">{(current ?? DEFAULT_THRESHOLDS[key]).toFixed(2)}</span>
                    <span>1.0</span>
                  </div>
                </div>
              ) : (
                <div className="relative h-2 w-full rounded-full bg-muted overflow-hidden">
                  <div
                    className={`absolute inset-y-0 left-0 rounded-full ${
                      key === "flag" ? "bg-yellow-400" :
                      key === "augment" ? "bg-blue-400" :
                      key === "reroute" ? "bg-orange-400" : "bg-red-400"
                    }`}
                    style={{ width: `${current * 100}%` }}
                  />
                </div>
              )}
              <p className="text-[10px] text-muted-foreground">
                {!editing && `${current.toFixed(2)}`}
                {!editing && ` (default: ${DEFAULT_THRESHOLDS[key]})`}
              </p>
            </div>
          );
        })}
      </div>

      {editing && (
        <div className="mt-4 flex items-center gap-2 border-t border-border pt-4">
          <button
            onClick={save}
            disabled={saving}
            className="rounded-md bg-asahio px-4 py-2 text-xs font-medium text-white hover:bg-asahio/90 disabled:opacity-50"
          >
            {saving ? "Saving..." : "Save Thresholds"}
          </button>
          {overrides && (
            <button
              onClick={reset}
              disabled={saving}
              className="rounded-md border border-red-500/50 bg-red-500/10 px-4 py-2 text-xs font-medium text-red-400 hover:bg-red-500/20 disabled:opacity-50"
            >
              Reset to Defaults
            </button>
          )}
          <button
            onClick={() => setEditing(false)}
            className="rounded-md border border-border px-4 py-2 text-xs font-medium text-muted-foreground hover:text-foreground"
          >
            Cancel
          </button>
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Evidence Panel (P1-2)
// ---------------------------------------------------------------------------

function EvidencePanel({
  eligibility,
  fingerprint,
}: {
  eligibility?: ModeEligibility | null;
  fingerprint?: ABAFingerprint | null;
}) {
  const evidence = eligibility?.evidence ?? {};

  return (
    <div className="space-y-4">
      {/* Eligibility Status */}
      <div className="rounded-lg border border-border bg-card p-6">
        <h2 className="text-sm font-semibold text-foreground mb-4">Mode Eligibility</h2>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <EvidenceStat label="Current Mode" value={eligibility?.current_mode ?? "-"} />
          <EvidenceStat label="Eligible for Upgrade" value={eligibility?.eligible ? "Yes" : "No"} highlight={eligibility?.eligible} />
          <EvidenceStat label="Suggested Mode" value={eligibility?.suggested_mode ?? "None"} />
          <EvidenceStat
            label="Baseline Confidence"
            value={typeof evidence.baseline_confidence === "number" ? `${(evidence.baseline_confidence * 100).toFixed(1)}%` : "-"}
          />
        </div>
        {eligibility?.reason && (
          <div className="mt-4 rounded-md border border-border bg-muted/30 px-4 py-3">
            <p className="text-xs text-muted-foreground">{eligibility.reason}</p>
          </div>
        )}
      </div>

      {/* Evidence Details */}
      {Object.keys(evidence).length > 0 && (
        <div className="rounded-lg border border-border bg-card p-6">
          <h2 className="text-sm font-semibold text-foreground mb-4">Evidence Data</h2>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {Object.entries(evidence).map(([key, value]) => (
              <div key={key} className="flex items-center justify-between rounded-md border border-border bg-muted/20 px-3 py-2">
                <span className="text-xs text-muted-foreground">{key.replace(/_/g, " ")}</span>
                <span className="text-xs font-mono text-foreground">
                  {typeof value === "number" ? value.toFixed(4) : String(value ?? "-")}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ABA Fingerprint */}
      {fingerprint && (
        <div className="rounded-lg border border-border bg-card p-6">
          <h2 className="text-sm font-semibold text-foreground mb-4">Behavioral Fingerprint</h2>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            <EvidenceStat label="Total Observations" value={fingerprint.total_observations.toLocaleString()} />
            <EvidenceStat label="Avg Complexity" value={fingerprint.avg_complexity.toFixed(3)} />
            <EvidenceStat label="Hallucination Rate" value={`${(fingerprint.hallucination_rate * 100).toFixed(1)}%`} highlight={fingerprint.hallucination_rate > 0.1} />
            <EvidenceStat label="Cache Hit Rate" value={`${(fingerprint.cache_hit_rate * 100).toFixed(1)}%`} />
            <EvidenceStat label="Avg Context Length" value={fingerprint.avg_context_length.toFixed(0)} />
            <EvidenceStat label="Models Used" value={Object.keys(fingerprint.model_distribution).length.toString()} />
          </div>

          {Object.keys(fingerprint.model_distribution).length > 0 && (
            <div className="mt-4">
              <h3 className="text-xs font-medium text-muted-foreground mb-2">Model Distribution</h3>
              <div className="space-y-1.5">
                {Object.entries(fingerprint.model_distribution)
                  .sort((a, b) => (b[1] as number) - (a[1] as number))
                  .map(([model, count]) => {
                    const pct = fingerprint.total_observations > 0 ? ((count as number) / fingerprint.total_observations) * 100 : 0;
                    return (
                      <div key={model} className="flex items-center gap-2">
                        <span className="w-40 truncate text-xs font-mono text-muted-foreground">{model}</span>
                        <div className="h-2 flex-1 overflow-hidden rounded-full bg-muted">
                          <div className="h-full rounded-full bg-asahio" style={{ width: `${pct}%` }} />
                        </div>
                        <span className="w-12 text-right text-[10px] text-muted-foreground">{count} ({pct.toFixed(0)}%)</span>
                      </div>
                    );
                  })}
              </div>
            </div>
          )}

          <p className="mt-3 text-[10px] text-muted-foreground">
            Last updated: {new Date(fingerprint.last_updated_at).toLocaleString()}
          </p>
        </div>
      )}

      {!fingerprint && (
        <div className="rounded-lg border border-dashed border-border p-8 text-center">
          <p className="text-sm text-muted-foreground">
            No behavioral fingerprint yet. Send requests through this agent to build a profile.
          </p>
        </div>
      )}
    </div>
  );
}

function EvidenceStat({ label, value, highlight }: { label: string; value: string; highlight?: boolean }) {
  return (
    <div className="space-y-1">
      <p className="text-[10px] uppercase tracking-wider text-muted-foreground">{label}</p>
      <p className={`text-sm font-medium ${highlight ? "text-asahio" : "text-foreground"}`}>{value}</p>
    </div>
  );
}
