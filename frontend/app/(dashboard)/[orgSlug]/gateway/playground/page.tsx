"use client";

import { type ComponentType, useMemo, useState } from "react";
import { useParams } from "next/navigation";
import { useMutation } from "@tanstack/react-query";
import { chatCompletions, getCompletionMetadata } from "@/lib/api";
import type { ChatCompletionResponse } from "@/lib/api";
import { cn, formatCurrency } from "@/lib/utils";
import {
  ChevronDown,
  Clock,
  Cpu,
  Database,
  DollarSign,
  Loader2,
  Play,
  Shield,
  Sparkles,
  TrendingDown,
} from "lucide-react";

const ROUTING_MODES = ["AUTO", "GUIDED", "EXPLICIT"] as const;
const INTERVENTION_MODES = ["OBSERVE", "ASSISTED", "AUTONOMOUS"] as const;

const MODE_DESCRIPTIONS: Record<string, string> = {
  AUTO: "ASAHIO picks the best route for the task, cost target, and available cache state.",
  GUIDED: "You constrain quality and latency. ASAHIO still decides the final provider and model.",
  EXPLICIT: "You pin the model while still collecting observability, cost, and policy metadata.",
};

const QUALITY_OPTIONS = [
  { label: "Economy", value: "low" },
  { label: "Balanced", value: "medium" },
  { label: "High", value: "high" },
  { label: "Max", value: "max" },
] as const;

const LATENCY_OPTIONS = [
  { label: "Relaxed", value: "slow" },
  { label: "Normal", value: "normal" },
  { label: "Fast", value: "fast" },
  { label: "Instant", value: "instant" },
] as const;

const AVAILABLE_MODELS = [
  { id: "gpt-4o", label: "GPT-4o", provider: "OpenAI" },
  { id: "claude-opus-4", label: "Claude Opus 4", provider: "Anthropic" },
  { id: "claude-3-5-sonnet", label: "Claude 3.5 Sonnet", provider: "Anthropic" },
];

export default function PlaygroundPage() {
  const params = useParams();
  const orgSlug = typeof params?.orgSlug === "string" ? params.orgSlug : undefined;

  const [routingMode, setRoutingMode] = useState<string>("AUTO");
  const [interventionMode, setInterventionMode] = useState<string>("OBSERVE");
  const [qualityIndex, setQualityIndex] = useState(1);
  const [latencyIndex, setLatencyIndex] = useState(1);
  const [selectedModel, setSelectedModel] = useState(AVAILABLE_MODELS[0].id);
  const [message, setMessage] = useState("");
  const [result, setResult] = useState<ChatCompletionResponse | null>(null);

  const metadata = useMemo(
    () => (result ? getCompletionMetadata(result) : null),
    [result]
  );

  const mutation = useMutation({
    mutationFn: (userMessage: string) =>
      chatCompletions(
        {
          messages: [{ role: "user", content: userMessage }],
          routing_mode: routingMode,
          intervention_mode: interventionMode,
          quality_preference: QUALITY_OPTIONS[qualityIndex].value,
          latency_preference: LATENCY_OPTIONS[latencyIndex].value,
          ...(routingMode === "EXPLICIT" ? { model: selectedModel } : {}),
        },
        undefined,
        orgSlug
      ),
    onSuccess: (data) => setResult(data),
  });

  const handleRun = () => {
    if (!message.trim()) return;
    mutation.mutate(message.trim());
  };

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Playground</h1>
        <p className="text-sm text-muted-foreground">
          Exercise the canonical ASAHIO gateway contract and inspect cost, routing, cache, and policy metadata.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="space-y-4">
          <div className="rounded-lg border border-border bg-card p-4">
            <label className="mb-3 block text-sm font-medium text-foreground">Routing Mode</label>
            <div className="grid grid-cols-3 gap-2">
              {ROUTING_MODES.map((mode) => (
                <button
                  key={mode}
                  onClick={() => setRoutingMode(mode)}
                  className={cn(
                    "rounded-md px-3 py-2 text-sm font-medium transition-colors",
                    routingMode === mode
                      ? "bg-asahio text-white"
                      : "border border-border bg-background text-muted-foreground hover:text-foreground"
                  )}
                >
                  {mode}
                </button>
              ))}
            </div>
            <p className="mt-2 text-xs text-muted-foreground">{MODE_DESCRIPTIONS[routingMode]}</p>
          </div>

          <div className="rounded-lg border border-border bg-card p-4">
            <label className="mb-3 block text-sm font-medium text-foreground">Intervention Mode</label>
            <div className="relative">
              <select
                value={interventionMode}
                onChange={(e) => setInterventionMode(e.target.value)}
                className="w-full appearance-none rounded-md border border-border bg-background px-4 py-2.5 pr-10 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-asahio"
              >
                {INTERVENTION_MODES.map((mode) => (
                  <option key={mode} value={mode}>
                    {mode}
                  </option>
                ))}
              </select>
              <ChevronDown className="pointer-events-none absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            </div>
          </div>

          {routingMode === "EXPLICIT" && (
            <div className="rounded-lg border border-border bg-card p-4">
              <label className="mb-3 block text-sm font-medium text-foreground">Model</label>
              <div className="relative">
                <select
                  value={selectedModel}
                  onChange={(e) => setSelectedModel(e.target.value)}
                  className="w-full appearance-none rounded-md border border-border bg-background px-4 py-2.5 pr-10 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-asahio"
                >
                  {AVAILABLE_MODELS.map((model) => (
                    <option key={model.id} value={model.id}>
                      {model.label} ({model.provider})
                    </option>
                  ))}
                </select>
                <ChevronDown className="pointer-events-none absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              </div>
            </div>
          )}

          {routingMode !== "EXPLICIT" && (
            <>
              <div className="rounded-lg border border-border bg-card p-4">
                <label className="mb-3 block text-sm font-medium text-foreground">Quality Preference</label>
                <input
                  type="range"
                  min={0}
                  max={3}
                  step={1}
                  value={qualityIndex}
                  onChange={(e) => setQualityIndex(Number(e.target.value))}
                  className="w-full accent-asahio"
                />
                <div className="mt-2 flex justify-between text-xs text-muted-foreground">
                  {QUALITY_OPTIONS.map((option, index) => (
                    <span key={option.value} className={cn(qualityIndex === index && "font-medium text-asahio")}>
                      {option.label}
                    </span>
                  ))}
                </div>
              </div>

              <div className="rounded-lg border border-border bg-card p-4">
                <label className="mb-3 block text-sm font-medium text-foreground">Latency Preference</label>
                <input
                  type="range"
                  min={0}
                  max={3}
                  step={1}
                  value={latencyIndex}
                  onChange={(e) => setLatencyIndex(Number(e.target.value))}
                  className="w-full accent-asahio"
                />
                <div className="mt-2 flex justify-between text-xs text-muted-foreground">
                  {LATENCY_OPTIONS.map((option, index) => (
                    <span key={option.value} className={cn(latencyIndex === index && "font-medium text-asahio")}>
                      {option.label}
                    </span>
                  ))}
                </div>
              </div>
            </>
          )}

          <div className="rounded-lg border border-border bg-card p-4">
            <label className="mb-3 block text-sm font-medium text-foreground">Message</label>
            <textarea
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder="Describe the task you want the agent control plane to handle..."
              rows={7}
              className="w-full resize-none rounded-md border border-border bg-background px-4 py-3 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-asahio"
              onKeyDown={(e) => {
                if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) handleRun();
              }}
            />
          </div>

          <button
            onClick={handleRun}
            disabled={!message.trim() || mutation.isPending}
            className="inline-flex w-full items-center justify-center gap-2 rounded-md bg-asahio px-4 py-3 text-sm font-medium text-white transition-colors hover:bg-asahio-dark disabled:opacity-50"
          >
            {mutation.isPending ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Running...
              </>
            ) : (
              <>
                <Play className="h-4 w-4" />
                Run Inference
              </>
            )}
          </button>
        </div>

        <div className="space-y-4">
          <div className="rounded-lg border border-border bg-card p-4">
            <h3 className="mb-3 text-sm font-medium text-foreground">Response</h3>
            {mutation.isPending ? (
              <div className="animate-pulse space-y-3">
                <div className="h-4 w-3/4 rounded bg-muted" />
                <div className="h-4 w-full rounded bg-muted" />
                <div className="h-4 w-5/6 rounded bg-muted" />
                <div className="h-4 w-2/3 rounded bg-muted" />
              </div>
            ) : mutation.isError ? (
              <div className="rounded-md border border-red-500/30 bg-red-500/10 p-4">
                <p className="text-sm font-medium text-red-400">Request failed</p>
                <p className="mt-1 break-words text-sm text-red-300/90">
                  {mutation.error instanceof Error ? mutation.error.message : "An error occurred"}
                </p>
              </div>
            ) : result ? (
              <div className="whitespace-pre-wrap text-sm leading-relaxed text-foreground">
                {result.choices[0]?.message.content || "No response content"}
              </div>
            ) : (
              <div className="flex h-48 items-center justify-center text-sm text-muted-foreground">
                Run a request to inspect the control-plane response.
              </div>
            )}
          </div>

          {result && metadata && (
            <div className="grid grid-cols-2 gap-3">
              <MetricCard icon={Cpu} label="Model Used" value={metadata.model_used} mono />
              <MetricCard icon={Database} label="Cache Tier" value={metadata.cache_hit ? metadata.cache_tier || "hit" : "miss"} />
              <MetricCard icon={DollarSign} label="Cost With ASAHIO" value={formatCurrency(metadata.cost_with_asahio)} subtitle={`vs ${formatCurrency(metadata.cost_without_asahio)} baseline`} />
              <MetricCard icon={TrendingDown} label="Savings" value={`${formatCurrency(metadata.savings_usd)} (${metadata.savings_pct.toFixed(0)}%)`} highlight />
              <MetricCard icon={Clock} label="Tokens" value={result.usage.total_tokens.toLocaleString()} subtitle={`${result.usage.prompt_tokens} in / ${result.usage.completion_tokens} out`} />
              <MetricCard icon={Shield} label="Policy" value={metadata.policy_action || metadata.intervention_mode || "OBSERVE"} subtitle={metadata.policy_reason || metadata.routing_reason || "No policy note"} />
              <MetricCard icon={Sparkles} label="Routing" value={metadata.routing_mode || routingMode} subtitle={metadata.routing_reason || MODE_DESCRIPTIONS[routingMode]} />
              <MetricCard icon={Shield} label="Request ID" value={metadata.request_id || "pending"} mono />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function MetricCard({
  icon: Icon,
  label,
  value,
  subtitle,
  highlight,
  mono,
}: {
  icon: ComponentType<{ className?: string }>;
  label: string;
  value: string;
  subtitle?: string;
  highlight?: boolean;
  mono?: boolean;
}) {
  return (
    <div className="rounded-lg border border-border bg-card p-4">
      <div className="flex items-center gap-2 text-xs text-muted-foreground">
        <Icon className="h-3.5 w-3.5" />
        {label}
      </div>
      <p className={cn("mt-1 text-sm font-medium text-foreground", highlight && "text-green-400", mono && "font-mono text-xs")}>{value}</p>
      {subtitle && <p className="mt-1 text-xs text-muted-foreground">{subtitle}</p>}
    </div>
  );
}

