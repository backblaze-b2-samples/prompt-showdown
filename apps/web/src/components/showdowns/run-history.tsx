"use client";

import Link from "next/link";
import { Plus, Swords } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Skeleton } from "@/components/ui/skeleton";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { useRuns } from "@/lib/queries";
import { formatDate } from "@/lib/utils";

export function RunHistory() {
  const { data: runs = [], isLoading, error, refetch } = useRuns();

  return (
    <div className="space-y-8">
      <div className="animate-fade-in border-b border-border pb-5 flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="page-title">Run History</h1>
          <p className="text-sm text-muted-foreground mt-1.5">
            Every showdown is preserved under the{" "}
            <code className="font-mono text-xs">showdowns/</code> prefix on
            Backblaze B2 — the durable system of record for your prompt runs.
          </p>
        </div>
        <Button asChild size="sm" className="h-8">
          <Link href="/showdowns/new">
            <Plus className="h-3.5 w-3.5" />
            New showdown
          </Link>
        </Button>
      </div>

      <Card>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="p-4 space-y-3">
              {Array.from({ length: 6 }).map((_, i) => (
                <Skeleton key={i} className="h-10 w-full" />
              ))}
            </div>
          ) : error ? (
            <ErrorState error={error} onRetry={() => refetch()} />
          ) : runs.length === 0 ? (
            <EmptyState
              icon={Swords}
              title="No showdowns yet"
              description="Create your first showdown to compare prompt variants side-by-side."
            />
          ) : (
            <Table>
              <TableHeader>
                <TableRow className="bg-muted/40 hover:bg-muted/40">
                  <TableHead className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                    Title
                  </TableHead>
                  <TableHead className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                    Variants
                  </TableHead>
                  <TableHead className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                    Inputs
                  </TableHead>
                  <TableHead className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                    Best
                  </TableHead>
                  <TableHead className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                    Avg Judge
                  </TableHead>
                  <TableHead className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                    Created
                  </TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {runs.map((run) => (
                  <TableRow key={run.run_id} className="table-row-hover">
                    <TableCell className="font-medium">
                      <Link
                        href={`/showdowns/${run.run_id}`}
                        className="hover:underline"
                      >
                        {run.title}
                      </Link>
                    </TableCell>
                    <TableCell className="tabular-nums text-muted-foreground">
                      {run.variant_count}
                    </TableCell>
                    <TableCell className="tabular-nums text-muted-foreground">
                      {run.input_count}
                    </TableCell>
                    <TableCell>
                      {run.best_variant ? (
                        <Badge variant="secondary">{run.best_variant}</Badge>
                      ) : (
                        <span className="text-muted-foreground">—</span>
                      )}
                    </TableCell>
                    <TableCell className="tabular-nums text-muted-foreground">
                      {run.avg_judge_score !== null
                        ? run.avg_judge_score.toFixed(1)
                        : "—"}
                    </TableCell>
                    <TableCell className="text-muted-foreground whitespace-nowrap">
                      {formatDate(run.created_at)}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
