"use client";

import { useState } from "react";
import { X, CheckCircle2, ArrowRight, Key, Bot, Code2, BarChart3 } from "lucide-react";
import { cn } from "@/lib/utils";
import { CodeSnippet } from "./code-snippet";

interface OnboardingWizardProps {
  onComplete: () => void;
  onDismiss: () => void;
}

const STEPS = [
  {
    id: "welcome",
    title: "Welcome to ASAHIO",
    description: "The control plane for production AI systems",
    icon: CheckCircle2,
  },
  {
    id: "api-key",
    title: "Get Your API Key",
    description: "Create an API key to start making requests",
    icon: Key,
  },
  {
    id: "create-agent",
    title: "Create Your First Agent",
    description: "Agents track calls, modes, and behavioral patterns",
    icon: Bot,
  },
  {
    id: "first-call",
    title: "Make Your First Call",
    description: "Send a request through the ASAHIO gateway",
    icon: Code2,
  },
  {
    id: "monitor",
    title: "Monitor & Analyze",
    description: "View traces, costs, and savings",
    icon: BarChart3,
  },
];

export function OnboardingWizard({ onComplete, onDismiss }: OnboardingWizardProps) {
  const [currentStep, setCurrentStep] = useState(0);
  const step = STEPS[currentStep];

  const nextStep = () => {
    if (currentStep < STEPS.length - 1) {
      setCurrentStep(currentStep + 1);
    } else {
      onComplete();
    }
  };

  const prevStep = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="relative w-full max-w-3xl max-h-[90vh] mx-4 rounded-xl border border-border bg-card shadow-2xl animate-fade-in flex flex-col">
        {/* Close button */}
        <button
          onClick={onDismiss}
          className="absolute right-4 top-4 rounded p-1 text-muted-foreground hover:text-foreground transition-colors"
        >
          <X className="h-5 w-5" />
        </button>

        {/* Progress bar */}
        <div className="border-b border-border bg-muted/30 px-8 py-4 shrink-0">
          <div className="flex items-center justify-between mb-3">
            {STEPS.map((s, idx) => (
              <div key={s.id} className="flex items-center">
                <button
                  onClick={() => setCurrentStep(idx)}
                  className={cn(
                    "flex h-8 w-8 items-center justify-center rounded-full text-xs font-bold transition-colors",
                    idx === currentStep
                      ? "bg-asahio text-white"
                      : idx < currentStep
                      ? "bg-green-500/20 text-green-500"
                      : "bg-muted text-muted-foreground"
                  )}
                >
                  {idx < currentStep ? "✓" : idx + 1}
                </button>
                {idx < STEPS.length - 1 && (
                  <div
                    className={cn(
                      "h-0.5 w-12 mx-2 transition-colors",
                      idx < currentStep ? "bg-green-500" : "bg-border"
                    )}
                  />
                )}
              </div>
            ))}
          </div>
          <p className="text-xs text-muted-foreground">
            Step {currentStep + 1} of {STEPS.length}
          </p>
        </div>

        {/* Content */}
        <div className="p-8 overflow-y-auto flex-1 min-h-0">
          <div className="mb-6 inline-flex h-12 w-12 items-center justify-center rounded-lg bg-asahio/10">
            <step.icon className="h-6 w-6 text-asahio" />
          </div>
          <h2 className="mb-2 text-2xl font-bold text-foreground">{step.title}</h2>
          <p className="mb-6 text-sm text-muted-foreground">{step.description}</p>

          {/* Step-specific content */}
          {currentStep === 0 && (
            <div className="space-y-4">
              <p className="text-sm text-muted-foreground">
                ASAHIO sits between your agents and LLMs, providing:
              </p>
              <ul className="space-y-2">
                {[
                  "Intelligent routing across 9 mode combinations",
                  "Three-tier caching (exact + semantic + intermediate)",
                  "Agent behavioral analytics and anomaly detection",
                  "Risk scoring and five-level intervention ladder",
                  "Full observability for every call",
                ].map((item) => (
                  <li key={item} className="flex items-start gap-2 text-sm text-muted-foreground">
                    <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-green-500" />
                    {item}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {currentStep === 1 && (
            <div className="space-y-4">
              <p className="text-sm text-muted-foreground">
                Navigate to the <strong className="text-foreground">API Keys</strong> page in the sidebar and create a new key.
                You'll only see the key once, so copy it immediately.
              </p>
              <div className="rounded-lg border border-asahio/30 bg-asahio/5 p-4">
                <p className="text-xs font-medium text-asahio mb-2">Pro Tip</p>
                <p className="text-xs text-muted-foreground">
                  Store your API key in an environment variable: <code className="rounded bg-muted px-1.5 py-0.5 font-mono text-foreground">ASAHIO_API_KEY</code>
                </p>
              </div>
            </div>
          )}

          {currentStep === 2 && (
            <div className="space-y-4">
              <p className="text-sm text-muted-foreground">
                Agents track routing modes, intervention settings, and behavioral patterns. Create one via the dashboard or SDK:
              </p>
              <CodeSnippet
                language="python"
                code={`from asahio import AsahioClient

client = AsahioClient(api_key="your-key")

agent = client.agents.create(
    name="My Agent",
    routing_mode="AUTO",
    intervention_mode="ASSISTED"
)`}
              />
              <p className="text-xs text-muted-foreground">
                <strong className="text-foreground">Routing modes:</strong> AUTO (6-factor engine), EXPLICIT (you pick), GUIDED (rules)
                <br />
                <strong className="text-foreground">Intervention modes:</strong> OBSERVE (watch only), ASSISTED (cache+augment), AUTONOMOUS (full control)
              </p>
            </div>
          )}

          {currentStep === 3 && (
            <div className="space-y-4">
              <p className="text-sm text-muted-foreground">
                Use the OpenAI-compatible endpoint to route requests through ASAHIO:
              </p>
              <CodeSnippet
                language="python"
                code={`response = client.chat.completions.create(
    messages=[
        {"role": "user", "content": "Explain quantum computing"}
    ],
    agent_id=agent.id,
    routing_mode="AUTO",
    intervention_mode="ASSISTED"
)

# Access ASAHIO metadata
meta = response.asahio
print(f"Model: {meta.model_used}")
print(f"Cache hit: {meta.cache_hit}")
print(f"Savings: \${meta.savings_usd:.4f}")
print(f"Risk score: {meta.risk_score}")`}
              />
            </div>
          )}

          {currentStep === 4 && (
            <div className="space-y-4">
              <p className="text-sm text-muted-foreground">
                View traces, analytics, and agent stats in the dashboard:
              </p>
              <ul className="space-y-2">
                {[
                  { label: "Traces", desc: "Every call with model, cost, latency, risk score" },
                  { label: "Analytics", desc: "Cost trends, savings breakdown, cache performance" },
                  { label: "Agent Stats", desc: "Per-agent call counts, cache hit rates, mode transitions" },
                  { label: "Interventions", desc: "Risk ladder actions (log, flag, augment, reroute, block)" },
                  { label: "ABA Dashboard", desc: "Behavioral fingerprints and anomaly detection" },
                ].map((item) => (
                  <li key={item.label} className="text-sm">
                    <strong className="text-foreground">{item.label}:</strong>{" "}
                    <span className="text-muted-foreground">{item.desc}</span>
                  </li>
                ))}
              </ul>
              <div className="rounded-lg border border-green-500/30 bg-green-500/5 p-4">
                <p className="text-xs font-medium text-green-500 mb-2">You're ready to go!</p>
                <p className="text-xs text-muted-foreground">
                  Check out the <a href="/docs" className="text-asahio hover:underline">documentation</a> for advanced features like
                  tool use, web search, MCP, fallback chains, and routing constraints.
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Actions */}
        <div className="flex items-center justify-between border-t border-border bg-muted/30 px-8 py-4 shrink-0">
          <button
            onClick={prevStep}
            disabled={currentStep === 0}
            className="text-sm font-medium text-muted-foreground hover:text-foreground disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            Back
          </button>
          <div className="flex gap-2">
            <button
              onClick={onDismiss}
              className="rounded-lg border border-border px-4 py-2 text-sm font-medium text-foreground hover:bg-muted transition-colors"
            >
              Skip Tutorial
            </button>
            <button
              onClick={nextStep}
              className="inline-flex items-center gap-2 rounded-lg bg-asahio px-4 py-2 text-sm font-medium text-white hover:bg-asahio-dark transition-colors"
            >
              {currentStep === STEPS.length - 1 ? "Get Started" : "Next"}
              <ArrowRight className="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
