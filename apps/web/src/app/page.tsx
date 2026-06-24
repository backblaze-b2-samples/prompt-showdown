import Link from "next/link";
import { Plus } from "lucide-react";

import { Button } from "@/components/ui/button";
import { ShowdownStatsCards } from "@/components/dashboard/showdown-stats-cards";
import { RecentRunsTable } from "@/components/dashboard/recent-runs-table";
import { WinsChart } from "@/components/dashboard/wins-chart";

export default function DashboardPage() {
  return (
    <div className="space-y-8">
      <div className="animate-fade-in border-b border-border pb-5 flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="page-title">Dashboard</h1>
          <p className="text-sm text-muted-foreground mt-1.5">
            Prompt-variant showdowns scored by an LLM judge and preserved on Backblaze B2.
          </p>
        </div>
        <Button asChild size="sm" className="h-8">
          <Link href="/showdowns/new">
            <Plus className="h-3.5 w-3.5" />
            New showdown
          </Link>
        </Button>
      </div>
      <ShowdownStatsCards />
      <div className="grid gap-6 lg:grid-cols-2">
        <div className="animate-fade-in-up stagger-3">
          <WinsChart />
        </div>
        <div className="animate-fade-in-up stagger-4">
          <RecentRunsTable />
        </div>
      </div>
    </div>
  );
}
