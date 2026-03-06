"use client";

import Link from "next/link";
import { useMutation, useQuery } from "@tanstack/react-query";
import { useParams } from "next/navigation";
import {
  createBillingCheckout,
  createBillingPortal,
  getBillingInvoices,
  getBillingSubscription,
  getBillingUsage,
} from "@/lib/api";
import { cn, formatCurrency, formatNumber } from "@/lib/utils";
import { ArrowUpRight, CreditCard, FileText, Gauge, Receipt } from "lucide-react";

function usageColor(pct: number) {
  if (pct >= 95) return "bg-red-500";
  if (pct >= 80) return "bg-amber-400";
  return "bg-asahio";
}

export default function BillingPage() {
  const params = useParams();
  const orgSlug = typeof params?.orgSlug === "string" ? params.orgSlug : "";
  const { data: subscription, isLoading: subscriptionLoading } = useQuery({
    queryKey: ["billing-subscription", orgSlug],
    queryFn: () => getBillingSubscription(undefined, orgSlug),
  });

  const { data: usage, isLoading: usageLoading } = useQuery({
    queryKey: ["billing-usage", orgSlug],
    queryFn: () => getBillingUsage(undefined, orgSlug),
    refetchInterval: 30_000,
  });

  const { data: invoices, isLoading: invoicesLoading } = useQuery({
    queryKey: ["billing-invoices", orgSlug],
    queryFn: () => getBillingInvoices(undefined, orgSlug),
  });

  const checkoutMutation = useMutation({
    mutationFn: () =>
      createBillingCheckout(
        {
          plan: "pro",
          success_url: `${window.location.origin}/${orgSlug}/billing?checkout=success`,
          cancel_url: `${window.location.origin}/${orgSlug}/billing?checkout=cancelled`,
        },
        undefined,
        orgSlug
      ),
    onSuccess: (data) => {
      window.location.href = data.checkout_url;
    },
  });

  const portalMutation = useMutation({
    mutationFn: () =>
      createBillingPortal(
        {
          return_url: `${window.location.origin}/${orgSlug}/billing`,
        },
        undefined,
        orgSlug
      ),
    onSuccess: (data) => {
      window.location.href = data.portal_url;
    },
  });

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Billing</h1>
          <p className="text-sm text-muted-foreground">
            Track plan status, live usage, invoices, and Stripe-backed upgrade flows.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Link
            href={`/${orgSlug}/billing/upgrade`}
            className="rounded-md border border-border px-4 py-2 text-sm font-medium text-foreground transition-colors hover:bg-muted"
          >
            Compare plans
          </Link>
          <button
            onClick={() => portalMutation.mutate()}
            disabled={portalMutation.isPending || subscriptionLoading}
            className="rounded-md bg-asahio px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-asahio-dark disabled:opacity-50"
          >
            Manage billing
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <div className="rounded-lg border border-border bg-card p-6 shadow-sm lg:col-span-2">
          <div className="flex items-center gap-2 text-sm font-semibold text-foreground">
            <CreditCard className="h-4 w-4 text-asahio" />
            Subscription
          </div>
          {subscriptionLoading || !subscription ? (
            <div className="mt-4 animate-pulse space-y-3">
              <div className="h-5 w-40 rounded bg-muted" />
              <div className="h-4 w-full rounded bg-muted" />
              <div className="h-4 w-3/4 rounded bg-muted" />
            </div>
          ) : (
            <div className="mt-4 space-y-4">
              <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <p className="text-2xl font-bold text-foreground">{subscription.plan_name}</p>
                  <p className="text-sm text-muted-foreground">
                    Status: <span className="font-medium text-foreground">{subscription.status}</span>
                  </p>
                </div>
                <div className="rounded-lg border border-border bg-background px-4 py-3 text-right">
                  <p className="text-xs uppercase tracking-wide text-muted-foreground">Meter</p>
                  <p className="text-sm font-medium text-foreground">{subscription.meter_name}</p>
                </div>
              </div>
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                <InfoTile label="Request limit" value={subscription.monthly_request_limit < 0 ? "Unlimited" : formatNumber(subscription.monthly_request_limit)} />
                <InfoTile label="Token limit" value={subscription.monthly_token_limit < 0 ? "Unlimited" : formatNumber(subscription.monthly_token_limit)} />
                <InfoTile label="Budget cap" value={subscription.monthly_budget_usd == null ? "Custom" : formatCurrency(subscription.monthly_budget_usd)} />
                <InfoTile label="Stripe mode" value={subscription.stripe_enabled ? "Enabled" : "Mock/local"} />
              </div>
              <div className="space-y-2">
                <p className="text-sm font-medium text-foreground">Included features</p>
                <ul className="space-y-2 text-sm text-muted-foreground">
                  {subscription.features.map((feature) => (
                    <li key={feature} className="flex items-center gap-2">
                      <div className="h-1.5 w-1.5 rounded-full bg-asahio" />
                      {feature}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          )}
        </div>

        <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
          <div className="flex items-center gap-2 text-sm font-semibold text-foreground">
            <ArrowUpRight className="h-4 w-4 text-asahio" />
            Upgrade path
          </div>
          <div className="mt-4 space-y-3 text-sm text-muted-foreground">
            <p>
              Move to Pro when you need routed production traffic, billing visibility, and decision logs.
            </p>
            <button
              onClick={() => checkoutMutation.mutate()}
              disabled={checkoutMutation.isPending || subscription?.plan === "pro" || subscription?.plan === "enterprise"}
              className="w-full rounded-md bg-asahio px-4 py-2 font-medium text-white transition-colors hover:bg-asahio-dark disabled:opacity-50"
            >
              {subscription?.plan === "pro" || subscription?.plan === "enterprise" ? "Current plan active" : "Upgrade to Pro"}
            </button>
            <p className="text-xs text-muted-foreground">
              Enterprise remains a manual sales flow because BYOM, compliance routing, and support terms vary by org.
            </p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
          <div className="flex items-center gap-2 text-sm font-semibold text-foreground">
            <Gauge className="h-4 w-4 text-asahio" />
            This month
          </div>
          {usageLoading || !usage ? (
            <div className="mt-4 animate-pulse space-y-3">
              <div className="h-4 w-full rounded bg-muted" />
              <div className="h-4 w-4/5 rounded bg-muted" />
              <div className="h-4 w-3/5 rounded bg-muted" />
            </div>
          ) : (
            <div className="mt-4 space-y-5">
              <UsageBar label="Requests" used={usage.requests_used} limit={usage.request_limit} pct={usage.request_usage_pct} />
              <UsageBar label="Tokens" used={usage.tokens_used} limit={usage.token_limit} pct={usage.token_usage_pct} />
              <InfoTile label="Spend with ASAHIO" value={formatCurrency(usage.spend_usd)} />
            </div>
          )}
        </div>

        <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
          <div className="flex items-center gap-2 text-sm font-semibold text-foreground">
            <Receipt className="h-4 w-4 text-asahio" />
            Invoice history
          </div>
          {invoicesLoading ? (
            <div className="mt-4 animate-pulse space-y-3">
              <div className="h-10 rounded bg-muted" />
              <div className="h-10 rounded bg-muted" />
              <div className="h-10 rounded bg-muted" />
            </div>
          ) : !invoices || invoices.data.length === 0 ? (
            <div className="mt-4 flex h-40 items-center justify-center rounded-lg border border-dashed border-border text-sm text-muted-foreground">
              No invoices yet. They will appear here after paid billing starts.
            </div>
          ) : (
            <div className="mt-4 space-y-3">
              {invoices.data.map((invoice) => (
                <div key={invoice.id} className="flex items-center justify-between rounded-lg border border-border bg-background px-4 py-3">
                  <div>
                    <p className="text-sm font-medium text-foreground">{invoice.id}</p>
                    <p className="text-xs text-muted-foreground">{new Date(invoice.created_at).toLocaleDateString()} • {invoice.status}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-medium text-foreground">{formatCurrency(invoice.amount_paid || invoice.amount_due)}</p>
                    {invoice.hosted_invoice_url && (
                      <a href={invoice.hosted_invoice_url} target="_blank" rel="noreferrer" className="text-xs text-asahio hover:underline">
                        Open invoice
                      </a>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
        <div className="flex items-center gap-2 text-sm font-semibold text-foreground">
          <FileText className="h-4 w-4 text-asahio" />
          Billing notes
        </div>
        <ul className="mt-4 space-y-2 text-sm text-muted-foreground">
          <li>Webhook processing is idempotent by event id when Redis is available.</li>
          <li>Usage metering sends ASAHIO token counts into Stripe meter events without blocking request traffic.</li>
          <li>Mock checkout and portal URLs are returned automatically when Stripe credentials are not configured.</li>
        </ul>
      </div>
    </div>
  );
}

function InfoTile({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-border bg-background px-4 py-3">
      <p className="text-xs uppercase tracking-wide text-muted-foreground">{label}</p>
      <p className="mt-1 text-sm font-medium text-foreground">{value}</p>
    </div>
  );
}

function UsageBar({ label, used, limit, pct }: { label: string; used: number; limit: number; pct: number }) {
  const unlimited = limit < 0;
  const width = unlimited ? 100 : Math.min(pct, 100);
  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between text-sm">
        <span className="font-medium text-foreground">{label}</span>
        <span className={cn("text-muted-foreground", pct >= 95 && "text-red-400", pct >= 80 && pct < 95 && "text-amber-300")}>
          {formatNumber(used)} / {unlimited ? "Unlimited" : formatNumber(limit)}
        </span>
      </div>
      <div className="h-2 rounded-full bg-muted">
        <div className={cn("h-2 rounded-full transition-all", usageColor(pct))} style={{ width: `${width}%` }} />
      </div>
      <p className="text-xs text-muted-foreground">{unlimited ? "No cap configured" : `${pct.toFixed(1)}% used`}</p>
    </div>
  );
}


