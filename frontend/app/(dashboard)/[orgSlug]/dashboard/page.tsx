"use client";

import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import {
  getAnalyticsOverview,
  getModelBreakdown,
  getRequestLogs,
  getSavingsTimeSeries,
} from "@/lib/api";
import { KpiCard } from "@/components/charts/kpi-card";
import { ModelDistributionChart } from "@/components/charts/model-distribution-chart";
import { RecentRequestsTable } from "@/components/charts/recent-requests-table";
import { SavingsChart } from "@/components/charts/savings-chart";
import { OnboardingWizard } from "@/components/onboarding-wizard";
import { Activity, Database, DollarSign, TrendingUp } from "lucide-react";

export default function DashboardPage() {
  const params = useParams();
  const orgSlug = typeof params?.orgSlug === "string" ? params.orgSlug : "";
  const [showOnboarding, setShowOnboarding] = useState(false);

  // Check if user has completed onboarding
  useEffect(() => {
    const key = `asahio_onboarding_${orgSlug}`;
    const completed = localStorage.getItem(key);
    if (!completed && orgSlug) {
      setShowOnboarding(true);
    }
  }, [orgSlug]);

  const handleOnboardingComplete = () => {
    localStorage.setItem(`asahio_onboarding_${orgSlug}`, "true");
    setShowOnboarding(false);
  };

  const handleOnboardingDismiss = () => {
    localStorage.setItem(`asahio_onboarding_${orgSlug}`, "true");
    setShowOnboarding(false);
  };

  const { data: overview, isLoading: overviewLoading } = useQuery({
    queryKey: ["overview", orgSlug],
    queryFn: () => getAnalyticsOverview("30d", undefined, orgSlug),
  });

  const { data: savings } = useQuery({
    queryKey: ["savings", orgSlug],
    queryFn: () => getSavingsTimeSeries("30d", "day", undefined, orgSlug),
  });

  const { data: models } = useQuery({
    queryKey: ["models", orgSlug],
    queryFn: () => getModelBreakdown("30d", undefined, orgSlug),
  });

  const { data: requests } = useQuery({
    queryKey: ["recent-requests", orgSlug],
    queryFn: () => getRequestLogs({ limit: 10 }, undefined, orgSlug),
  });

  return (
    <>
      {showOnboarding && (
        <OnboardingWizard
          onComplete={handleOnboardingComplete}
          onDismiss={handleOnboardingDismiss}
        />
      )}

      <div className="space-y-6 animate-fade-in">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-foreground">Dashboard</h1>
            <p className="text-sm text-muted-foreground">
              Monitor request volume, savings, cache performance, and routing health for your ASAHIO deployment.
            </p>
          </div>
          {!showOnboarding && (
            <button
              onClick={() => setShowOnboarding(true)}
              className="text-sm text-asahio hover:underline"
            >
              Restart Tutorial
            </button>
          )}
        </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <KpiCard title="Total Savings" value={overview?.total_savings_usd ?? 0} format="currency" delta={overview?.savings_delta_pct} deltaLabel="vs last period" icon={DollarSign} loading={overviewLoading} highlight />
        <KpiCard title="Total Requests" value={overview?.total_requests ?? 0} format="number" delta={overview?.requests_delta_pct} deltaLabel="vs last period" icon={Activity} loading={overviewLoading} />
        <KpiCard title="Cache Hit Rate" value={(overview?.cache_hit_rate ?? 0) * 100} format="percentage" icon={Database} loading={overviewLoading} />
        <KpiCard title="Avg Latency" value={overview?.avg_latency_ms ?? 0} format="number" suffix="ms" icon={TrendingUp} loading={overviewLoading} />
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <SavingsChart data={savings?.data ?? []} />
        <ModelDistributionChart data={models?.data ?? []} />
      </div>

      <RecentRequestsTable data={requests?.data ?? []} orgSlug={orgSlug} />
      </div>
    </>
  );
}
