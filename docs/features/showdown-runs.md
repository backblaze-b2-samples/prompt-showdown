<!-- last_verified: 2026-06-25 -->
# Feature: Showdown Runs

## Purpose
Execute the variant × input grid through a Genblaze Pipeline, persist every
cell's output (plus a SHA-256 provenance manifest) and the canonical run record
to Backblaze B2, and expose the run for browsing and export.

## Used By
- UI: `/showdowns/new` (launch), `/showdowns/[id]` (view), Export button
- API: `POST /runs`, `GET /runs/{id}`, `GET /runs/{id}/export`

## Core Functions
- `services/api/app/service/showdown.py` — `create_run()`, `export_run()`
- `services/api/app/repo/genblaze_repo.py` — `run_variant()` (Pipeline `batch_run`), `_sink()`
- `services/api/app/repo/showdown_store.py` — `put_run()`, `get_run()`
- `apps/web/src/components/showdowns/run-detail.tsx` + `showdown-grid.tsx`

## Canonical Files
- Orchestration: `services/api/app/service/showdown.py`
- Genblaze pipeline: `services/api/app/repo/genblaze_repo.py`

## Inputs
- `POST /runs` body → `CreateRunRequest` (title, variants[], inputs[], gen_model?, judge_model?, judge_enabled, criteria)

## Outputs
- `ShowdownRun` (cells filled with outputs + scores, leaderboard computed)
- Side effects on B2:
  - `showdowns/<run_id>/run.json` — canonical record (boto3)
  - `showdowns/<run_id>/cells/...` — outputs + manifests (genblaze-s3 sink)
- Export: `GET /runs/{id}/export` streams the run record as JSON for download

## Flow
- `create_run` builds the grid → for each variant `run_variant` fans the shared
  input set via a `Pipeline(...).step(NvidiaChatProvider(), ...).batch_run(...)`
- If judging is on, each non-empty output is scored (see [LLM Judge](llm-judge.md))
- `service/scoring.build_leaderboard` computes per-variant averages + wins
- `put_run` writes the canonical JSON record to B2

## Edge Cases
- A provider failure for a cell → that cell's output is empty; the run still
  completes and persists (`raise_on_failure=False`)
- Slow generation → each call uses `SHOWDOWN_REQUEST_TIMEOUT` (default 300s) as
  its HTTP timeout. The genblaze default is 60s, which is too short for the 70B
  default model on NIM's free tier and drops cells; the larger timeout prevents
  this.
- Missing `NVIDIA_API_KEY` → the provider raises; surfaced as `502` from `POST /runs`
- Generation default is small (3×3) to stay under the NIM free-tier rate limit

## UX States
- Loading: "Running…" button state during `POST /runs`
- Error: toast with the API error detail
- Loaded: redirect to the run-detail grid

## Verification
- Test files: `services/api/tests/test_genblaze_signatures.py`
- Quick verify command: `pnpm test:api`
- Full verify command: `pnpm lint && pnpm lint:api && pnpm test:api && pnpm check:structure && pnpm build`
- Pass criteria: signature guard asserts the Pipeline/batch_run/sink call shape

## Related Docs
- [LLM Judge](llm-judge.md)
- [Run History](run-history.md)
- [ARCHITECTURE.md](../../ARCHITECTURE.md)
