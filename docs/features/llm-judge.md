<!-- last_verified: 2026-06-24 -->
# Feature: LLM Judge

## Purpose
Score each generated output automatically with a structured-output LLM call,
producing `{score, rationale}` per cell so variants can be compared objectively.

## Used By
- UI: scores + rationale shown per cell in `/showdowns/[id]`; leaderboard averages
- API: invoked inside `POST /runs` when `judge_enabled` is true

## Core Functions
- `services/api/app/repo/genblaze_repo.py` — `judge_cell()`, `JudgeVerdict`
- `services/api/app/service/showdown.py` — calls `judge_cell` per non-empty cell
- `services/api/app/service/scoring.py` — averages judge scores into the leaderboard

## Canonical Files
- Judge call: `services/api/app/repo/genblaze_repo.py`

## Inputs
- `output_text: str` — the candidate output to score
- `criteria: str` — run-level judging criteria
- `model: str` — judge model (default `meta/llama-3.3-70b-instruct`)

## Outputs
- `JudgeVerdict(score: int 1..10, rationale: str)` per cell, stored on the run record

## Flow
- For each generated, non-empty cell, `judge_cell` calls Genblaze's `chat()` with
  `response_format=JudgeVerdict` and `temperature=0`
- The structured JSON response is parsed into `JudgeVerdict`
- Scores feed the leaderboard (averages + per-input wins)

## Edge Cases
- Judge call fails for a cell → logged as a warning; that cell keeps a null score
  and the run completes (judging is best-effort per cell)
- `judge_enabled=false` → generation only; the human-rating control still applies
- Malformed structured output → JSON parse / Pydantic validation error, caught
  per cell

## UX States
- Loaded: `Judge: N/10` badge + rationale text per cell
- Empty: no badge when the cell has no judge score

## Verification
- Test files: `services/api/tests/test_genblaze_signatures.py::test_judge_cell_signature`
- Quick verify command: `pnpm test:api`
- Full verify command: `pnpm lint && pnpm lint:api && pnpm test:api && pnpm check:structure && pnpm build`
- Pass criteria: the guard asserts `response_format` is the `JudgeVerdict` model and `temperature=0`

## Related Docs
- [Showdown Runs](showdown-runs.md)
- [Run History](run-history.md)
- [ARCHITECTURE.md](../../ARCHITECTURE.md)
