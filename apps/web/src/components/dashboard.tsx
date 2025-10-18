"use client";

import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import { StatsCard } from "./stats-card";
import { Battery, Zap, TrendingDown, Leaf } from "lucide-react";

export function Dashboard() {
  const { data: health } = useQuery({
    queryKey: ["health"],
    queryFn: () => apiClient.get("/health"),
  });

  return (
    <div className="space-y-6">
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        <StatsCard
          title="Current Usage"
          value="42.5 kW"
          icon={<Zap className="h-5 w-5" />}
          trend="+5.2%"
        />
        <StatsCard
          title="Today's Cost"
          value="$187.40"
          icon={<Battery className="h-5 w-5" />}
          trend="-2.1%"
          trendPositive={true}
        />
        <StatsCard
          title="Savings Potential"
          value="$45.30"
          icon={<TrendingDown className="h-5 w-5" />}
          trend="Based on AI analysis"
        />
        <StatsCard
          title="CO₂ Saved"
          value="23.4 kg"
          icon={<Leaf className="h-5 w-5" />}
          trend="This month"
        />
      </div>

      <div className="rounded-lg border bg-white p-6 shadow-sm">
        <h2 className="mb-4 text-lg font-semibold">System Status</h2>
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-600">API Status</span>
            <span className="text-sm font-medium text-green-600">
              {health?.status || "Connecting..."}
            </span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-600">Version</span>
            <span className="text-sm font-medium">
              {health?.version || "v0.1.0"}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}