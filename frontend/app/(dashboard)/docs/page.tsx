"use client";

import { useState, useMemo } from "react";
import Image from "next/image";
import Link from "next/link";
import {
  BookOpen,
  Check,
  ChevronRight,
  Code2,
  Copy,
  Rocket,
  Search,
  Terminal,
  Zap,
  Shield,
  Brain,
  Database,
  GitBranch,
  Activity,
} from "lucide-react";
import { cn } from "@/lib/utils";

const apiBase = (process.env.NEXT_PUBLIC_API_URL || "").replace(/\/$/, "");

// ---------------------------------------------------------------------------
// Copy button + code block
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

function CodeBlock({ code }: { code: string }) {
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
// Tabs
// ---------------------------------------------------------------------------

type Section = "getting-started" | "api-reference" | "sdk";

const SECTIONS: { id: Section; label: string; icon: typeof BookOpen }[] = [
  { id: "getting-started", label: "Getting Started", icon: Rocket },
  { id: "api-reference", label: "API Reference", icon: Code2 },
  { id: "sdk", label: "SDK", icon: Terminal },
];

// ---------------------------------------------------------------------------
// API Endpoints
// ---------------------------------------------------------------------------

interface Endpoint {
  method: string;
  path: string;
  description: string;
  category: string;
}

const ENDPOINTS: Endpoint[] = [
  { method: "POST", path: "/v1/chat/completions", description: "Send a chat completion request through the ASAHIO gateway.", category: "Gateway" },
  { method: "GET", path: "/agents", description: "List all agents for the organisation.", category: "Agents" },
  { method: "POST", path: "/agents", description: "Create a new agent with routing and intervention modes.", category: "Agents" },
  { method: "PATCH", path: "/agents/{id}", description: "Update agent configuration.", category: "Agents" },
  { method: "POST", path: "/agents/{id}/archive", description: "Archive (deactivate) an agent.", category: "Agents" },
  { method: "GET", path: "/agents/{id}/stats", description: "Get agent call statistics.", category: "Agents" },
  { method: "POST", path: "/agents/{id}/mode-transition", description: "Transition an agent to a new intervention mode.", category: "Agents" },
  { method: "GET", path: "/analytics/overview", description: "Aggregated analytics: requests, cost, savings, cache hit rate.", category: "Analytics" },
  { method: "GET", path: "/analytics/savings", description: "Time-series savings data with configurable granularity.", category: "Analytics" },
  { method: "GET", path: "/analytics/cache", description: "Cache performance breakdown by tier.", category: "Analytics" },
  { method: "GET", path: "/analytics/forecast", description: "Cost and savings forecast for the next N days.", category: "Analytics" },
  { method: "GET", path: "/routing/decisions", description: "Audit trail of routing decisions with factors.", category: "Routing" },
  { method: "GET", path: "/routing/constraints", description: "List routing constraints (rules) for the org.", category: "Routing" },
  { method: "POST", path: "/routing/constraints", description: "Create a routing constraint.", category: "Routing" },
  { method: "POST", path: "/routing/rules/dry-run", description: "Test a rule configuration without saving.", category: "Routing" },
  { method: "GET", path: "/models", description: "List registered model endpoints.", category: "Models" },
  { method: "POST", path: "/models/register", description: "Register a new model endpoint (BYOM).", category: "Models" },
  { method: "PATCH", path: "/models/{id}", description: "Update a model endpoint.", category: "Models" },
  { method: "DELETE", path: "/models/{id}", description: "Delete a model endpoint.", category: "Models" },
  { method: "GET", path: "/aba/fingerprints", description: "List ABA fingerprints for all agents.", category: "ABA" },
  { method: "GET", path: "/aba/anomalies", description: "Detect behavioral anomalies across agents.", category: "ABA" },
  { method: "GET", path: "/interventions", description: "List intervention logs with risk scores and actions.", category: "Interventions" },
  { method: "GET", path: "/keys", description: "List API keys for the organisation.", category: "Keys" },
  { method: "POST", path: "/keys", description: "Create a new API key.", category: "Keys" },
  { method: "GET", path: "/billing/subscription", description: "Get current billing subscription details.", category: "Billing" },
  { method: "GET", path: "/health", description: "Health check with component status.", category: "Health" },
  { method: "GET", path: "/health/providers", description: "Provider health status.", category: "Health" },
];

const METHOD_COLORS: Record<string, string> = {
  GET: "bg-emerald-500/20 text-emerald-400",
  POST: "bg-blue-500/20 text-blue-400",
  PUT: "bg-amber-500/20 text-amber-400",
  DELETE: "bg-red-500/20 text-red-400",
  PATCH: "bg-violet-500/20 text-violet-400",
};

// ---------------------------------------------------------------------------
// Main Page
// ---------------------------------------------------------------------------

export default function PublicDocsPage() {
  const [activeSection, setActiveSection] = useState<Section>("getting-started");
  const [search, setSearch] = useState("");

  return (
    <div className="min-h-screen bg-background text-foreground">
      {/* Navbar */}
      <nav className="fixed top-0 inset-x-0 z-50 border-b border-border bg-background/80 backdrop-blur-md">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-6">
          <Link href="/" className="flex items-center gap-2">
            <Image src="/asashio_logo-NB.png" alt="ASAHIO" width={28} height={28} className="rounded-md" />
            <span className="text-xl font-bold tracking-tight text-asahio">ASAHIO</span>
          </Link>
          <div className="flex items-center gap-3">
            <Link
              href="/sign-in"
              className="rounded-lg px-4 py-2 text-sm font-medium text-muted-foreground hover:text-foreground transition-colors"
            >
              Sign In
            </Link>
            <Link
              href="/sign-up"
              className="rounded-lg bg-asahio px-4 py-2 text-sm font-medium text-white hover:bg-asahio-dark transition-colors"
            >
              Get Started
            </Link>
          </div>
        </div>
      </nav>

      <div className="mx-auto max-w-5xl px-6 pt-28 pb-20">
        {/* Header */}
        <div className="mb-8">
          <p className="text-sm font-medium uppercase tracking-wide text-asahio">Documentation</p>
          <h1 className="mt-2 text-4xl font-bold">ASAHIO Platform Docs</h1>
          <p className="mt-4 max-w-2xl text-lg text-muted-foreground">
            The control plane for production AI systems. Route, cache, observe, and intervene on every LLM call.
          </p>
        </div>

        {/* Tab bar + search */}
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between border-b border-border mb-8">
          <div className="flex gap-1">
            {SECTIONS.map((s) => (
              <button
                key={s.id}
                onClick={() => setActiveSection(s.id)}
                className={cn(
                  "flex items-center gap-2 border-b-2 px-4 py-2 text-sm font-medium transition-colors",
                  activeSection === s.id
                    ? "border-asahio text-asahio"
                    : "border-transparent text-muted-foreground hover:text-foreground"
                )}
              >
                <s.icon className="h-4 w-4" />
                {s.label}
              </button>
            ))}
          </div>
          {activeSection === "api-reference" && (
            <div className="relative mb-2 sm:mb-0">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search endpoints..."
                className="w-full rounded-md border border-border bg-background pl-9 pr-3 py-2 text-sm text-foreground placeholder:text-muted-foreground sm:w-64"
              />
            </div>
          )}
        </div>

        {/* Getting Started */}
        {activeSection === "getting-started" && (
          <div className="space-y-8">
            <div className="space-y-6">
              <Step n={1} title="Install the SDK">
                <CodeBlock code="pip install asahio" />
              </Step>
              <Step n={2} title="Create an API Key">
                <p className="text-sm text-muted-foreground">
                  Sign in to the dashboard and go to <strong>API Keys</strong>. Create a new key and copy it immediately.
                </p>
              </Step>
              <Step n={3} title="Send Your First Request">
                <CodeBlock
                  code={`from asahio import AsahioClient

client = AsahioClient(
    api_key="your-api-key",
    base_url="https://api.asahio.dev"
)

response = client.chat.completions.create(
    messages=[{"role": "user", "content": "Hello, ASAHIO!"}],
    routing_mode="AUTO",
)

print(response.choices[0].message.content)
print(f"Cost saved: \${response.asahio.savings_usd:.4f}")`}
                />
              </Step>
              <Step n={4} title="View Your Traces">
                <p className="text-sm text-muted-foreground">
                  Go to the <strong>Traces</strong> page to see which model was selected, cache status,
                  cost savings, and risk score for every request.
                </p>
              </Step>
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

            <div className="rounded-xl border border-border bg-card p-6 space-y-4">
              <h3 className="font-semibold text-foreground">Authentication</h3>
              <p className="text-sm text-muted-foreground">
                All API requests require an API key in the <code className="text-foreground">Authorization</code> header.
              </p>
              <CodeBlock
                code={`curl -X POST https://api.asahio.dev/v1/chat/completions \\
  -H "Authorization: Bearer asahio_live_your_key" \\
  -H "Content-Type: application/json" \\
  -d '{"messages": [{"role": "user", "content": "Hello"}]}'`}
              />
            </div>
          </div>
        )}

        {/* API Reference */}
        {activeSection === "api-reference" && (
          <ApiReference search={search} />
        )}

        {/* SDK */}
        {activeSection === "sdk" && (
          <div className="space-y-8">
            <div>
              <h2 className="text-xl font-bold text-foreground">Python SDK</h2>
              <p className="mt-2 text-sm text-muted-foreground">
                The official ASAHIO Python SDK wraps the gateway API with typed responses.
              </p>
            </div>
            <CodeBlock code="pip install asahio" />

            <div className="space-y-4">
              <h3 className="font-semibold text-foreground">Basic Usage</h3>
              <CodeBlock
                code={`from asahio import AsahioClient

client = AsahioClient(api_key="sk-...", base_url="https://api.asahio.dev")

# Simple completion
response = client.chat.completions.create(
    messages=[{"role": "user", "content": "What is ASAHIO?"}],
    routing_mode="AUTO",
    intervention_mode="ASSISTED",
)

# Access metadata
meta = response.asahio
print(f"Model: {meta.model_used}")
print(f"Cache hit: {meta.cache_hit}")
print(f"Savings: \${meta.savings_usd:.4f}")`}
              />
            </div>

            <div className="space-y-4">
              <h3 className="font-semibold text-foreground">Agent Sessions</h3>
              <CodeBlock
                code={`# Create a session for multi-step conversations
response = client.chat.completions.create(
    messages=[{"role": "user", "content": "Step 1 of my workflow"}],
    agent_id="your-agent-uuid",
    session_id="session-uuid",
    routing_mode="AUTO",
)

# Session graph tracks dependencies between steps`}
              />
            </div>

            <div className="space-y-4">
              <h3 className="font-semibold text-foreground">Explicit Model Routing</h3>
              <CodeBlock
                code={`# Pin to a specific model
response = client.chat.completions.create(
    messages=[{"role": "user", "content": "Important task"}],
    model="gpt-4o",
    routing_mode="EXPLICIT",
)`}
              />
            </div>

            <div className="rounded-lg border border-border p-4">
              <h3 className="font-semibold text-foreground mb-2">Backward Compatibility</h3>
              <p className="text-sm text-muted-foreground">
                The canonical package is <code className="text-foreground">asahio</code>. Legacy packages
                (<code className="text-foreground">asahi</code>, <code className="text-foreground">acorn</code>)
                are thin wrappers that re-export from <code className="text-foreground">asahio</code>.
                The <code className="text-foreground">response.asahio</code> metadata shape is stable — only new optional fields are added.
              </p>
            </div>
          </div>
        )}

        {/* CTA */}
        <section className="mt-12 rounded-xl border border-asahio/30 bg-asahio/5 p-8 text-center">
          <h2 className="text-2xl font-bold mb-3">Ready to start?</h2>
          <p className="text-muted-foreground mb-6">
            Create a free account to get your API key and access the full dashboard.
          </p>
          <div className="flex flex-wrap justify-center gap-3">
            <Link
              href="/sign-up"
              className="rounded-lg bg-asahio px-6 py-3 text-sm font-medium text-white transition-colors hover:bg-asahio-dark"
            >
              Create Account
            </Link>
            <Link
              href="/sign-in"
              className="rounded-lg border border-border px-6 py-3 text-sm font-medium text-foreground transition-colors hover:bg-muted"
            >
              Sign In
            </Link>
          </div>
        </section>
      </div>

      {/* Footer */}
      <footer className="border-t border-border bg-card px-6 py-8">
        <div className="mx-auto flex max-w-5xl items-center justify-between">
          <div className="flex items-center gap-2">
            <Image src="/asashio_logo-NB.png" alt="ASAHIO" width={18} height={18} className="rounded" />
            <p className="text-sm text-muted-foreground">
              &copy; {new Date().getFullYear()} ASAHIO. All rights reserved.
            </p>
          </div>
          <Link href="/" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
            Home
          </Link>
        </div>
      </footer>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Step component
// ---------------------------------------------------------------------------

function Step({ n, title, children }: { n: number; title: string; children: React.ReactNode }) {
  return (
    <div className="flex items-start gap-4">
      <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-asahio text-xs font-bold text-white">
        {n}
      </span>
      <div className="space-y-3 flex-1">
        <h3 className="font-semibold text-foreground">{title}</h3>
        {children}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// API Reference tab
// ---------------------------------------------------------------------------

function ApiReference({ search }: { search: string }) {
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

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-xl font-bold text-foreground">API Reference</h2>
        <p className="mt-2 text-sm text-muted-foreground">
          All endpoints require an API key via <code className="rounded bg-muted px-1.5 py-0.5 text-xs">Authorization: Bearer &lt;key&gt;</code> header.
        </p>
        {apiBase && (
          <div className="mt-3 flex flex-wrap gap-3">
            <a
              href={`${apiBase}/docs`}
              target="_blank"
              rel="noreferrer"
              className="rounded-lg bg-asahio px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-asahio-dark"
            >
              Open Interactive Docs
            </a>
            <a
              href={`${apiBase}/openapi.json`}
              target="_blank"
              rel="noreferrer"
              className="rounded-lg border border-border px-4 py-2 text-sm font-medium text-foreground transition-colors hover:bg-muted"
            >
              OpenAPI Schema
            </a>
          </div>
        )}
      </div>

      {filtered.length === 0 ? (
        <p className="text-sm text-muted-foreground">No endpoints match your search.</p>
      ) : (
        Array.from(categories.entries()).map(([cat, eps]) => (
          <div key={cat} className="space-y-2">
            <h3 className="text-sm font-semibold text-foreground">{cat}</h3>
            <div className="space-y-1">
              {eps.map((ep) => (
                <div key={`${ep.method} ${ep.path}`} className="flex items-center gap-3 rounded-lg border border-border px-4 py-3">
                  <span className={cn("rounded px-1.5 py-0.5 text-[10px] font-bold", METHOD_COLORS[ep.method])}>
                    {ep.method}
                  </span>
                  <span className="font-mono text-sm text-foreground">{ep.path}</span>
                  <ChevronRight className="h-3 w-3 text-muted-foreground ml-auto shrink-0 hidden sm:block" />
                  <span className="hidden sm:block text-xs text-muted-foreground max-w-xs truncate">{ep.description}</span>
                </div>
              ))}
            </div>
          </div>
        ))
      )}
    </div>
  );
}
