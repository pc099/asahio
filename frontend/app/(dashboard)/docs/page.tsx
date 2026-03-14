import Link from "next/link";

const apiBase = (process.env.NEXT_PUBLIC_API_URL || "").replace(/\/$/, "");

export default function PublicDocsPage() {
  return (
    <div className="min-h-screen bg-background text-foreground">
      {/* Navbar */}
      <nav className="fixed top-0 inset-x-0 z-50 border-b border-border bg-background/80 backdrop-blur-md">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-6">
          <Link href="/" className="text-xl font-bold tracking-tight">
            <span className="text-asahio">ASAHIO</span>
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

      <div className="mx-auto max-w-4xl px-6 pt-28 pb-20">
        {/* Header */}
        <div className="mb-12">
          <p className="text-sm font-medium uppercase tracking-wide text-asahio">Documentation</p>
          <h1 className="mt-2 text-4xl font-bold">Getting Started with ASAHIO</h1>
          <p className="mt-4 max-w-2xl text-lg text-muted-foreground">
            ASAHIO is the control plane for production AI systems. Route LLM calls intelligently,
            cache semantically, observe every request, and cut inference costs by up to 87%.
          </p>
        </div>

        {/* Quick Start */}
        <section className="mb-10">
          <h2 className="text-2xl font-bold mb-4">Quick Start</h2>
          <div className="space-y-4">
            <div className="rounded-xl border border-border bg-card p-6">
              <h3 className="font-semibold text-foreground mb-2">1. Install the SDK</h3>
              <pre className="overflow-x-auto rounded-md border border-border bg-background p-4 text-sm font-mono text-foreground">
                <code>pip install asahio</code>
              </pre>
            </div>
            <div className="rounded-xl border border-border bg-card p-6">
              <h3 className="font-semibold text-foreground mb-2">2. Create a client</h3>
              <pre className="overflow-x-auto rounded-md border border-border bg-background p-4 text-sm font-mono text-foreground"><code>{`from asahio import Asahio

client = Asahio(
    api_key="asahio_live_your_key",
    org_slug="your-org",
)`}</code></pre>
            </div>
            <div className="rounded-xl border border-border bg-card p-6">
              <h3 className="font-semibold text-foreground mb-2">3. Make a request</h3>
              <pre className="overflow-x-auto rounded-md border border-border bg-background p-4 text-sm font-mono text-foreground"><code>{`response = client.chat.completions.create(
    messages=[{"role": "user", "content": "Hello!"}],
    routing_mode="AUTO",
    intervention_mode="OBSERVE",
)

print(response.choices[0].message.content)
print(response.asahio.model_used)
print(response.asahio.savings_usd)`}</code></pre>
              <p className="mt-3 text-sm text-muted-foreground">
                ASAHIO selects the cheapest model that meets your quality and latency constraints.
                The <code className="text-foreground">response.asahio</code> object shows which model was used and how much you saved.
              </p>
            </div>
          </div>
        </section>

        {/* Core Concepts */}
        <section className="mb-10">
          <h2 className="text-2xl font-bold mb-4">Core Concepts</h2>
          <div className="grid gap-6 md:grid-cols-2">
            <div className="rounded-xl border border-border bg-card p-6">
              <h3 className="font-semibold text-foreground mb-2">Routing Modes</h3>
              <p className="text-sm text-muted-foreground mb-3">How ASAHIO selects a model for each request.</p>
              <dl className="space-y-2 text-sm">
                <div>
                  <dt className="font-medium text-foreground">AUTO</dt>
                  <dd className="text-muted-foreground">Six-factor engine picks the optimal model based on complexity, context, latency, budget, and provider health.</dd>
                </div>
                <div>
                  <dt className="font-medium text-foreground">EXPLICIT</dt>
                  <dd className="text-muted-foreground">You specify the model directly. Supports model pinning and custom endpoints.</dd>
                </div>
                <div>
                  <dt className="font-medium text-foreground">GUIDED</dt>
                  <dd className="text-muted-foreground">Your rules: cost ceilings, provider allowlists, fallback chains, time-based routing.</dd>
                </div>
              </dl>
            </div>
            <div className="rounded-xl border border-border bg-card p-6">
              <h3 className="font-semibold text-foreground mb-2">Intervention Modes</h3>
              <p className="text-sm text-muted-foreground mb-3">How much ASAHIO is allowed to act on your requests.</p>
              <dl className="space-y-2 text-sm">
                <div>
                  <dt className="font-medium text-foreground">OBSERVE</dt>
                  <dd className="text-muted-foreground">Watch only. ASAHIO logs and observes but never modifies calls.</dd>
                </div>
                <div>
                  <dt className="font-medium text-foreground">ASSISTED</dt>
                  <dd className="text-muted-foreground">Serve cache hits, augment risky prompts, reroute when risk is high.</dd>
                </div>
                <div>
                  <dt className="font-medium text-foreground">AUTONOMOUS</dt>
                  <dd className="text-muted-foreground">Full intervention including blocking. Requires explicit agent authorization.</dd>
                </div>
              </dl>
            </div>
          </div>
        </section>

        {/* Caching */}
        <section className="mb-10">
          <h2 className="text-2xl font-bold mb-4">Two-Tier Caching</h2>
          <div className="rounded-xl border border-border bg-card p-6">
            <p className="text-sm text-muted-foreground mb-4">
              ASAHIO caches at two levels to reduce cost and latency automatically. No configuration required.
            </p>
            <div className="space-y-3 text-sm">
              <div className="flex gap-4">
                <span className="shrink-0 font-medium text-foreground w-40">Tier 1 &mdash; Exact Match</span>
                <span className="text-muted-foreground">Identical queries return instantly from Redis (~0.5ms). TTL 1 hour.</span>
              </div>
              <div className="flex gap-4">
                <span className="shrink-0 font-medium text-foreground w-40">Tier 2 &mdash; Semantic</span>
                <span className="text-muted-foreground">Similar queries matched via vector embeddings (~20ms). Threshold 85% similarity.</span>
              </div>
              <div className="flex gap-4">
                <span className="shrink-0 font-medium text-foreground w-40">Auto-promotion</span>
                <span className="text-muted-foreground">Semantic hits above 95% similarity are promoted to exact cache for faster repeat access.</span>
              </div>
            </div>
          </div>
        </section>

        {/* API Endpoints */}
        <section className="mb-10">
          <h2 className="text-2xl font-bold mb-4">API Reference</h2>
          <div className="rounded-xl border border-border bg-card p-6">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-border">
                    <th className="pb-3 pr-4 font-medium text-muted-foreground">Endpoint</th>
                    <th className="pb-3 font-medium text-muted-foreground">Purpose</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  <tr><td className="py-2.5 pr-4 font-mono text-xs text-foreground">POST /v1/chat/completions</td><td className="py-2.5 text-muted-foreground">Gateway &mdash; send LLM requests through ASAHIO</td></tr>
                  <tr><td className="py-2.5 pr-4 font-mono text-xs text-foreground">GET /agents/*</td><td className="py-2.5 text-muted-foreground">Agent lifecycle &mdash; register, configure, list agents</td></tr>
                  <tr><td className="py-2.5 pr-4 font-mono text-xs text-foreground">GET /models/*</td><td className="py-2.5 text-muted-foreground">Model registry &mdash; BYOM endpoints, health, fallbacks</td></tr>
                  <tr><td className="py-2.5 pr-4 font-mono text-xs text-foreground">GET /routing/*</td><td className="py-2.5 text-muted-foreground">Routing rules &mdash; constraints, guided rules, decision audit</td></tr>
                  <tr><td className="py-2.5 pr-4 font-mono text-xs text-foreground">GET /billing/*</td><td className="py-2.5 text-muted-foreground">Billing &mdash; plans, usage, invoices, checkout</td></tr>
                  <tr><td className="py-2.5 pr-4 font-mono text-xs text-foreground">GET /analytics/*</td><td className="py-2.5 text-muted-foreground">Analytics &mdash; cost breakdown, trends, forecasting</td></tr>
                  <tr><td className="py-2.5 pr-4 font-mono text-xs text-foreground">GET /governance/*</td><td className="py-2.5 text-muted-foreground">Governance &mdash; audit log, policies, compliance</td></tr>
                </tbody>
              </table>
            </div>
            {apiBase && (
              <div className="mt-4 flex flex-wrap gap-3">
                <a
                  href={`${apiBase}/docs`}
                  target="_blank"
                  rel="noreferrer"
                  className="rounded-lg bg-asahio px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-asahio-dark"
                >
                  Open Interactive API Docs
                </a>
                <a
                  href={`${apiBase}/openapi.json`}
                  target="_blank"
                  rel="noreferrer"
                  className="rounded-lg border border-border px-4 py-2 text-sm font-medium text-foreground transition-colors hover:bg-muted"
                >
                  OpenAPI Schema (JSON)
                </a>
              </div>
            )}
          </div>
        </section>

        {/* Authentication */}
        <section className="mb-10">
          <h2 className="text-2xl font-bold mb-4">Authentication</h2>
          <div className="rounded-xl border border-border bg-card p-6 space-y-4">
            <p className="text-sm text-muted-foreground">
              All API requests require an API key passed in the <code className="text-foreground">Authorization</code> header.
            </p>
            <pre className="overflow-x-auto rounded-md border border-border bg-background p-4 text-sm font-mono text-foreground"><code>{`curl -X POST https://api.asahio.com/v1/chat/completions \\
  -H "Authorization: Bearer asahio_live_your_key" \\
  -H "Content-Type: application/json" \\
  -d '{"messages": [{"role": "user", "content": "Hello"}]}'`}</code></pre>
            <p className="text-sm text-muted-foreground">
              API keys are created in the dashboard under <strong>API Keys</strong>. Keys use the <code className="text-foreground">asahio_</code> prefix.
              Legacy <code className="text-foreground">asahi_</code> keys continue to work during the deprecation window.
            </p>
          </div>
        </section>

        {/* CTA */}
        <section className="rounded-xl border border-asahio/30 bg-asahio/5 p-8 text-center">
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
      <footer className="border-t border-border bg-card px-6 py-8 text-center text-sm text-muted-foreground">
        <p>&copy; {new Date().getFullYear()} ASAHIO. All rights reserved.</p>
      </footer>
    </div>
  );
}
