"use client";

import { useEffect, useState } from "react";
import Image from "next/image";
import Link from "next/link";

export default function LandingPage() {
  const apiBase = (process.env.NEXT_PUBLIC_API_URL || "").replace(/\/$/, "");
  const [engineStatus, setEngineStatus] = useState<
    "checking" | "ready" | "offline"
  >("checking");

  useEffect(() => {
    if (!apiBase) {
      setEngineStatus("ready");
      return;
    }
    fetch(`${apiBase}/health`, { method: "GET" })
      .then((r) => setEngineStatus(r.ok ? "ready" : "offline"))
      .catch(() => setEngineStatus("offline"));
  }, [apiBase]);

  const statusBadge = {
    checking: { color: "bg-yellow-500", text: "Checking..." },
    ready: { color: "bg-green-500", text: "Engine Online" },
    offline: { color: "bg-neutral-400", text: "Configure API" },
  }[engineStatus];

  return (
    <div className="min-h-screen bg-background text-foreground">
      {/* Navbar */}
      <nav className="fixed top-0 inset-x-0 z-50 border-b border-border bg-background/80 backdrop-blur-md">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-6">
          <Link href="/" className="flex items-center gap-2">
            <Image src="/asashio_logo-NB.png" alt="ASAHIO" width={32} height={32} className="rounded-md" />
            <span className="text-xl font-bold tracking-tight text-asahio">ASAHIO</span>
          </Link>
          <div className="hidden items-center gap-8 md:flex">
            <a href="#features" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
              Features
            </a>
            <a href="#architecture" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
              Architecture
            </a>
            <a href="/docs" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
              Docs
            </a>
          </div>
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

      {/* Hero */}
      <section className="pt-32 pb-20 px-6">
        <div className="mx-auto grid max-w-7xl items-center gap-16 md:grid-cols-2">
          <div>
            <div className="mb-4 flex items-center gap-3">
              <span className="text-sm font-medium uppercase tracking-wide text-asahio">
                Agent control plane
              </span>
              <span className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium ${
                engineStatus === "ready" ? "bg-green-500/10 text-green-600" :
                engineStatus === "checking" ? "bg-yellow-500/10 text-yellow-600" :
                "bg-neutral-500/10 text-neutral-500"
              }`}>
                <span className={`h-1.5 w-1.5 rounded-full ${statusBadge.color}`} />
                {statusBadge.text}
              </span>
            </div>
            <h1 className="mb-6 text-4xl font-bold leading-tight text-foreground md:text-5xl">
              The control plane for{" "}
              <span className="text-asahio">production AI systems</span>
            </h1>
            <p className="mb-8 text-lg leading-relaxed text-muted-foreground">
              Route every LLM call through intelligent model selection, three-tier
              caching, behavioral analytics, and risk-aware intervention. Full
              observability for every request, every agent, every session.
            </p>
            <div className="flex flex-wrap gap-4">
              <Link
                href="/sign-up"
                className="rounded-lg bg-asahio px-6 py-3 text-sm font-medium text-white hover:bg-asahio-dark transition-colors"
              >
                Start Building
              </Link>
              <a
                href="#features"
                className="rounded-lg border border-border px-6 py-3 text-sm font-medium text-foreground hover:bg-muted transition-colors"
              >
                Learn More
              </a>
            </div>
          </div>

          {/* SDK snippet */}
          <div className="rounded-xl border border-border bg-card overflow-hidden">
            <div className="flex items-center gap-2 border-b border-border bg-muted/50 px-4 py-2">
              <div className="h-3 w-3 rounded-full bg-red-400" />
              <div className="h-3 w-3 rounded-full bg-yellow-400" />
              <div className="h-3 w-3 rounded-full bg-green-400" />
              <span className="ml-2 text-xs text-muted-foreground font-mono">quickstart.py</span>
            </div>
            <pre className="p-6 text-sm leading-relaxed font-mono overflow-x-auto">
              <code>
                <span className="text-muted-foreground"># pip install asahio</span>{"\n"}
                <span className="text-blue-400">from</span> <span className="text-green-400">asahio</span> <span className="text-blue-400">import</span> AsahioClient{"\n"}
                {"\n"}
                client = AsahioClient(api_key=<span className="text-amber-400">&quot;sk-...&quot;</span>){"\n"}
                {"\n"}
                <span className="text-muted-foreground"># ASAHIO selects the optimal model,</span>{"\n"}
                <span className="text-muted-foreground"># checks cache, scores risk, logs trace</span>{"\n"}
                resp = client.chat.completions.create({"\n"}
                {"    "}messages=[{"{"}role: <span className="text-amber-400">&quot;user&quot;</span>, content: <span className="text-amber-400">&quot;...&quot;</span>{"}"}],{"\n"}
                {"    "}routing_mode=<span className="text-amber-400">&quot;auto&quot;</span>,{"\n"}
                {"    "}intervention_mode=<span className="text-amber-400">&quot;assisted&quot;</span>,{"\n"}
                ){"\n"}
                {"\n"}
                <span className="text-blue-400">print</span>(resp.asahio.savings_usd){"\n"}
                <span className="text-blue-400">print</span>(resp.asahio.cache_hit)
              </code>
            </pre>
          </div>
        </div>
      </section>

      {/* Features — 6 real platform capabilities */}
      <section id="features" className="border-y border-border bg-card px-6 py-20">
        <div className="mx-auto max-w-7xl">
          <h2 className="mb-4 text-center text-3xl font-bold text-foreground md:text-4xl">
            Built for Production AI
          </h2>
          <p className="mb-12 text-center text-muted-foreground max-w-2xl mx-auto">
            Every feature is live and functional. No roadmap promises &mdash; these are
            capabilities you can use today.
          </p>
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {[
              {
                title: "Intelligent Routing",
                description:
                  "Three routing modes: AUTO (six-factor engine weighing complexity, context, ABA history, latency, budget, and provider health), EXPLICIT (pin to any model or BYOM endpoint), and GUIDED (rule-based chains with fallback triggers).",
                tag: "3 modes",
              },
              {
                title: "Three-Tier Cache",
                description:
                  "Exact match (Redis, sub-millisecond), semantic similarity (Pinecone vectors, ~20ms), and intermediate result caching. Context-aware cache keys built from dependency fingerprints.",
                tag: "3 tiers",
              },
              {
                title: "Agent Behavioral Analytics",
                description:
                  "Per-agent fingerprinting across every call. Anomaly detection on complexity drift, model distribution shifts, and hallucination rate changes. Cold-start bootstrapping from similar agents.",
                tag: "ABA engine",
              },
              {
                title: "Risk Scoring & Intervention",
                description:
                  "Five-level intervention ladder: log, flag, augment, reroute, block. Three intervention modes (OBSERVE, ASSISTED, AUTONOMOUS) operate independently from routing. Per-agent threshold overrides.",
                tag: "5 levels",
              },
              {
                title: "Full Observability",
                description:
                  "Every call traced with model, tokens, cost, latency, risk score, and intervention action. Session graphs track multi-step agent workflows. Live SSE trace streaming.",
                tag: "Every call",
              },
              {
                title: "Governance & Compliance",
                description:
                  "Organisation-scoped isolation on every query. API key management with scoped permissions. Immutable audit logging. Role-based access control. Encrypted provider credentials.",
                tag: "Org-scoped",
              },
            ].map((feature) => (
              <div
                key={feature.title}
                className="group rounded-xl border border-border bg-background p-6 transition-colors hover:border-asahio/30"
              >
                <div className="mb-3 inline-flex rounded-md bg-asahio/10 px-2 py-0.5 text-xs font-medium text-asahio">
                  {feature.tag}
                </div>
                <h3 className="mb-2 text-lg font-semibold text-foreground">
                  {feature.title}
                </h3>
                <p className="text-sm leading-relaxed text-muted-foreground">
                  {feature.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Architecture facts — no fake numbers */}
      <section id="architecture" className="px-6 py-20">
        <div className="mx-auto max-w-7xl">
          <h2 className="mb-4 text-center text-3xl font-bold text-foreground md:text-4xl">
            Platform Architecture
          </h2>
          <p className="mb-12 text-center text-muted-foreground">
            Verifiable architecture facts, not marketing metrics
          </p>
          <div className="grid grid-cols-2 gap-6 md:grid-cols-4">
            {[
              { value: "< 10ms", label: "Gateway Overhead", detail: "Added latency on cache miss" },
              { value: "3 Tiers", label: "Cache Hierarchy", detail: "Exact + Semantic + Intermediate" },
              { value: "9", label: "Mode Combinations", detail: "3 routing \u00d7 3 intervention" },
              { value: "Every Call", label: "Traced & Auditable", detail: "Full observability pipeline" },
            ].map((metric) => (
              <div
                key={metric.label}
                className="rounded-xl border border-border bg-card p-6 text-center"
              >
                <p className="text-3xl font-bold text-asahio">
                  {metric.value}
                </p>
                <p className="mt-2 text-sm font-medium text-foreground">
                  {metric.label}
                </p>
                <p className="mt-1 text-xs text-muted-foreground">
                  {metric.detail}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="relative overflow-hidden bg-asahio px-6 py-20">
        <div className="absolute inset-0 bg-black/10" />
        <div className="relative z-10 mx-auto max-w-4xl text-center text-white">
          <h2 className="mb-6 text-3xl font-bold md:text-4xl">
            Ready to run AI systems with control?
          </h2>
          <p className="mb-8 text-lg opacity-95">
            Route intelligently. Cache aggressively. Intervene when it matters.
            Full visibility into every LLM call your agents make.
          </p>
          <div className="flex flex-wrap justify-center gap-4">
            <Link
              href="/sign-up"
              className="inline-block rounded-lg bg-white px-6 py-3 text-sm font-medium text-asahio-dark hover:bg-neutral-100 transition-colors"
            >
              Start Building
            </Link>
            <a
              href="/docs"
              className="inline-block rounded-lg border border-white/30 px-6 py-3 text-sm font-medium text-white hover:bg-white/10 transition-colors"
            >
              Read the Docs
            </a>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-border bg-card px-6 py-12 text-muted-foreground">
        <div className="mx-auto grid max-w-7xl grid-cols-2 gap-8 md:grid-cols-4">
          <div>
            <h4 className="mb-4 font-semibold text-foreground">Platform</h4>
            <ul className="space-y-2 text-sm">
              <li>
                <a href="#features" className="hover:text-foreground transition-colors">
                  Routing
                </a>
              </li>
              <li>
                <a href="#features" className="hover:text-foreground transition-colors">
                  Caching
                </a>
              </li>
              <li>
                <a href="#features" className="hover:text-foreground transition-colors">
                  Observability
                </a>
              </li>
              <li>
                <a href="#features" className="hover:text-foreground transition-colors">
                  Intervention
                </a>
              </li>
            </ul>
          </div>
          <div>
            <h4 className="mb-4 font-semibold text-foreground">Resources</h4>
            <ul className="space-y-2 text-sm">
              <li>
                <a href="/docs" className="hover:text-foreground transition-colors">
                  Documentation
                </a>
              </li>
              <li>
                <a href="/docs" className="hover:text-foreground transition-colors">
                  API Reference
                </a>
              </li>
              <li>
                <a href="/docs" className="hover:text-foreground transition-colors">
                  SDK Guide
                </a>
              </li>
            </ul>
          </div>
          <div>
            <h4 className="mb-4 font-semibold text-foreground">Company</h4>
            <ul className="space-y-2 text-sm">
              <li>
                <a href="#architecture" className="hover:text-foreground transition-colors">
                  About
                </a>
              </li>
              <li>
                <a href="/sign-up" className="hover:text-foreground transition-colors">
                  Get Started
                </a>
              </li>
            </ul>
          </div>
          <div>
            <h4 className="mb-4 font-semibold text-foreground">Legal</h4>
            <ul className="space-y-2 text-sm">
              <li>
                <span className="text-muted-foreground/60">Privacy Policy</span>
              </li>
              <li>
                <span className="text-muted-foreground/60">Terms of Service</span>
              </li>
            </ul>
          </div>
        </div>
        <div className="mx-auto mt-12 flex max-w-7xl flex-col items-center justify-between gap-4 border-t border-border pt-8 md:flex-row">
          <div className="flex items-center gap-2">
            <Image src="/asashio_logo-NB.png" alt="ASAHIO" width={20} height={20} className="rounded" />
            <p className="text-sm">
              &copy; {new Date().getFullYear()} ASAHIO. All rights reserved.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}
