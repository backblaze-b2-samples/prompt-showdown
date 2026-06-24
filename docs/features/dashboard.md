<!-- last_verified: 2026-06-24 -->
# Feature: Dashboard

## Purpose
Provide an at-a-glance overview of showdown activity: how many runs, how many
variants compared, the average judge score, the best variant, the wins-per-variant
chart, and the most recent runs.

## Used By
- UI: `/` page (dashboard home)
- API: `GET /runs/stats`, `GET /runs/stats/wins`, `GET /runs`

## Core Functions
- `apps/web/src/components/dashboard/showdown-stats-cards.tsx` — 4 stat cards
- `apps/web/src/components/dashboard/wins-chart.tsx` — wins-per-variant bar chart
- `apps/web/src/components/dashboard/recent-runs-table.tsx` — most recent runs
- `apps/web/src/lib/api-client.ts` — `getShowdownStats()`, `getVariantWins()`, `getRuns()`
- `services/api/app/runtime/showdown.py` — `GET /runs/stats`, `GET /runs/stats/wins` handlers
- `services/api/app/service/showdown.py` — `get_stats()`, `get_variant_wins()`
- `services/api/app/service/scoring.py` — `aggregate_stats()`, `variant_wins()`

## Canonical Files
- Stat cards: `apps/web/src/components/dashboard/showdown-stats-cards.tsx`
- Aggregation logic: `services/api/app/service/scoring.py`

## Inputs
- None (dashboard loads data automatically)

## Outputs
- `GET /runs/stats` → `ShowdownStats` (total_runs, total_variants_compared, avg_judge_score, best_variant)
- `GET /runs/stats/wins` → `VariantWins[]` for the chart (wins aggregated across runs)
- `GET /runs` → `RunSummary[]` for the recent-runs table (newest-first)

## Flow
- Page loads → three parallel API calls (stats, wins, recent runs)
- Stat cards show total runs, variants compared, average judge score, best variant
- Wins chart shows how often each variant scored highest on an input, across all runs
- Recent runs table links each row to its run-detail grid

## Edge Cases
- API unavailable → inline `ErrorState` with retry
- No runs yet → empty states on cards (`—`), chart, and table
- Many runs → `list_runs` paginates the `showdowns/` prefix

## UX States
- Loading: skeleton placeholders
- Empty: "No runs yet" messaging
- Loaded: populated cards, chart, table

## Verification
- Test files: `services/api/tests/test_genblaze_signatures.py`, `services/api/tests/test_structure.py`
- Quick verify command: `pnpm test:api`
- Full verify command: `pnpm lint && pnpm lint:api && pnpm test:api && pnpm check:structure && pnpm build`
- Pass criteria: all pytest tests green, no ruff/eslint violations, build succeeds

## Related Docs
- [Run History](run-history.md)
- [ARCHITECTURE.md](../../ARCHITECTURE.md)
- [App Workflows](../app-workflows.md)
