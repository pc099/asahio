"use client";

import { useEffect, useState } from "react";
import Image from "next/image";
import Link from "next/link";
import {
  Eye,
  GitBranch,
  Shield,
  TrendingDown,
  Database,
  Activity,
  Lock,
  CheckCircle2,
  DollarSign,
  Zap,
  Clock,
  BarChart3,
} from "lucide-react";

export default function LandingPage() {
  const apiBase = (process.env.NEXT_PUBLIC_API_URL || "").replace(/\/$/, "");
  const [engineStatus, setEngineStatus] = useState<
    "checking" | "ready" | "offline"
  >("checking");

  // Savings calculator state
  const [monthlyRequests, setMonthlyRequests] = useState(100000);
  const [avgCost, setAvgCost] = useState(0.002);

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

  // Calculate savings
  const baseCost = monthlyRequests * avgCost;
  const cacheHitRate = 0.35; // Conservative 35% cache hit rate
  const routingSavings = 0.40; // 40% savings from intelligent routing
  const totalSavings = baseCost * (cacheHitRate + routingSavings * (1 - cacheHitRate));
  const annualSavings = totalSavings * 12;

  return (
    <div className="min-h-screen bg-background text-foreground">
      {/* Navbar */}
      <nav className="fixed top-0 inset-x-0 z-50 border-b border-border bg-background/80 backdrop-blur-md">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-6">
          <Link href="/" className="flex items-center gap-2">
            <Image src="/asashio_logo-NB.png" alt="ASAHIO" width={48} height={48} className="rounded-md" />
            <span className="text-xl font-bold tracking-tight text-asahio">ASAHIO</span>
          </Link>
          <div className="hidden items-center gap-8 md:flex">
            <a href="#how-it-works" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
              How It Works
            </a>
            <a href="#features" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
              Features
            </a>
            <a href="#savings" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
              Calculator
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
                href="#how-it-works"
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

      {/* Problem/Solution */}
      <section className="border-y border-border bg-muted/30 px-6 py-20">
        <div className="mx-auto max-w-7xl">
          <div className="grid gap-12 md:grid-cols-2">
            {/* Problem */}
            <div>
              <div className="mb-4 inline-flex items-center gap-2 rounded-full bg-red-500/10 px-3 py-1 text-sm font-medium text-red-600">
                <span className="h-2 w-2 rounded-full bg-red-500" />
                The Problem
              </div>
              <h2 className="mb-6 text-2xl font-bold text-foreground">
                AI systems are expensive, opaque, and risky
              </h2>
              <ul className="space-y-4">
                {[
                  "No visibility into model selection or cost drivers",
                  "Repeated identical queries waste thousands in API calls",
                  "Agents can drift into high-cost or risky behavior patterns",
                  "No central place to intervene when things go wrong",
                  "Multi-step workflows are black boxes",
                ].map((problem) => (
                  <li key={problem} className="flex items-start gap-3">
                    <span className="mt-1 h-5 w-5 shrink-0 rounded-full bg-red-500/20 flex items-center justify-center">
                      <span className="h-2 w-2 rounded-full bg-red-500" />
                    </span>
                    <span className="text-sm text-muted-foreground">{problem}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* Solution */}
            <div>
              <div className="mb-4 inline-flex items-center gap-2 rounded-full bg-green-500/10 px-3 py-1 text-sm font-medium text-green-600">
                <CheckCircle2 className="h-3.5 w-3.5" />
                The Solution
              </div>
              <h2 className="mb-6 text-2xl font-bold text-foreground">
                ASAHIO gives you complete control
              </h2>
              <ul className="space-y-4">
                {[
                  "Every call traced with model, cost, latency, and risk score",
                  "35%+ cache hit rate on production workloads",
                  "Agent behavioral analytics detect drift before it costs you",
                  "Five-level intervention ladder from observe to block",
                  "Session graphs show dependencies across multi-step workflows",
                ].map((solution) => (
                  <li key={solution} className="flex items-start gap-3">
                    <CheckCircle2 className="mt-0.5 h-5 w-5 shrink-0 text-green-500" />
                    <span className="text-sm text-muted-foreground">{solution}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* Three Pillars */}
      <section id="how-it-works" className="px-6 py-20">
        <div className="mx-auto max-w-7xl">
          <h2 className="mb-4 text-center text-3xl font-bold text-foreground md:text-4xl">
            Three Pillars of Control
          </h2>
          <p className="mb-16 text-center text-muted-foreground max-w-2xl mx-auto">
            ASAHIO sits between your agents and LLMs, providing intelligent routing, caching, and intervention on every call
          </p>
          <div className="grid gap-8 md:grid-cols-3">
            {[
              {
                icon: Eye,
                title: "Observe",
                color: "bg-blue-500",
                description: "Full observability for every LLM call",
                features: [
                  "Trace every request with model, tokens, cost, latency",
                  "Session graphs track multi-step agent workflows",
                  "Agent behavioral analytics fingerprint patterns",
                  "Real-time anomaly detection on drift",
                ],
              },
              {
                icon: GitBranch,
                title: "Route",
                color: "bg-green-500",
                description: "Intelligent model selection and caching",
                features: [
                  "AUTO mode: 6-factor engine picks optimal model",
                  "EXPLICIT mode: Pin to specific models or BYOM",
                  "GUIDED mode: Rule-based chains with fallbacks",
                  "3-tier cache: Exact + Semantic + Intermediate",
                ],
              },
              {
                icon: Shield,
                title: "Intervene",
                color: "bg-amber-500",
                description: "Risk-aware intervention when it matters",
                features: [
                  "5-level ladder: Log → Flag → Augment → Reroute → Block",
                  "OBSERVE mode: Watch only, zero intervention",
                  "ASSISTED mode: Cache hits + prompt augmentation",
                  "AUTONOMOUS mode: Full control with authorization",
                ],
              },
            ].map((pillar) => (
              <div
                key={pillar.title}
                className="rounded-xl border border-border bg-card p-8 hover:border-asahio/30 transition-colors"
              >
                <div className={`mb-4 inline-flex h-12 w-12 items-center justify-center rounded-lg ${pillar.color}/20`}>
                  <pillar.icon className={`h-6 w-6 text-${pillar.color.replace('bg-', '')}`} />
                </div>
                <h3 className="mb-2 text-xl font-bold text-foreground">{pillar.title}</h3>
                <p className="mb-4 text-sm text-muted-foreground">{pillar.description}</p>
                <ul className="space-y-2">
                  {pillar.features.map((feature) => (
                    <li key={feature} className="flex items-start gap-2 text-xs text-muted-foreground">
                      <span className="mt-1 h-1 w-1 shrink-0 rounded-full bg-asahio" />
                      {feature}
                    </li>
                  ))}
                </ul>
              </div>
            ))}
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
                icon: GitBranch,
              },
              {
                title: "Three-Tier Cache",
                description:
                  "Exact match (Redis, sub-millisecond), semantic similarity (Pinecone vectors, ~20ms), and intermediate result caching. Context-aware cache keys built from dependency fingerprints.",
                tag: "3 tiers",
                icon: Database,
              },
              {
                title: "Agent Behavioral Analytics",
                description:
                  "Per-agent fingerprinting across every call. Anomaly detection on complexity drift, model distribution shifts, and hallucination rate changes. Cold-start bootstrapping from similar agents.",
                tag: "ABA engine",
                icon: Activity,
              },
              {
                title: "Risk Scoring & Intervention",
                description:
                  "Five-level intervention ladder: log, flag, augment, reroute, block. Three intervention modes (OBSERVE, ASSISTED, AUTONOMOUS) operate independently from routing. Per-agent threshold overrides.",
                tag: "5 levels",
                icon: Shield,
              },
              {
                title: "Full Observability",
                description:
                  "Every call traced with model, tokens, cost, latency, risk score, and intervention action. Session graphs track multi-step agent workflows. Live SSE trace streaming.",
                tag: "Every call",
                icon: Eye,
              },
              {
                title: "Governance & Compliance",
                description:
                  "Organisation-scoped isolation on every query. API key management with scoped permissions. Immutable audit logging. Role-based access control. Encrypted provider credentials.",
                tag: "Org-scoped",
                icon: Lock,
              },
            ].map((feature) => (
              <div
                key={feature.title}
                className="group rounded-xl border border-border bg-background p-6 transition-colors hover:border-asahio/30"
              >
                <div className="mb-4 flex items-center justify-between">
                  <div className="inline-flex h-10 w-10 items-center justify-center rounded-lg bg-asahio/10">
                    <feature.icon className="h-5 w-5 text-asahio" />
                  </div>
                  <span className="inline-flex rounded-md bg-asahio/10 px-2 py-0.5 text-xs font-medium text-asahio">
                    {feature.tag}
                  </span>
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

      {/* Savings Calculator */}
      <section id="savings" className="px-6 py-20">
        <div className="mx-auto max-w-4xl">
          <h2 className="mb-4 text-center text-3xl font-bold text-foreground md:text-4xl">
            Calculate Your Savings
          </h2>
          <p className="mb-12 text-center text-muted-foreground">
            Conservative estimates based on 35% cache hit rate and 40% routing optimization
          </p>
          <div className="rounded-xl border border-border bg-card p-8">
            <div className="grid gap-8 md:grid-cols-2">
              {/* Inputs */}
              <div className="space-y-6">
                <div>
                  <label className="mb-2 block text-sm font-medium text-foreground">
                    Monthly LLM Requests
                  </label>
                  <input
                    type="number"
                    value={monthlyRequests}
                    onChange={(e) => setMonthlyRequests(parseInt(e.target.value) || 0)}
                    className="w-full rounded-lg border border-border bg-background px-4 py-2 text-foreground"
                  />
                  <p className="mt-1 text-xs text-muted-foreground">
                    Total number of LLM API calls per month
                  </p>
                </div>
                <div>
                  <label className="mb-2 block text-sm font-medium text-foreground">
                    Average Cost per Request
                  </label>
                  <div className="relative">
                    <span className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground">$</span>
                    <input
                      type="number"
                      step="0.0001"
                      value={avgCost}
                      onChange={(e) => setAvgCost(parseFloat(e.target.value) || 0)}
                      className="w-full rounded-lg border border-border bg-background px-4 py-2 pl-7 text-foreground"
                    />
                  </div>
                  <p className="mt-1 text-xs text-muted-foreground">
                    Current average cost per LLM call
                  </p>
                </div>
              </div>

              {/* Results */}
              <div className="space-y-4">
                <div className="rounded-lg border border-border bg-muted/30 p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <DollarSign className="h-4 w-4 text-muted-foreground" />
                    <span className="text-sm font-medium text-muted-foreground">Current Monthly Cost</span>
                  </div>
                  <p className="text-2xl font-bold text-foreground">
                    ${baseCost.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                  </p>
                </div>
                <div className="rounded-lg border border-asahio/30 bg-asahio/5 p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <TrendingDown className="h-4 w-4 text-asahio" />
                    <span className="text-sm font-medium text-asahio">Monthly Savings with ASAHIO</span>
                  </div>
                  <p className="text-2xl font-bold text-asahio">
                    ${totalSavings.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                  </p>
                  <p className="mt-1 text-xs text-muted-foreground">
                    {((totalSavings / baseCost) * 100).toFixed(0)}% reduction
                  </p>
                </div>
                <div className="rounded-lg border border-border bg-background p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <BarChart3 className="h-4 w-4 text-muted-foreground" />
                    <span className="text-sm font-medium text-muted-foreground">Annual Savings</span>
                  </div>
                  <p className="text-2xl font-bold text-foreground">
                    ${annualSavings.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                  </p>
                </div>
              </div>
            </div>
            <div className="mt-6 rounded-lg bg-muted/30 p-4">
              <p className="text-xs text-muted-foreground">
                <strong>Calculation:</strong> 35% cache hit rate + 40% savings on routed calls.
                Actual savings vary based on workload characteristics, model mix, and cache effectiveness.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Architecture facts */}
      <section className="border-y border-border bg-muted/30 px-6 py-20">
        <div className="mx-auto max-w-7xl">
          <h2 className="mb-4 text-center text-3xl font-bold text-foreground md:text-4xl">
            Platform Architecture
          </h2>
          <p className="mb-12 text-center text-muted-foreground">
            Verifiable architecture facts, not marketing metrics
          </p>
          <div className="grid grid-cols-2 gap-6 md:grid-cols-4">
            {[
              { value: "< 10ms", label: "Gateway Overhead", detail: "Added latency on cache miss", icon: Zap },
              { value: "3 Tiers", label: "Cache Hierarchy", detail: "Exact + Semantic + Intermediate", icon: Database },
              { value: "9", label: "Mode Combinations", detail: "3 routing × 3 intervention", icon: GitBranch },
              { value: "Every Call", label: "Traced & Auditable", detail: "Full observability pipeline", icon: Activity },
            ].map((metric) => (
              <div
                key={metric.label}
                className="rounded-xl border border-border bg-card p-6 text-center"
              >
                <div className="mx-auto mb-3 inline-flex h-10 w-10 items-center justify-center rounded-lg bg-asahio/10">
                  <metric.icon className="h-5 w-5 text-asahio" />
                </div>
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

      {/* Trust Signals */}
      <section className="px-6 py-20">
        <div className="mx-auto max-w-7xl">
          <h2 className="mb-4 text-center text-3xl font-bold text-foreground md:text-4xl">
            Enterprise-Ready
          </h2>
          <p className="mb-12 text-center text-muted-foreground max-w-2xl mx-auto">
            Built for production workloads with security and compliance at the core
          </p>
          <div className="grid gap-6 md:grid-cols-3">
            {[
              {
                title: "SOC 2 Ready",
                description: "Immutable audit logs, role-based access control, and encrypted credentials at rest",
                icon: Lock,
              },
              {
                title: "HIPAA Compliant Infrastructure",
                description: "Org-scoped data isolation, encrypted storage, and configurable data retention policies",
                icon: Shield,
              },
              {
                title: "99.9% Uptime SLA",
                description: "Multi-region deployment, automatic failover, and real-time health monitoring",
                icon: Clock,
              },
            ].map((trust) => (
              <div
                key={trust.title}
                className="rounded-xl border border-border bg-card p-6 text-center"
              >
                <div className="mx-auto mb-4 inline-flex h-12 w-12 items-center justify-center rounded-lg bg-green-500/10">
                  <trust.icon className="h-6 w-6 text-green-500" />
                </div>
                <h3 className="mb-2 text-lg font-semibold text-foreground">{trust.title}</h3>
                <p className="text-sm text-muted-foreground">{trust.description}</p>
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
                <a href="#how-it-works" className="hover:text-foreground transition-colors">
                  Routing
                </a>
              </li>
              <li>
                <a href="#how-it-works" className="hover:text-foreground transition-colors">
                  Caching
                </a>
              </li>
              <li>
                <a href="#how-it-works" className="hover:text-foreground transition-colors">
                  Observability
                </a>
              </li>
              <li>
                <a href="#how-it-works" className="hover:text-foreground transition-colors">
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
                <a href="#how-it-works" className="hover:text-foreground transition-colors">
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
            <Image src="/asashio_logo-NB.png" alt="ASAHIO" width={32} height={32} className="rounded" />
            <p className="text-sm">
              &copy; {new Date().getFullYear()} ASAHIO. All rights reserved.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}
