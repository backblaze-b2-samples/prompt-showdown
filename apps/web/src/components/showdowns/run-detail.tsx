"use client";

import Link from "next/link";
import { ArrowLeft, Download } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { ErrorState } from "@/components/ui/error-state";
import { useRun } from "@/lib/queries";
import { exportRunUrl } from "@/lib/api-client";
import { formatDate } from "@/lib/utils";
import { Leaderboard } from "@/components/showdowns/leaderboard";
import { ShowdownGrid } from "@/components/showdowns/showdown-grid";

export function RunDetail({ runId }: { runId: string }) {
  const { data: run, isLoading, error, refetch } = useRun(runId);

  if (isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-10 w-64" />
        <Skeleton className="h-48 w-full" />
      </div>
    );
  }

  if (error) {
    return <ErrorState error={error} onRetry={() => refetch()} />;
  }

  if (!run) return null;

  return (
    <div className="space-y-8">
      <div className="animate-fade-in border-b border-border pb-5 space-y-3">
        <Link
          href="/showdowns"
          className="inline-flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground"
        >
          <ArrowLeft className="h-3 w-3" /> Run History
        </Link>
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <h1 className="page-title">{run.title}</h1>
            <p className="text-sm text-muted-foreground mt-1.5 flex flex-wrap items-center gap-2">
              <Badge variant="outline" className="font-mono">{run.gen_model}</Badge>
              {run.judge_enabled && <Badge variant="secondary">LLM judge on</Badge>}
              <span>{formatDate(run.created_at)}</span>
              <code className="font-mono text-xs">showdowns/{run.run_id}/</code>
            </p>
          </div>
          <Button asChild variant="outline" size="sm" className="h-8">
            <a href={exportRunUrl(run.run_id)} target="_blank" rel="noopener noreferrer">
              <Download className="h-3.5 w-3.5" />
              Export JSON
            </a>
          </Button>
        </div>
      </div>

      <Card>
        <CardContent className="p-5">
          <Leaderboard leaderboard={run.leaderboard} judgeEnabled={run.judge_enabled} />
        </CardContent>
      </Card>

      <ShowdownGrid run={run} />
    </div>
  );
}
