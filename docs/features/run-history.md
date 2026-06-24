<!-- last_verified: 2026-06-24 -->
# Feature: Run History

## Purpose
Browse every preserved showdown run from the sample's own B2 prefix
(`showdowns/`), open a run-detail grid (variants × inputs) with the leaderboard,
and rate any cell by hand. This is the "Library" of the sample — distinct from
the full-bucket `/files` explorer, which is kept and coexists by design.

## Used By
- UI: `/showdowns` (history list), `/showdowns/[id]` (grid + leaderboard + human scoring)
- API: `GET /runs`, `GET /runs/{id}`, `POST /runs/{id}/scores`

## Core Functions
- `apps/web/src/components/showdowns/run-history.tsx` — scoped run list
- `apps/web/src/components/showdowns/run-detail.tsx` — page shell + export
- `apps/web/src/components/showdowns/showdown-grid.tsx` — N×M grid + human rating control
- `apps/web/src/components/showdowns/leaderboard.tsx` — per-variant summary
- `services/api/app/repo/showdown_store.py` — `list_runs()` (scoped `Prefix="showdowns/"`), `get_run()`, `put_run()`
- `services/api/app/service/showdown.py` — `list_run_summaries()`, `get_run_detail()`, `record_human_score()`

## Canonical Files
- Scoped explorer data access: `services/api/app/repo/showdown_store.py`
- Grid: `apps/web/src/components/showdowns/showdown-grid.tsx`

## Inputs
- `GET /runs` — none
- `GET /runs/{id}` — `run_id` path param (validated)
- `POST /runs/{id}/scores` — `ScoreRequest` (variant, input_label, human_score 1..10)

## Outputs
- `RunSummary[]` for the history list (best_variant, avg_judge_score, counts)
- `ShowdownRun` for the detail grid + leaderboard
- Human score side effect: the matching cell is updated, the leaderboard is
  recomputed, and `run.json` is rewritten to B2 (so human scores are themselves
  durable B2 run data)

## Flow
- `/showdowns` lists runs newest-first, each linking to its detail page
- `/showdowns/[id]` renders the grid: variants as columns, inputs as rows; each
  cell shows the output, the judge score + rationale, and a 1–10 human rating
- Selecting a human rating posts to `POST /runs/{id}/scores`; the cache
  invalidates and the leaderboard refreshes

## Edge Cases
- Invalid run id → `400`; unknown run id → `404`
- Human score for a non-existent cell → `400`
- No runs → empty state with a link to create one
- The bucket explorer (`/files`) and this scoped explorer (`/showdowns`) coexist

## UX States
- Loading: skeleton rows / cards
- Empty: "No showdowns yet"
- Error: inline `ErrorState` with retry
- Loaded: grid + leaderboard; toast on a saved human score

## Verification
- Test files: `services/api/tests/test_structure.py`, `services/api/tests/test_genblaze_signatures.py`
- Quick verify command: `pnpm test:api`
- Full verify command: `pnpm lint && pnpm lint:api && pnpm test:api && pnpm check:structure && pnpm build`
- Pass criteria: tests green, build green, routes reachable (`/showdowns`, `/showdowns/[id]`)

## Related Docs
- [Showdown Runs](showdown-runs.md)
- [LLM Judge](llm-judge.md)
- [File Browser](file-browser.md)
- [ARCHITECTURE.md](../../ARCHITECTURE.md)
