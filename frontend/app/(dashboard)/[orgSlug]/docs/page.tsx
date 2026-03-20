"use client";

import { useState, useMemo } from "react";
import { useParams } from "next/navigation";
import {
  BookOpen,
  Rocket,
  Code2,
  Terminal,
  Search,
  ChevronRight,
  Copy,
  Check,
  Zap,
  Shield,
  Brain,
  Database,
  GitBranch,
  Activity,
} from "lucide-react";
import { cn } from "@/lib/utils";

// ---------------------------------------------------------------------------
// Content Sections
// ---------------------------------------------------------------------------

type Section = "getting-started" | "api-reference" | "sdk";

interface DocSection {
  id: Section;
  label: string;
  icon: typeof BookOpen;
}

const SECTIONS: DocSection[] = [
  { id: "getting-started", label: "Getting Started", icon: Rocket },
  { id: "api-reference", label: "API Reference", icon: Code2 },
  { id: "sdk", label: "SDK", icon: Terminal },
];

// ---------------------------------------------------------------------------
// Copy button
// ---------------------------------------------------------------------------

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);
  return (
    <button
      type="button"
      className="absolute right-2 top-2 rounded p-1 text-muted-foreground hover:text-foreground"
      onClick={() => {
        navigator.clipboard.writeText(text);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
      }}
    >
      {copied ? <Check className="h-3.5 w-3.5 text-emerald-400" /> : <Copy className="h-3.5 w-3.5" />}
    </button>
  );
}

function CodeBlock({ code, lang = "bash" }: { code: string; lang?: string }) {
  return (
    <div className="relative rounded-lg border border-border bg-muted/30">
      <CopyButton text={code} />
      <pre className="overflow-x-auto p-4 text-sm text-foreground">
        <code>{code}</code>
      </pre>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Getting Started
// ---------------------------------------------------------------------------

function GettingStartedContent() {
  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-xl font-bold text-foreground">Quick Start Guide</h2>
        <p className="mt-2 text-sm text-muted-foreground">
          Get up and running with ASAHIO in under 5 minutes.
        </p>
      </div>

      <div className="space-y-6">
        <div className="flex items-start gap-4">
          <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-asahio text-xs font-bold text-white">
            1
          </span>
          <div className="space-y-3">
            <h3 className="font-semibold text-foreground">Install the SDK</h3>
            <CodeBlock code="pip install asahio-ai" />
          </div>
        </div>

        <div className="flex items-start gap-4">
          <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-asahio text-xs font-bold text-white">
            2
          </span>
          <div className="space-y-3">
            <h3 className="font-semibold text-foreground">Create an API Key</h3>
            <p className="text-sm text-muted-foreground">
              Go to the <strong>API Keys</strong> page in the sidebar and create a new key.
              Copy the key immediately — it won&apos;t be shown again.
            </p>
          </div>
        </div>

        <div className="flex items-start gap-4">
          <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-asahio text-xs font-bold text-white">
            3
          </span>
          <div className="space-y-3">
            <h3 className="font-semibold text-foreground">Send Your First Request</h3>
            <CodeBlock
              lang="python"
              code={`from asahio import AsahioClient

client = AsahioClient(
    api_key="your-api-key",
    base_url="https://api.asahio.dev"
)

response = client.chat.completions.create(
    messages=[{"role": "user", "content": "Hello, ASAHIO!"}],
    routing_mode="AUTO",  # Let ASAHIO pick the best model
)

print(response.choices[0].message.content)
print(f"Cost saved: \${response.asahio.savings_usd:.4f}")`}
            />
          </div>
        </div>

        <div className="flex items-start gap-4">
          <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-asahio text-xs font-bold text-white">
            4
          </span>
          <div className="space-y-3">
            <h3 className="font-semibold text-foreground">View Your Traces</h3>
            <p className="text-sm text-muted-foreground">
              Go to the <strong>Traces</strong> page to see the request, which model was selected,
              cache status, cost savings, and risk score.
            </p>
          </div>
        </div>
      </div>

      <div className="rounded-lg border border-border p-4 space-y-3">
        <h3 className="font-semibold text-foreground">Key Concepts</h3>
        <div className="grid gap-3 sm:grid-cols-2">
          {[
            { icon: Zap, title: "Gateway", desc: "OpenAI-compatible endpoint that routes, caches, and observes every LLM call" },
            { icon: GitBranch, title: "Routing Modes", desc: "AUTO (6-factor engine), EXPLICIT (you pick), or GUIDED (rules you define)" },
            { icon: Shield, title: "Intervention Modes", desc: "OBSERVE (watch only), ASSISTED (cache+augment), AUTONOMOUS (full control)" },
            { icon: Brain, title: "ABA Engine", desc: "Agent Behavioral Analytics — fingerprints agents and detects anomalies" },
            { icon: Database, title: "3-Tier Cache", desc: "Exact match (Redis), semantic match (Pinecone), and intermediate results" },
            { icon: Activity, title: "Traces", desc: "Full observability for every call: cost, latency, risk, intervention" },
          ].map((item) => (
            <div key={item.title} className="flex items-start gap-3 rounded-md border border-border p-3">
              <item.icon className="mt-0.5 h-4 w-4 text-asahio" />
              <div>
                <p className="text-sm font-medium text-foreground">{item.title}</p>
                <p className="text-xs text-muted-foreground">{item.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// API Reference
// ---------------------------------------------------------------------------

interface Endpoint {
  method: string;
  path: string;
  description: string;
  category: string;
  requestExample?: string;
  responseExample?: string;
}

const ENDPOINTS: Endpoint[] = [
  {
    method: "POST",
    path: "/v1/chat/completions",
    description: "Send a chat completion request through the ASAHIO gateway. Supports routing_mode, intervention_mode, agent_id, and session_id.",
    category: "Gateway",
    requestExample: `{
  "messages": [{"role": "user", "content": "Explain quantum computing"}],
  "routing_mode": "AUTO",
  "intervention_mode": "ASSISTED",
  "agent_id": "agent-uuid"
}`,
    responseExample: `{
  "id": "chatcmpl-...",
  "model": "gpt-4o-mini",
  "choices": [{"message": {"role": "assistant", "content": "..."}}],
  "asahio": {
    "cache_hit": false,
    "cost_without_asahio": 0.0012,
    "cost_with_asahio": 0.0003,
    "savings_usd": 0.0009,
    "routing_reason": "Auto: cheapest meeting quality threshold"
  }
}`,
  },
  { method: "GET", path: "/agents", description: "List all agents for the organisation.", category: "Agents" },
  { method: "POST", path: "/agents", description: "Create a new agent with routing and intervention modes.", category: "Agents" },
  { method: "GET", path: "/agents/{id}", description: "Get agent details including stats.", category: "Agents" },
  { method: "POST", path: "/agents/{id}/mode-transition", description: "Transition an agent to a new intervention mode.", category: "Agents" },
  { method: "GET", path: "/analytics/overview", description: "Aggregated analytics: requests, cost, savings, cache hit rate.", category: "Analytics" },
  { method: "GET", path: "/analytics/savings", description: "Time-series savings data with configurable granularity.", category: "Analytics" },
  { method: "GET", path: "/analytics/cache", description: "Cache performance breakdown by tier.", category: "Analytics" },
  { method: "GET", path: "/analytics/forecast", description: "Cost and savings forecast for the next N days.", category: "Analytics" },
  { method: "GET", path: "/routing/decisions", description: "Audit trail of routing decisions with factors.", category: "Routing" },
  { method: "GET", path: "/routing/constraints", description: "List routing constraints (rules) for the org.", category: "Routing" },
  { method: "POST", path: "/routing/constraints", description: "Create a routing constraint (step_based, time_based, fallback_chain, etc.).", category: "Routing" },
  { method: "POST", path: "/routing/rules/dry-run", description: "Test a rule configuration without saving it.", category: "Routing" },
  { method: "GET", path: "/aba/fingerprints", description: "List ABA fingerprints for all agents.", category: "ABA" },
  { method: "GET", path: "/aba/anomalies", description: "Detect behavioral anomalies across agents.", category: "ABA" },
  { method: "GET", path: "/interventions", description: "List intervention logs with risk scores and actions.", category: "Interventions" },
  { method: "GET", path: "/interventions/stats", description: "Intervention statistics over time.", category: "Interventions" },
  { method: "GET", path: "/keys", description: "List API keys for the organisation.", category: "Keys" },
  { method: "POST", path: "/keys", description: "Create a new API key. Returns the raw key once.", category: "Keys" },
  { method: "GET", path: "/models", description: "List registered model endpoints.", category: "Models" },
  { method: "POST", path: "/models/register", description: "Register a new model endpoint (BYOM).", category: "Models" },
  { method: "GET", path: "/billing/subscription", description: "Get current billing subscription details.", category: "Billing" },
  { method: "GET", path: "/health", description: "Health check with component status.", category: "Health" },
  { method: "GET", path: "/health/providers", description: "Provider health status (latency, errors).", category: "Health" },
];

const METHOD_COLORS: Record<string, string> = {
  GET: "bg-emerald-500/20 text-emerald-400",
  POST: "bg-blue-500/20 text-blue-400",
  PUT: "bg-amber-500/20 text-amber-400",
  DELETE: "bg-red-500/20 text-red-400",
  PATCH: "bg-violet-500/20 text-violet-400",
};

function ApiReferenceContent({ search }: { search: string }) {
  const filtered = useMemo(() => {
    if (!search) return ENDPOINTS;
    const q = search.toLowerCase();
    return ENDPOINTS.filter(
      (e) =>
        e.path.toLowerCase().includes(q) ||
        e.description.toLowerCase().includes(q) ||
        e.category.toLowerCase().includes(q)
    );
  }, [search]);

  const categories = useMemo(() => {
    const cats = new Map<string, Endpoint[]>();
    for (const ep of filtered) {
      const list = cats.get(ep.category) ?? [];
      list.push(ep);
      cats.set(ep.category, list);
    }
    return cats;
  }, [filtered]);

  const [expandedPath, setExpandedPath] = useState<string | null>(null);

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-xl font-bold text-foreground">API Reference</h2>
        <p className="mt-2 text-sm text-muted-foreground">
          All endpoints require an API key via <code className="rounded bg-muted px-1.5 py-0.5 text-xs">Authorization: Bearer &lt;key&gt;</code> header
          and org context via <code className="rounded bg-muted px-1.5 py-0.5 text-xs">X-Org-Slug</code> header.
        </p>
      </div>

      {filtered.length === 0 ? (
        <p className="text-sm text-muted-foreground">No endpoints match your search.</p>
      ) : (
        Array.from(categories.entries()).map(([cat, eps]) => (
          <div key={cat} className="space-y-2">
            <h3 className="text-sm font-semibold text-foreground">{cat}</h3>
            <div className="space-y-1">
              {eps.map((ep) => {
                const key = `${ep.method} ${ep.path}`;
                const isExpanded = expandedPath === key;
                return (
                  <div key={key} className="rounded-lg border border-border">
                    <button
                      type="button"
                      onClick={() => setExpandedPath(isExpanded ? null : key)}
                      className="flex w-full items-center gap-3 px-4 py-3 text-left hover:bg-muted/30 transition-colors"
                    >
                      <span className={cn("rounded px-1.5 py-0.5 text-[10px] font-bold", METHOD_COLORS[ep.method])}>
                        {ep.method}
                      </span>
                      <span className="font-mono text-xs text-foreground">{ep.path}</span>
                      <span className="flex-1 truncate text-xs text-muted-foreground">{ep.description}</span>
                      <ChevronRight className={cn("h-4 w-4 text-muted-foreground transition-transform", isExpanded && "rotate-90")} />
                    </button>
                    {isExpanded && (
                      <div className="border-t border-border px-4 py-3 space-y-3">
                        <p className="text-sm text-muted-foreground">{ep.description}</p>
                        {ep.requestExample && (
                          <div>
                            <p className="mb-1 text-xs font-medium text-muted-foreground">Request Body</p>
                            <CodeBlock code={ep.requestExample} lang="json" />
                          </div>
                        )}
                        {ep.responseExample && (
                          <div>
                            <p className="mb-1 text-xs font-medium text-muted-foreground">Response</p>
                            <CodeBlock code={ep.responseExample} lang="json" />
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        ))
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// SDK
// ---------------------------------------------------------------------------

function SdkContent() {
  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-xl font-bold text-foreground">Python SDK</h2>
        <p className="mt-2 text-sm text-muted-foreground">
          The official Python SDK for ASAHIO. Works with Python 3.9+.
        </p>
      </div>

      <div className="space-y-4">
        <h3 className="font-semibold text-foreground">Installation</h3>
        <CodeBlock code="pip install asahio-ai" />
      </div>

      <div className="space-y-4">
        <h3 className="font-semibold text-foreground">Synchronous Client</h3>
        <CodeBlock
          lang="python"
          code={`from asahio import AsahioClient

client = AsahioClient(
    api_key="ask_...",
    base_url="https://api.asahio.dev",
    org_slug="my-org",
)

# Simple chat completion
response = client.chat.completions.create(
    messages=[{"role": "user", "content": "Hello!"}],
    routing_mode="AUTO",
)

# Access ASAHIO metadata
meta = response.asahio
print(f"Model used: {meta.model_used}")
print(f"Cache hit: {meta.cache_hit}")
print(f"Savings: \${meta.savings_usd:.4f}")
print(f"Risk score: {meta.risk_score}")`}
        />
      </div>

      <div className="space-y-4">
        <h3 className="font-semibold text-foreground">Async Client</h3>
        <CodeBlock
          lang="python"
          code={`from asahio import AsyncAsahioClient

client = AsyncAsahioClient(
    api_key="ask_...",
    base_url="https://api.asahio.dev",
)

response = await client.chat.completions.create(
    messages=[{"role": "user", "content": "Hello!"}],
    agent_id="agent-uuid",
    session_id="session-uuid",
)

print(response.choices[0].message.content)`}
        />
      </div>

      <div className="space-y-4">
        <h3 className="font-semibold text-foreground">Agent Sessions</h3>
        <CodeBlock
          lang="python"
          code={`import uuid

session_id = str(uuid.uuid4())

# Step 1
r1 = client.chat.completions.create(
    messages=[{"role": "user", "content": "Research quantum computing"}],
    agent_id="research-agent",
    session_id=session_id,
    routing_mode="AUTO",
    intervention_mode="ASSISTED",
)

# Step 2 — ASAHIO tracks step dependencies
r2 = client.chat.completions.create(
    messages=[
        {"role": "user", "content": "Research quantum computing"},
        {"role": "assistant", "content": r1.choices[0].message.content},
        {"role": "user", "content": "Now summarize the key points"},
    ],
    agent_id="research-agent",
    session_id=session_id,
)`}
        />
      </div>

      <div className="space-y-4">
        <h3 className="font-semibold text-foreground">Routing Modes</h3>
        <div className="overflow-x-auto rounded-lg border border-border">
          <table className="w-full text-sm">
            <thead className="border-b border-border bg-muted/50">
              <tr>
                <th className="px-4 py-2 text-left font-medium text-muted-foreground">Mode</th>
                <th className="px-4 py-2 text-left font-medium text-muted-foreground">Description</th>
                <th className="px-4 py-2 text-left font-medium text-muted-foreground">Use Case</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              <tr>
                <td className="px-4 py-2 font-mono text-xs text-emerald-400">AUTO</td>
                <td className="px-4 py-2 text-muted-foreground">6-factor engine picks the best model</td>
                <td className="px-4 py-2 text-muted-foreground">Default for most workloads</td>
              </tr>
              <tr>
                <td className="px-4 py-2 font-mono text-xs text-blue-400">EXPLICIT</td>
                <td className="px-4 py-2 text-muted-foreground">You specify the exact model</td>
                <td className="px-4 py-2 text-muted-foreground">Fine-tuned models, specific requirements</td>
              </tr>
              <tr>
                <td className="px-4 py-2 font-mono text-xs text-amber-400">GUIDED</td>
                <td className="px-4 py-2 text-muted-foreground">Rules you define (step-based, time-based, etc.)</td>
                <td className="px-4 py-2 text-muted-foreground">Cost control, compliance, scheduling</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div className="space-y-4">
        <h3 className="font-semibold text-foreground">Backward Compatibility</h3>
        <p className="text-sm text-muted-foreground">
          The <code className="rounded bg-muted px-1.5 py-0.5 text-xs">asahi</code> and{" "}
          <code className="rounded bg-muted px-1.5 py-0.5 text-xs">acorn</code> package names are
          supported as aliases. They re-export everything from <code className="rounded bg-muted px-1.5 py-0.5 text-xs">asahio</code>.
        </p>
        <CodeBlock
          lang="python"
          code={`# All three are equivalent:
from asahio import AsahioClient
from asahi import AsahioClient
from acorn import AsahioClient`}
        />
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main Page
// ---------------------------------------------------------------------------

export default function DocsPage() {
  const params = useParams();
  const orgSlug = typeof params?.orgSlug === "string" ? params.orgSlug : "";

  const [activeSection, setActiveSection] = useState<Section>("getting-started");
  const [search, setSearch] = useState("");

  return (
    <div className="animate-fade-in">
      <div className="flex gap-6">
        {/* Sidebar navigation */}
        <aside className="hidden w-48 shrink-0 space-y-1 lg:block">
          <div className="relative mb-4">
            <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-muted-foreground" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search docs..."
              className="w-full rounded-md border border-border bg-background pl-8 pr-3 py-2 text-xs"
            />
          </div>
          {SECTIONS.map((s) => (
            <button
              key={s.id}
              type="button"
              onClick={() => setActiveSection(s.id)}
              className={cn(
                "flex w-full items-center gap-2 rounded-md px-3 py-2 text-sm transition-colors",
                activeSection === s.id
                  ? "bg-asahio/10 text-asahio font-medium"
                  : "text-muted-foreground hover:text-foreground hover:bg-muted/50"
              )}
            >
              <s.icon className="h-4 w-4" />
              {s.label}
            </button>
          ))}
        </aside>

        {/* Mobile section tabs */}
        <div className="mb-4 flex gap-1 overflow-x-auto lg:hidden">
          {SECTIONS.map((s) => (
            <button
              key={s.id}
              type="button"
              onClick={() => setActiveSection(s.id)}
              className={cn(
                "flex shrink-0 items-center gap-1 rounded-full px-3 py-1.5 text-xs font-medium transition-colors",
                activeSection === s.id
                  ? "bg-asahio text-white"
                  : "bg-muted text-muted-foreground"
              )}
            >
              <s.icon className="h-3 w-3" />
              {s.label}
            </button>
          ))}
        </div>

        {/* Content */}
        <div className="min-w-0 flex-1">
          {activeSection === "getting-started" && <GettingStartedContent />}
          {activeSection === "api-reference" && <ApiReferenceContent search={search} />}
          {activeSection === "sdk" && <SdkContent />}
        </div>
      </div>
    </div>
  );
}
