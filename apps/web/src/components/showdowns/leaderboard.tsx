"use client";

import { Trophy } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import type { VariantScore } from "@prompt-showdown/shared";

function fmt(n: number | null): string {
  return n !== null ? n.toFixed(1) : "—";
}

export function Leaderboard({
  leaderboard,
  judgeEnabled,
}: {
  leaderboard: VariantScore[];
  judgeEnabled: boolean;
}) {
  return (
    <div className="space-y-3">
      <h2 className="card-title flex items-center gap-2">
        <Trophy className="h-4 w-4 text-[var(--primary)]" />
        Leaderboard
      </h2>
      <Table>
        <TableHeader>
          <TableRow className="bg-muted/40 hover:bg-muted/40">
            <TableHead className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              Variant
            </TableHead>
            {judgeEnabled && (
              <TableHead className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                Avg Judge
              </TableHead>
            )}
            <TableHead className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              Avg Human
            </TableHead>
            <TableHead className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              Wins
            </TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {leaderboard.map((v, i) => (
            <TableRow key={v.variant} className="table-row-hover">
              <TableCell className="font-medium">
                <span className="inline-flex items-center gap-2">
                  {i === 0 && <Trophy className="h-3.5 w-3.5 text-[var(--primary)]" />}
                  {v.variant}
                  {i === 0 && <Badge variant="secondary">leader</Badge>}
                </span>
              </TableCell>
              {judgeEnabled && (
                <TableCell className="tabular-nums">{fmt(v.avg_judge_score)}</TableCell>
              )}
              <TableCell className="tabular-nums">{fmt(v.avg_human_score)}</TableCell>
              <TableCell className="tabular-nums">{v.wins}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
