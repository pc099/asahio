"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  listChains,
  createChain,
  deleteChain,
  testChain,
  listOllamaConfigs,
  type ChainItem,
  type ChainTestResult,
} from "@/lib/api";
import {
  GitBranch,
  Plus,
  Trash2,
  Play,
  CheckCircle,
  AlertCircle,
  X,
  ChevronDown,
  ChevronRight,
  Loader2,
  Shield,
} from "lucide-react";
import { cn } from "@/lib/utils";

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const CLOUD_PROVIDERS = ["openai", "anthropic", "google", "deepseek", "mistral"];
const ALL_PROVIDERS = [...CLOUD_PROVIDERS, "ollama"];

const CLOUD_MODELS: Record<string, string[]> = {
  openai: ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"],
  anthropic: ["claude-3-5-sonnet-20241022", "claude-3-5-haiku-20241022", "claude-3-opus-20240229"],
  google: ["gemini-1.5-pro", "gemini-1.5-flash"],
  deepseek: ["deepseek-chat"],
  mistral: ["mistral-large-latest", "mistral-small-latest"],
};

const FALLBACK_TRIGGERS = [
  { value: "rate_limit", label: "Rate Limited", description: "Provider returns 429" },
  { value: "server_error", label: "Server Error", description: "Provider returns 5xx" },
  { value: "timeout", label: "Timeout", description: "Request exceeds latency limit" },
  { value: "cost_ceiling", label: "Cost Ceiling", description: "Slot cost exceeds max" },
  { value: "no_key", label: "No Key", description: "No BYOK key available" },
];

const DEFAULT_TRIGGERS = ["rate_limit", "server_error", "timeout"];

// ---------------------------------------------------------------------------
// Slot editor
// ---------------------------------------------------------------------------

interface SlotState {
  provider: string;
  model: string;
  max_latency_ms: string;
  max_cost_per_1k_tokens: string;
}

function SlotEditor({
  slot,
  index,
  onChange,
  onRemove,
  canRemove,
  ollamaModels,
}: {
  slot: SlotState;
  index: number;
  onChange: (s: SlotState) => void;
  onRemove: () => void;
  canRemove: boolean;
  ollamaModels: string[];
}) {
  const models =
    slot.provider === "ollama"
      ? ollamaModels
      : CLOUD_MODELS[slot.provider] ?? [];

  // Reset model when provider changes and current model isn't in new list
  const handleProviderChange = (provider: string) => {
    const newModels = provider === "ollama" ? ollamaModels : CLOUD_MODELS[provider] ?? [];
    const model = newModels.includes(slot.model) ? slot.model : newModels[0] ?? "";
    onChange({ ...slot, provider, model });
  };

  const priorityLabel = index === 0 ? "Primary" : index === 1 ? "Fallback" : "Last Resort";
  const priorityColor = index === 0 ? "text-emerald-400" : index === 1 ? "text-amber-400" : "text-red-400";

  return (
    <div className="rounded-lg border border-border p-4 space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className={cn("flex h-6 w-6 items-center justify-center rounded-full bg-muted text-xs font-bold", priorityColor)}>
            {index + 1}
          </span>
          <span className={cn("text-xs font-medium", priorityColor)}>{priorityLabel}</span>
        </div>
        {canRemove && (
          <button type="button" onClick={onRemove} className="rounded p-1 text-muted-foreground hover:text-red-400">
            <Trash2 className="h-3.5 w-3.5" />
          </button>
        )}
      </div>

      <div className="grid gap-3 sm:grid-cols-2">
        {/* Provider */}
        <div>
          <label className="mb-1 block text-xs text-muted-foreground">Provider</label>
          <select
            value={slot.provider}
            onChange={(e) => handleProviderChange(e.target.value)}
            className="w-full rounded-md border border-border bg-background px-2 py-1.5 text-sm"
          >
            {ALL_PROVIDERS.map((p) => (
              <option key={p} value={p}>{p}</option>
            ))}
          </select>
        </div>

        {/* Model */}
        <div>
          <label className="mb-1 block text-xs text-muted-foreground">Model</label>
          {models.length === 0 ? (
            <input
              type="text"
              value={slot.model}
              onChange={(e) => onChange({ ...slot, model: e.target.value })}
              placeholder={slot.provider === "ollama" ? "No Ollama configs found" : "Enter model ID"}
              className="w-full rounded-md border border-border bg-background px-2 py-1.5 text-sm"
            />
          ) : (
            <select
              value={slot.model}
              onChange={(e) => onChange({ ...slot, model: e.target.value })}
              className="w-full rounded-md border border-border bg-background px-2 py-1.5 text-sm"
            >
              {models.map((m) => (
                <option key={m} value={m}>{m}</option>
              ))}
            </select>
          )}
          {slot.provider === "ollama" && models.length === 0 && (
            <p className="mt-1 text-[10px] text-amber-400">
              Add an Ollama config in Settings &gt; Providers first.
            </p>
          )}
        </div>

        {/* Max Latency */}
        <div>
          <label className="mb-1 block text-xs text-muted-foreground">Max Latency (ms)</label>
          <input
            type="number"
            min={0}
            value={slot.max_latency_ms}
            onChange={(e) => onChange({ ...slot, max_latency_ms: e.target.value })}
            placeholder="No limit"
            className="w-full rounded-md border border-border bg-background px-2 py-1.5 text-sm font-mono"
          />
        </div>

        {/* Max Cost */}
        <div>
          <label className="mb-1 block text-xs text-muted-foreground">Max $/1K tokens</label>
          <input
            type="number"
            min={0}
            step={0.001}
            value={slot.max_cost_per_1k_tokens}
            onChange={(e) => onChange({ ...slot, max_cost_per_1k_tokens: e.target.value })}
            placeholder="No limit"
            className="w-full rounded-md border border-border bg-background px-2 py-1.5 text-sm font-mono"
          />
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Chain card (existing chain)
// ---------------------------------------------------------------------------

function ChainCard({
  chain,
  orgSlug,
}: {
  chain: ChainItem;
  orgSlug: string;
}) {
  const queryClient = useQueryClient();
  const [expanded, setExpanded] = useState(false);
  const [testResult, setTestResult] = useState<ChainTestResult | null>(null);

  const deleteMutation = useMutation({
    mutationFn: () => deleteChain(chain.id, undefined, orgSlug),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["chains", orgSlug] }),
  });

  const testMutation = useMutation({
    mutationFn: () => testChain(chain.id, undefined, orgSlug),
    onSuccess: (data) => setTestResult(data),
  });

  return (
    <div className="rounded-lg border border-border">
      <button
        type="button"
        onClick={() => setExpanded(!expanded)}
        className="flex w-full items-center justify-between px-4 py-3 text-left hover:bg-muted/30 transition-colors"
      >
        <div className="flex items-center gap-3">
          <GitBranch className="h-4 w-4 text-asahio" />
          <div>
            <p className="text-sm font-medium text-foreground">{chain.name}</p>
            <p className="text-xs text-muted-foreground">
              {chain.slots.length} slot{chain.slots.length !== 1 ? "s" : ""}
              {chain.is_default && " \u00b7 Default"}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {chain.fallback_triggers.length > 0 && (
            <div className="hidden gap-1 sm:flex">
              {chain.fallback_triggers.map((t) => (
                <span key={t} className="rounded bg-muted px-1.5 py-0.5 text-[10px] text-muted-foreground">
                  {t}
                </span>
              ))}
            </div>
          )}
          {expanded ? <ChevronDown className="h-4 w-4 text-muted-foreground" /> : <ChevronRight className="h-4 w-4 text-muted-foreground" />}
        </div>
      </button>

      {expanded && (
        <div className="border-t border-border px-4 py-3 space-y-3">
          {/* Slots */}
          <div className="space-y-2">
            {chain.slots
              .sort((a, b) => a.priority - b.priority)
              .map((s) => (
                <div key={s.id} className="flex items-center gap-3 rounded-md bg-muted/30 px-3 py-2 text-sm">
                  <span className={cn(
                    "flex h-5 w-5 items-center justify-center rounded-full bg-muted text-[10px] font-bold",
                    s.priority === 1 ? "text-emerald-400" : s.priority === 2 ? "text-amber-400" : "text-red-400"
                  )}>
                    {s.priority}
                  </span>
                  <span className="font-mono text-xs text-foreground">{s.model}</span>
                  <span className="text-xs text-muted-foreground">({s.provider})</span>
                  {s.max_latency_ms != null && (
                    <span className="text-[10px] text-muted-foreground">&le; {s.max_latency_ms}ms</span>
                  )}
                  {s.max_cost_per_1k_tokens != null && (
                    <span className="text-[10px] text-muted-foreground">&le; ${s.max_cost_per_1k_tokens}/1K</span>
                  )}
                </div>
              ))}
          </div>

          {/* Test results */}
          {testResult && (
            <div className={cn("rounded-md border p-3 text-sm", testResult.ready ? "border-emerald-500/30 bg-emerald-500/10" : "border-red-500/30 bg-red-500/10")}>
              <div className="flex items-center gap-2 mb-2">
                {testResult.ready ? (
                  <CheckCircle className="h-4 w-4 text-emerald-400" />
                ) : (
                  <AlertCircle className="h-4 w-4 text-red-400" />
                )}
                <span className={testResult.ready ? "text-emerald-400" : "text-red-400"}>
                  {testResult.ready ? "All slots ready" : "Some slots need keys"}
                </span>
              </div>
              {testResult.slots.map((s) => (
                <div key={s.position} className="flex items-center gap-2 text-xs">
                  {s.key_available ? (
                    <CheckCircle className="h-3 w-3 text-emerald-400" />
                  ) : (
                    <AlertCircle className="h-3 w-3 text-red-400" />
                  )}
                  <span className="text-muted-foreground">Slot {s.position}:</span>
                  <span className="font-mono">{s.model}</span>
                  {s.error && <span className="text-red-400">({s.error})</span>}
                </div>
              ))}
            </div>
          )}

          {/* Actions */}
          <div className="flex gap-2">
            <button
              type="button"
              onClick={() => testMutation.mutate()}
              disabled={testMutation.isPending}
              className="flex items-center gap-1 rounded-md bg-muted px-3 py-1.5 text-xs font-medium text-foreground hover:bg-muted/80 disabled:opacity-50"
            >
              {testMutation.isPending ? <Loader2 className="h-3 w-3 animate-spin" /> : <Play className="h-3 w-3" />}
              Test Keys
            </button>
            <button
              type="button"
              onClick={() => deleteMutation.mutate()}
              disabled={deleteMutation.isPending}
              className="flex items-center gap-1 rounded-md border border-red-500/30 px-3 py-1.5 text-xs text-red-400 hover:bg-red-500/10 disabled:opacity-50"
            >
              <Trash2 className="h-3 w-3" />
              Delete
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

interface ChainBuilderProps {
  orgSlug: string;
}

export function ChainBuilder({ orgSlug }: ChainBuilderProps) {
  const queryClient = useQueryClient();
  const [building, setBuilding] = useState(false);
  const [name, setName] = useState("");
  const [triggers, setTriggers] = useState<string[]>(DEFAULT_TRIGGERS);
  const [isDefault, setIsDefault] = useState(false);
  const [slots, setSlots] = useState<SlotState[]>([
    { provider: "openai", model: "gpt-4o", max_latency_ms: "", max_cost_per_1k_tokens: "" },
  ]);

  // Fetch existing chains
  const { data: chainsData, isLoading } = useQuery({
    queryKey: ["chains", orgSlug],
    queryFn: () => listChains(undefined, orgSlug),
    enabled: !!orgSlug,
  });

  // Fetch Ollama configs for dynamic model list (P0-5)
  const { data: ollamaData } = useQuery({
    queryKey: ["ollama-configs", orgSlug],
    queryFn: () => listOllamaConfigs(undefined, orgSlug),
    enabled: !!orgSlug,
  });

  const ollamaModels = (ollamaData?.data ?? []).flatMap((c) => c.available_models);
  const chains = chainsData?.data ?? [];

  const createMutation = useMutation({
    mutationFn: () =>
      createChain(
        {
          name,
          fallback_triggers: triggers,
          is_default: isDefault,
          slots: slots.map((s, i) => ({
            provider: s.provider,
            model: s.model,
            priority: i + 1,
            max_latency_ms: s.max_latency_ms ? parseInt(s.max_latency_ms) : null,
            max_cost_per_1k_tokens: s.max_cost_per_1k_tokens ? parseFloat(s.max_cost_per_1k_tokens) : null,
          })),
        },
        undefined,
        orgSlug
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["chains", orgSlug] });
      resetBuilder();
    },
  });

  const resetBuilder = () => {
    setBuilding(false);
    setName("");
    setTriggers(DEFAULT_TRIGGERS);
    setIsDefault(false);
    setSlots([{ provider: "openai", model: "gpt-4o", max_latency_ms: "", max_cost_per_1k_tokens: "" }]);
  };

  const addSlot = () => {
    if (slots.length >= 3) return;
    setSlots([...slots, { provider: "openai", model: "gpt-4o-mini", max_latency_ms: "", max_cost_per_1k_tokens: "" }]);
  };

  const removeSlot = (idx: number) => {
    setSlots(slots.filter((_, i) => i !== idx));
  };

  const updateSlot = (idx: number, s: SlotState) => {
    setSlots(slots.map((old, i) => (i === idx ? s : old)));
  };

  const toggleTrigger = (t: string) => {
    setTriggers((prev) => (prev.includes(t) ? prev.filter((x) => x !== t) : [...prev, t]));
  };

  const canSave = name.trim().length > 0 && slots.length > 0 && slots.every((s) => s.model.length > 0);

  return (
    <div className="space-y-6">
      {/* Existing chains */}
      {isLoading ? (
        <div className="flex items-center justify-center py-8 text-muted-foreground">
          <Loader2 className="mr-2 h-4 w-4 animate-spin" /> Loading chains...
        </div>
      ) : chains.length > 0 ? (
        <div className="space-y-2">
          <h3 className="text-sm font-medium text-foreground">Guided Chains</h3>
          {chains.map((c) => (
            <ChainCard key={c.id} chain={c} orgSlug={orgSlug} />
          ))}
        </div>
      ) : !building ? (
        <div className="flex flex-col items-center justify-center rounded-lg border border-dashed border-border py-12">
          <GitBranch className="h-12 w-12 text-muted-foreground/50" />
          <p className="mt-4 text-sm text-muted-foreground">No guided chains configured yet.</p>
          <p className="text-xs text-muted-foreground">
            Create a chain to define a fallback sequence of models.
          </p>
        </div>
      ) : null}

      {/* Builder toggle */}
      {!building && (
        <button
          type="button"
          onClick={() => setBuilding(true)}
          className="flex items-center gap-2 rounded-md bg-asahio px-4 py-2 text-sm font-medium text-white hover:bg-asahio/90"
        >
          <Plus className="h-4 w-4" />
          New Chain
        </button>
      )}

      {/* Builder form */}
      {building && (
        <div className="rounded-lg border border-asahio/30 bg-asahio/5 p-5 space-y-5">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-medium text-foreground">Build Guided Chain</h3>
            <button type="button" onClick={resetBuilder} className="rounded p-1 text-muted-foreground hover:text-foreground">
              <X className="h-4 w-4" />
            </button>
          </div>

          {/* Chain name */}
          <div>
            <label className="mb-1 block text-xs text-muted-foreground">Chain Name</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Production Fallback"
              className="w-full max-w-sm rounded-md border border-border bg-background px-3 py-1.5 text-sm"
            />
          </div>

          {/* Slots */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <label className="text-xs font-medium text-muted-foreground">Slots (1-3)</label>
              {slots.length < 3 && (
                <button
                  type="button"
                  onClick={addSlot}
                  className="flex items-center gap-1 text-xs text-asahio hover:underline"
                >
                  <Plus className="h-3 w-3" /> Add slot
                </button>
              )}
            </div>
            {slots.map((s, i) => (
              <SlotEditor
                key={i}
                slot={s}
                index={i}
                onChange={(updated) => updateSlot(i, updated)}
                onRemove={() => removeSlot(i)}
                canRemove={slots.length > 1}
                ollamaModels={ollamaModels}
              />
            ))}
          </div>

          {/* Fallback triggers */}
          <div>
            <label className="mb-2 block text-xs font-medium text-muted-foreground">
              Fallback Triggers
            </label>
            <p className="mb-2 text-[10px] text-muted-foreground">
              When these conditions occur, the chain falls back to the next slot.
            </p>
            <div className="flex flex-wrap gap-2">
              {FALLBACK_TRIGGERS.map((t) => (
                <button
                  key={t.value}
                  type="button"
                  onClick={() => toggleTrigger(t.value)}
                  title={t.description}
                  className={cn(
                    "rounded-md border px-3 py-1.5 text-xs transition-colors",
                    triggers.includes(t.value)
                      ? "border-asahio bg-asahio/10 text-asahio"
                      : "border-border text-muted-foreground hover:border-asahio/50"
                  )}
                >
                  {t.label}
                </button>
              ))}
            </div>
          </div>

          {/* Default flag */}
          <label className="flex items-center gap-2 text-xs text-muted-foreground">
            <input
              type="checkbox"
              checked={isDefault}
              onChange={(e) => setIsDefault(e.target.checked)}
              className="rounded border-border"
            />
            Set as default chain for GUIDED routing mode
          </label>

          {/* Actions */}
          <div className="flex items-center gap-3 border-t border-border pt-4">
            <button
              type="button"
              onClick={() => createMutation.mutate()}
              disabled={!canSave || createMutation.isPending}
              className="flex items-center gap-2 rounded-md bg-asahio px-4 py-2 text-sm font-medium text-white hover:bg-asahio/90 disabled:opacity-50"
            >
              {createMutation.isPending ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Shield className="h-4 w-4" />
              )}
              {createMutation.isPending ? "Creating..." : "Create Chain"}
            </button>
            <button
              type="button"
              onClick={resetBuilder}
              className="rounded-md border border-border px-4 py-2 text-sm text-muted-foreground hover:text-foreground"
            >
              Cancel
            </button>
          </div>

          {createMutation.isError && (
            <div className="flex items-start gap-2 rounded-md border border-red-500/30 bg-red-500/10 p-3 text-xs text-red-400">
              <AlertCircle className="mt-0.5 h-4 w-4 flex-shrink-0" />
              {(createMutation.error as Error).message}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
