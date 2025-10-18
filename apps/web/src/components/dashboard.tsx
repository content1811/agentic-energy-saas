
"use client";

import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import { StatsCard } from "@/components/stats-card";
import { UsageChart } from "@/components/usage-chart";
import { AdviceCards } from "@/components/advice-cards";
import { Battery, Zap, TrendingDown, Leaf } from "lucide-react";

const TENANT_ID = "123e4567-e89b-12d3-a456-426614174000";
const SITE_ID = "site-01";

interface Reading {
  ts: string;
  kw: number;
  site_id: string;
}

interface Advice {
  id: string;
  title: string;
  text: string;
  savings_est_usd: number;
  co2_saved_kg: number;
  type: string;
}

export function Dashboard() {
  const { data: latestReading } = useQuery({
    queryKey: ["latest-reading", SITE_ID],
    queryFn: () => apiClient.get<Reading>(
      `/api/v1/readings/latest?tenant_id=${TENANT_ID}&site_id=${SITE_ID}`
    ),
    refetchInterval: 15000,
  });

  const { data: readings } = useQuery({
    queryKey: ["readings", SITE_ID],
    queryFn: () => apiClient.get<Reading[]>(
      `/api/v1/readings/?tenant_id=${TENANT_ID}&site_id=${SITE_ID}&limit=100`
    ),
    refetchInterval: 15000,
  });

  const { data: advice } = useQuery({
    queryKey: ["advice", SITE_ID],
    queryFn: () => apiClient.get<Advice[]>(
      `/api/v1/advice/?tenant_id=${TENANT_ID}&site_id=${SITE_ID}&limit=3`
    ),
    refetchInterval: 60000,
  });

  const currentKw = latestReading?.kw || 0;
  const avgKw = readings && readings.length > 0
    ? readings.reduce((sum, r) => sum + r.kw, 0) / readings.length
    : 0;
  const dailyCost = currentKw * 24 * 0.12;
  const totalSavings = advice?.reduce((sum, a) => sum + a.savings_est_usd, 0) || 0;
  const totalCO2 = advice?.reduce((sum, a) => sum + a.co2_saved_kg, 0) || 0;

  return (
    <div className="space-y-6">
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        <StatsCard
          title="Current Usage"
          value={`${currentKw.toFixed(1)} kW`}
          icon={<Zap className="h-5 w-5" />}
          trend={currentKw > avgKw ? `+${((currentKw/avgKw - 1) * 100).toFixed(1)}%` : "Normal"}
        />
        <StatsCard
          title="Today's Cost"
          value={`$${dailyCost.toFixed(2)}`}
          icon={<Battery className="h-5 w-5" />}
          trend="Est. 24hr"
        />
        <StatsCard
          title="Savings Potential"
          value={`$${totalSavings.toFixed(2)}`}
          icon={<TrendingDown className="h-5 w-5" />}
          trend="Per day"
          trendPositive={true}
        />
        <StatsCard
          title="CO₂ Impact"
          value={`${totalCO2.toFixed(1)} kg`}
          icon={<Leaf className="h-5 w-5" />}
          trend="Potential savings"
        />
      </div>

      <UsageChart readings={readings || []} />

      <AdviceCards advice={advice || []} />
    </div>
  );
}