"use client";

import { useMutation, useQuery } from "@tanstack/react-query";
import { useParams } from "next/navigation";
import { createBillingCheckout, getBillingPlans, getBillingSubscription } from "@/lib/api";
import { cn, formatCurrency, formatNumber } from "@/lib/utils";

export default function BillingUpgradePage() {
  const params = useParams();
  const orgSlug = typeof params?.orgSlug === "string" ? params.orgSlug : "";
  const { data: plans, isLoading } = useQuery({
    queryKey: ["billing-plans", orgSlug],
    queryFn: () => getBillingPlans(undefined, orgSlug),
  });

  const { data: subscription } = useQuery({
    queryKey: ["billing-subscription", orgSlug, "upgrade"],
    queryFn: () => getBillingSubscription(undefined, orgSlug),
  });

  const checkoutMutation = useMutation({
    mutationFn: (plan: string) =>
      createBillingCheckout(
        {
          plan,
          success_url: `${window.location.origin}/${orgSlug}/billing?checkout=success`,
          cancel_url: `${window.location.origin}/${orgSlug}/billing/upgrade?checkout=cancelled`,
        },
        undefined,
        orgSlug
      ),
    onSuccess: (data) => {
      window.location.href = data.checkout_url;
    },
  });

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Upgrade</h1>
        <p className="text-sm text-muted-foreground">
          Choose the commercial layer that matches your traffic, compliance posture, and routing needs.
        </p>
      </div>

      {isLoading || !plans ? (
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
          {[1, 2, 3].map((item) => (
            <div key={item} className="rounded-lg border border-border bg-card p-6 shadow-sm">
              <div className="animate-pulse space-y-3">
                <div className="h-5 w-24 rounded bg-muted" />
                <div className="h-10 w-32 rounded bg-muted" />
                <div className="h-4 w-full rounded bg-muted" />
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
          {plans.map((plan) => {
            const isCurrent = subscription?.plan === plan.id;
            const isEnterprise = plan.id === "enterprise";
            return (
              <div
                key={plan.id}
                className={cn(
                  "rounded-lg border bg-card p-6 shadow-sm",
                  isCurrent ? "border-asahio bg-asahio/5" : "border-border"
                )}
              >
                <div className="flex items-start justify-between">
                  <div>
                    <p className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">{plan.id}</p>
                    <h2 className="mt-1 text-2xl font-bold text-foreground">{plan.name}</h2>
                  </div>
                  {isCurrent && (
                    <span className="rounded-full bg-asahio px-2 py-1 text-xs font-medium text-white">Current</span>
                  )}
                </div>
                <p className="mt-4 text-3xl font-bold text-foreground">
                  {plan.price_monthly_usd == null ? "Custom" : formatCurrency(plan.price_monthly_usd)}
                  <span className="text-sm font-normal text-muted-foreground">{plan.price_monthly_usd == null ? "" : "/month"}</span>
                </p>
                <div className="mt-4 space-y-2 text-sm text-muted-foreground">
                  <p>Requests: {plan.monthly_request_limit < 0 ? "Unlimited" : formatNumber(plan.monthly_request_limit)}</p>
                  <p>Tokens: {plan.monthly_token_limit < 0 ? "Unlimited" : formatNumber(plan.monthly_token_limit)}</p>
                  <p>Budget: {plan.monthly_budget_usd == null ? "Custom" : formatCurrency(plan.monthly_budget_usd)}</p>
                </div>
                <ul className="mt-6 space-y-2 text-sm text-muted-foreground">
                  {plan.features.map((feature) => (
                    <li key={feature} className="flex items-center gap-2">
                      <div className="h-1.5 w-1.5 rounded-full bg-asahio" />
                      {feature}
                    </li>
                  ))}
                </ul>
                <button
                  onClick={() => {
                    if (isEnterprise) {
                      window.location.href = "mailto:sales@asahio.dev?subject=ASAHIO%20Enterprise";
                      return;
                    }
                    checkoutMutation.mutate(plan.id);
                  }}
                  disabled={isCurrent || checkoutMutation.isPending || plan.id === "free"}
                  className="mt-6 w-full rounded-md bg-asahio px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-asahio-dark disabled:opacity-50"
                >
                  {isCurrent ? "Already active" : isEnterprise ? "Contact sales" : plan.id === "free" ? "Included by default" : `Choose ${plan.name}`}
                </button>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}


