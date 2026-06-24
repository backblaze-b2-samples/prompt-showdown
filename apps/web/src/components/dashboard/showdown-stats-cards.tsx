"use client";

import { Layers, Trophy, Gauge, Swords } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { ErrorState } from "@/components/ui/error-state";
import { useShowdownStats } from "@/lib/queries";

export function ShowdownStatsCards() {
  const { data: stats, isLoading, error, refetch } = useShowdownStats();

  if (error) {
    return (
      <Card>
        <CardContent className="p-0">
          <ErrorState error={error} onRetry={() => refetch()} />
        </CardContent>
      </Card>
    );
  }

  const cards = [
    { title: "Total Runs", value: stats?.total_runs ?? 0, icon: Swords },
    { title: "Variants Compared", value: stats?.total_variants_compared ?? 0, icon: Layers },
    {
      title: "Avg Judge Score",
      value:
        typeof stats?.avg_judge_score === "number"
          ? stats.avg_judge_score.toFixed(1)
          : "—",
      icon: Gauge,
    },
    { title: "Best Variant", value: stats?.best_variant ?? "—", icon: Trophy },
  ];

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {cards.map((card, i) => (
        <Card
          key={card.title}
          className={`card-hover animate-fade-in-up stagger-${i + 1}`}
        >
          <CardHeader className="flex flex-row items-center justify-between pt-4 pb-2 px-4 space-y-0">
            <CardTitle className="text-xs font-semibold text-muted-foreground">
              {card.title}
            </CardTitle>
            <div className="stat-icon-wrap">
              <card.icon className="h-4 w-4" />
            </div>
          </CardHeader>
          <CardContent className="pb-5 px-4">
            {isLoading ? (
              <Skeleton className="h-8 w-24" />
            ) : (
              <div className="stat-value truncate" title={String(card.value)}>
                {card.value}
              </div>
            )}
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
