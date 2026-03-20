"use client";

import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import {
  createConstraint,
  dryRunRule,
  type RoutingConstraintItem,
} from "@/lib/api";
import {
  Layers,
  Clock,
  GitBranch,
  DollarSign,
  ListFilter,
  Server,
  Play,
  Plus,
  X,
  Trash2,
  AlertCircle,
  CheckCircle,
} from "lucide-react";
import { cn } from "@/lib/utils";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

type RuleType =
  | "step_based"
  | "time_based"
  | "fallback_chain"
  | "cost_ceiling_per_1k"
  | "model_allowlist"
  | "provider_restriction";

interface RuleTypeOption {
  type: RuleType;
  label: string;
  description: string;
  icon: typeof Layers;
}

const RULE_TYPES: RuleTypeOption[] = [
  {
    type: "step_based",
    label: "Step-Based",
    description: "Route to different models based on the conversation step number",
    icon: Layers,
  },
  {
    type: "time_based",
    label: "Time-Based",
    description: "Route to different models based on the time of day (UTC)",
    icon: Clock,
  },
  {
    type: "fallback_chain",
    label: "Fallback Chain",
    description: "Try models in order — if one fails, fall back to the next",
    icon: GitBranch,
  },
  {
    type: "cost_ceiling_per_1k",
    label: "Cost Ceiling",
    description: "Set a maximum cost per 1,000 tokens for model selection",
    icon: DollarSign,
  },
  {
    type: "model_allowlist",
    label: "Model Allowlist",
    description: "Restrict routing to only approved models",
    icon: ListFilter,
  },
  {
    type: "provider_restriction",
    label: "Provider Restriction",
    description: "Restrict routing to a specific provider",
    icon: Server,
  },
];

const AVAILABLE_MODELS = [
  "gpt-4o",
  "gpt-4o-mini",
  "gpt-4-turbo",
  "gpt-3.5-turbo",
  "claude-3-5-sonnet-20241022",
  "claude-3-5-haiku-20241022",
  "claude-3-opus-20240229",
  "gemini-1.5-pro",
  "gemini-1.5-flash",
  "deepseek-chat",
  "mistral-large-latest",
  "mistral-small-latest",
];

const AVAILABLE_PROVIDERS = [
  "openai",
  "anthropic",
  "google",
  "deepseek",
  "mistral",
  "ollama",
];

// ---------------------------------------------------------------------------
// Sub-editors per rule type
// ---------------------------------------------------------------------------

function StepBasedEditor({
  config,
  onChange,
}: {
  config: Record<string, unknown>;
  onChange: (c: Record<string, unknown>) => void;
}) {
  const rules = (config.rules as Array<{ step: number; model: string }>) ?? [];

  const addRow = () =>
    onChange({ rules: [...rules, { step: rules.length + 1, model: AVAILABLE_MODELS[0] }] });
  const removeRow = (idx: number) =>
    onChange({ rules: rules.filter((_, i) => i !== idx) });
  const updateRow = (idx: number, field: string, value: unknown) =>
    onChange({ rules: rules.map((r, i) => (i === idx ? { ...r, [field]: value } : r)) });

  return (
    <div className="space-y-3">
      <p className="text-xs text-muted-foreground">
        Map conversation step numbers to specific models.
      </p>
      {rules.map((r, idx) => (
        <div key={idx} className="flex items-center gap-2">
          <label className="text-xs text-muted-foreground w-12">Step</label>
          <input
            type="number"
            min={1}
            value={r.step}
            onChange={(e) => updateRow(idx, "step", parseInt(e.target.value) || 1)}
            className="w-20 rounded-md border border-border bg-background px-2 py-1.5 text-sm"
          />
          <label className="text-xs text-muted-foreground w-12 ml-2">Model</label>
          <select
            value={r.model}
            onChange={(e) => updateRow(idx, "model", e.target.value)}
            className="flex-1 rounded-md border border-border bg-background px-2 py-1.5 text-sm"
          >
            {AVAILABLE_MODELS.map((m) => (
              <option key={m} value={m}>{m}</option>
            ))}
          </select>
          <button
            type="button"
            onClick={() => removeRow(idx)}
            className="rounded p-1 text-muted-foreground hover:text-red-400"
          >
            <Trash2 className="h-3.5 w-3.5" />
          </button>
        </div>
      ))}
      <button
        type="button"
        onClick={addRow}
        className="flex items-center gap-1 text-xs text-asahio hover:underline"
      >
        <Plus className="h-3 w-3" /> Add step rule
      </button>
    </div>
  );
}

function TimeBasedEditor({
  config,
  onChange,
}: {
  config: Record<string, unknown>;
  onChange: (c: Record<string, unknown>) => void;
}) {
  const rules = (config.rules as Array<{ hours: string; model: string }>) ?? [];

  const addRow = () =>
    onChange({ rules: [...rules, { hours: "0-8", model: AVAILABLE_MODELS[0] }] });
  const removeRow = (idx: number) =>
    onChange({ rules: rules.filter((_, i) => i !== idx) });
  const updateRow = (idx: number, field: string, value: string) =>
    onChange({ rules: rules.map((r, i) => (i === idx ? { ...r, [field]: value } : r)) });

  return (
    <div className="space-y-3">
      <p className="text-xs text-muted-foreground">
        Route to different models based on time of day (UTC, 24h format &quot;start-end&quot;).
      </p>
      {rules.map((r, idx) => (
        <div key={idx} className="flex items-center gap-2">
          <label className="text-xs text-muted-foreground w-12">Hours</label>
          <input
            type="text"
            placeholder="0-8"
            value={r.hours}
            onChange={(e) => updateRow(idx, "hours", e.target.value)}
            className="w-24 rounded-md border border-border bg-background px-2 py-1.5 text-sm font-mono"
          />
          <label className="text-xs text-muted-foreground w-12 ml-2">Model</label>
          <select
            value={r.model}
            onChange={(e) => updateRow(idx, "model", e.target.value)}
            className="flex-1 rounded-md border border-border bg-background px-2 py-1.5 text-sm"
          >
            {AVAILABLE_MODELS.map((m) => (
              <option key={m} value={m}>{m}</option>
            ))}
          </select>
          <button
            type="button"
            onClick={() => removeRow(idx)}
            className="rounded p-1 text-muted-foreground hover:text-red-400"
          >
            <Trash2 className="h-3.5 w-3.5" />
          </button>
        </div>
      ))}
      <button
        type="button"
        onClick={addRow}
        className="flex items-center gap-1 text-xs text-asahio hover:underline"
      >
        <Plus className="h-3 w-3" /> Add time rule
      </button>
    </div>
  );
}

function FallbackChainEditor({
  config,
  onChange,
}: {
  config: Record<string, unknown>;
  onChange: (c: Record<string, unknown>) => void;
}) {
  const chain = (config.chain as string[]) ?? [];

  const addModel = () =>
    onChange({
      chain: [...chain, AVAILABLE_MODELS.find((m) => !chain.includes(m)) ?? AVAILABLE_MODELS[0]],
    });
  const removeModel = (idx: number) =>
    onChange({ chain: chain.filter((_, i) => i !== idx) });
  const updateModel = (idx: number, value: string) =>
    onChange({ chain: chain.map((m, i) => (i === idx ? value : m)) });

  return (
    <div className="space-y-3">
      <p className="text-xs text-muted-foreground">
        Models are tried in order. If the first fails or is unavailable, the next is used.
      </p>
      {chain.map((model, idx) => (
        <div key={idx} className="flex items-center gap-2">
          <span className="flex h-5 w-5 items-center justify-center rounded-full bg-muted text-[10px] font-bold text-muted-foreground">
            {idx + 1}
          </span>
          <select
            value={model}
            onChange={(e) => updateModel(idx, e.target.value)}
            className="flex-1 rounded-md border border-border bg-background px-2 py-1.5 text-sm"
          >
            {AVAILABLE_MODELS.map((m) => (
              <option key={m} value={m}>{m}</option>
            ))}
          </select>
          <button
            type="button"
            onClick={() => removeModel(idx)}
            className="rounded p-1 text-muted-foreground hover:text-red-400"
          >
            <Trash2 className="h-3.5 w-3.5" />
          </button>
        </div>
      ))}
      <button
        type="button"
        onClick={addModel}
        className="flex items-center gap-1 text-xs text-asahio hover:underline"
      >
        <Plus className="h-3 w-3" /> Add fallback model
      </button>
    </div>
  );
}

function CostCeilingEditor({
  config,
  onChange,
}: {
  config: Record<string, unknown>;
  onChange: (c: Record<string, unknown>) => void;
}) {
  const value = (config.value as number) ?? 0.01;

  return (
    <div className="space-y-3">
      <p className="text-xs text-muted-foreground">
        Maximum cost per 1,000 tokens. Models exceeding this cost will be excluded.
      </p>
      <div className="flex items-center gap-2">
        <label className="text-xs text-muted-foreground">$ per 1K tokens</label>
        <input
          type="number"
          step="0.001"
          min="0.001"
          value={value}
          onChange={(e) => onChange({ value: parseFloat(e.target.value) || 0.001 })}
          className="w-32 rounded-md border border-border bg-background px-2 py-1.5 text-sm font-mono"
        />
      </div>
    </div>
  );
}

function AllowlistEditor({
  config,
  onChange,
}: {
  config: Record<string, unknown>;
  onChange: (c: Record<string, unknown>) => void;
}) {
  const models = (config.models as string[]) ?? [];

  const toggle = (model: string) => {
    if (models.includes(model)) {
      onChange({ models: models.filter((m) => m !== model) });
    } else {
      onChange({ models: [...models, model] });
    }
  };

  return (
    <div className="space-y-3">
      <p className="text-xs text-muted-foreground">
        Only these models will be considered during routing.
      </p>
      <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
        {AVAILABLE_MODELS.map((model) => (
          <label
            key={model}
            className={cn(
              "flex cursor-pointer items-center gap-2 rounded-md border px-3 py-2 text-xs transition-colors",
              models.includes(model)
                ? "border-asahio bg-asahio/10 text-asahio"
                : "border-border text-muted-foreground hover:border-asahio/50"
            )}
          >
            <input
              type="checkbox"
              checked={models.includes(model)}
              onChange={() => toggle(model)}
              className="sr-only"
            />
            <span className={cn("h-3 w-3 rounded-sm border", models.includes(model) ? "border-asahio bg-asahio" : "border-border")} />
            {model}
          </label>
        ))}
      </div>
    </div>
  );
}

function ProviderRestrictionEditor({
  config,
  onChange,
}: {
  config: Record<string, unknown>;
  onChange: (c: Record<string, unknown>) => void;
}) {
  const provider = (config.provider as string) ?? "";

  return (
    <div className="space-y-3">
      <p className="text-xs text-muted-foreground">
        Restrict routing to only use models from this provider.
      </p>
      <select
        value={provider}
        onChange={(e) => onChange({ provider: e.target.value })}
        className="w-48 rounded-md border border-border bg-background px-2 py-1.5 text-sm"
      >
        <option value="">Select provider...</option>
        {AVAILABLE_PROVIDERS.map((p) => (
          <option key={p} value={p}>{p}</option>
        ))}
      </select>
    </div>
  );
}

const EDITORS: Record<RuleType, React.ComponentType<{ config: Record<string, unknown>; onChange: (c: Record<string, unknown>) => void }>> = {
  step_based: StepBasedEditor,
  time_based: TimeBasedEditor,
  fallback_chain: FallbackChainEditor,
  cost_ceiling_per_1k: CostCeilingEditor,
  model_allowlist: AllowlistEditor,
  provider_restriction: ProviderRestrictionEditor,
};

const DEFAULT_CONFIGS: Record<RuleType, Record<string, unknown>> = {
  step_based: { rules: [{ step: 1, model: "gpt-4o-mini" }, { step: 3, model: "gpt-4o" }] },
  time_based: { rules: [{ hours: "0-8", model: "gpt-4o-mini" }, { hours: "9-17", model: "gpt-4o" }, { hours: "18-23", model: "gpt-4o-mini" }] },
  fallback_chain: { chain: ["gpt-4o", "gpt-4o-mini"] },
  cost_ceiling_per_1k: { value: 0.01 },
  model_allowlist: { models: ["gpt-4o", "gpt-4o-mini"] },
  provider_restriction: { provider: "openai" },
};

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

interface VisualRuleBuilderProps {
  orgSlug: string;
  existingConstraints: RoutingConstraintItem[];
}

export function VisualRuleBuilder({ orgSlug, existingConstraints }: VisualRuleBuilderProps) {
  const queryClient = useQueryClient();
  const [selectedType, setSelectedType] = useState<RuleType | null>(null);
  const [config, setConfig] = useState<Record<string, unknown>>({});
  const [dryRunResult, setDryRunResult] = useState<{
    selected_model?: string;
    provider?: string;
    reason?: string;
    validation_errors?: string[];
  } | null>(null);
  const [dryRunError, setDryRunError] = useState<string | null>(null);
  const [samplePrompt, setSamplePrompt] = useState("What is machine learning?");

  const createMutation = useMutation({
    mutationFn: (body: Parameters<typeof createConstraint>[0]) =>
      createConstraint(body, undefined, orgSlug),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["constraints", orgSlug] });
      setSelectedType(null);
      setConfig({});
      setDryRunResult(null);
    },
  });

  const dryRunMutation = useMutation({
    mutationFn: () =>
      dryRunRule(
        { rule_type: selectedType!, rule_config: config, sample_prompt: samplePrompt },
        undefined,
        orgSlug
      ),
    onSuccess: (data) => {
      setDryRunResult(data);
      setDryRunError(null);
    },
    onError: (err: Error) => {
      setDryRunError(err.message);
      setDryRunResult(null);
    },
  });

  const selectType = (type: RuleType) => {
    setSelectedType(type);
    setConfig(DEFAULT_CONFIGS[type]);
    setDryRunResult(null);
    setDryRunError(null);
  };

  const Editor = selectedType ? EDITORS[selectedType] : null;

  return (
    <div className="space-y-6">
      {/* Existing constraints */}
      {existingConstraints.length > 0 && (
        <div className="space-y-2">
          <h3 className="text-sm font-medium text-foreground">Active Rules</h3>
          <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
            {existingConstraints.map((c) => {
              const typeDef = RULE_TYPES.find((t) => t.type === c.rule_type);
              const Icon = typeDef?.icon ?? Layers;
              return (
                <div
                  key={c.id}
                  className="flex items-start gap-3 rounded-lg border border-border p-3"
                >
                  <Icon className="mt-0.5 h-4 w-4 text-asahio" />
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-medium text-foreground">
                      {typeDef?.label ?? c.rule_type}
                    </p>
                    <p className="truncate text-xs text-muted-foreground">
                      Priority: {c.priority} | {c.is_active ? "Active" : "Inactive"}
                    </p>
                    <pre className="mt-1 max-h-16 overflow-auto text-[10px] text-muted-foreground">
                      {JSON.stringify(c.rule_config, null, 2)}
                    </pre>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Rule type selector */}
      {!selectedType && (
        <div>
          <h3 className="mb-3 text-sm font-medium text-foreground">Add Routing Rule</h3>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {RULE_TYPES.map((rt) => (
              <button
                key={rt.type}
                type="button"
                onClick={() => selectType(rt.type)}
                className="flex items-start gap-3 rounded-lg border border-border p-4 text-left transition-colors hover:border-asahio hover:bg-asahio/5"
              >
                <rt.icon className="mt-0.5 h-5 w-5 text-asahio" />
                <div>
                  <p className="text-sm font-medium text-foreground">{rt.label}</p>
                  <p className="text-xs text-muted-foreground">{rt.description}</p>
                </div>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Rule editor */}
      {selectedType && Editor && (
        <div className="rounded-lg border border-border p-4 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-medium text-foreground">
              {RULE_TYPES.find((t) => t.type === selectedType)?.label}
            </h3>
            <button
              type="button"
              onClick={() => {
                setSelectedType(null);
                setConfig({});
                setDryRunResult(null);
              }}
              className="rounded p-1 text-muted-foreground hover:text-foreground"
            >
              <X className="h-4 w-4" />
            </button>
          </div>

          <Editor config={config} onChange={setConfig} />

          {/* Dry Run */}
          <div className="border-t border-border pt-4 space-y-3">
            <p className="text-xs font-medium text-muted-foreground">Test this rule (dry run)</p>
            <div className="flex items-center gap-2">
              <input
                type="text"
                value={samplePrompt}
                onChange={(e) => setSamplePrompt(e.target.value)}
                placeholder="Sample prompt..."
                className="flex-1 rounded-md border border-border bg-background px-2 py-1.5 text-sm"
              />
              <button
                type="button"
                onClick={() => dryRunMutation.mutate()}
                disabled={dryRunMutation.isPending}
                className="flex items-center gap-1 rounded-md bg-muted px-3 py-1.5 text-sm font-medium text-foreground transition-colors hover:bg-muted/80 disabled:opacity-50"
              >
                <Play className="h-3.5 w-3.5" />
                {dryRunMutation.isPending ? "Running..." : "Dry Run"}
              </button>
            </div>

            {dryRunResult && (
              <div className="rounded-md border border-border bg-muted/30 p-3 text-sm">
                {dryRunResult.validation_errors && dryRunResult.validation_errors.length > 0 ? (
                  <div className="flex items-start gap-2 text-red-400">
                    <AlertCircle className="mt-0.5 h-4 w-4 flex-shrink-0" />
                    <div>
                      <p className="font-medium">Validation errors:</p>
                      <ul className="mt-1 list-disc pl-4 text-xs">
                        {dryRunResult.validation_errors.map((e, i) => (
                          <li key={i}>{e}</li>
                        ))}
                      </ul>
                    </div>
                  </div>
                ) : (
                  <div className="flex items-start gap-2 text-emerald-400">
                    <CheckCircle className="mt-0.5 h-4 w-4 flex-shrink-0" />
                    <div>
                      <p>
                        <span className="font-medium">Model:</span>{" "}
                        <span className="font-mono">{dryRunResult.selected_model}</span>
                      </p>
                      <p>
                        <span className="font-medium">Provider:</span> {dryRunResult.provider}
                      </p>
                      <p className="text-xs text-muted-foreground mt-1">{dryRunResult.reason}</p>
                    </div>
                  </div>
                )}
              </div>
            )}

            {dryRunError && (
              <div className="flex items-start gap-2 rounded-md border border-red-500/30 bg-red-500/10 p-3 text-sm text-red-400">
                <AlertCircle className="mt-0.5 h-4 w-4 flex-shrink-0" />
                <p className="text-xs">{dryRunError}</p>
              </div>
            )}
          </div>

          {/* JSON preview + Save */}
          <div className="border-t border-border pt-4 space-y-3">
            <details className="text-xs">
              <summary className="cursor-pointer text-muted-foreground hover:text-foreground">
                View JSON config
              </summary>
              <pre className="mt-2 overflow-auto rounded-md border border-border bg-background p-3 text-[11px] text-muted-foreground">
                {JSON.stringify(config, null, 2)}
              </pre>
            </details>

            <div className="flex justify-end gap-2">
              <button
                type="button"
                onClick={() => {
                  setSelectedType(null);
                  setConfig({});
                }}
                className="rounded-md border border-border px-4 py-2 text-sm text-muted-foreground hover:text-foreground"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={() =>
                  createMutation.mutate({
                    rule_type: selectedType,
                    rule_config: config,
                  })
                }
                disabled={createMutation.isPending}
                className="rounded-md bg-asahio px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-asahio/90 disabled:opacity-50"
              >
                {createMutation.isPending ? "Saving..." : "Save Rule"}
              </button>
            </div>

            {createMutation.isError && (
              <p className="text-xs text-red-400">
                {(createMutation.error as Error).message}
              </p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
