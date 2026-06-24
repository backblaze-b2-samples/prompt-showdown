<!-- last_verified: 2026-06-24 -->
# Feature: Prompt Variants

## Purpose
Version prompts like code: a named prompt template with `{variable}` placeholders
is one *variant* under comparison. Variants are defined per run and stored with
the run record on B2.

## Used By
- UI: `/showdowns/new` (New Showdown form)
- API: variants are part of the `POST /runs` payload and the persisted record

## Core Functions
- `apps/web/src/components/showdowns/new-showdown-form.tsx` — add/remove variants, template editor
- `apps/web/src/lib/showdown.ts` — `extractVars()` surfaces template variables
- `services/api/app/types/showdown.py` — `PromptVariant` model
- `services/api/app/repo/genblaze_repo.py` — wraps each template in `PromptTemplate`

## Canonical Files
- Model: `services/api/app/types/showdown.py`
- Template-to-pipeline glue: `services/api/app/repo/genblaze_repo.py`

## Inputs
- `name: str` — variant name (column header in the grid)
- `template: str` — prompt text with `{variable}` placeholders

## Outputs
- Stored verbatim in `showdowns/<run_id>/run.json` under `variants[]`
- Drives one Genblaze `Pipeline` per variant

## Flow
- User adds named variants in the form; detected `{variables}` are surfaced
- On run, each variant's template becomes a `PromptTemplate`
- `batch_run` renders the template against each input row's variable dict

## Edge Cases
- Missing variable in an input row → `PromptTemplate.render` raises; the cell
  output is empty and the run still completes for other cells
- Empty name/template → blocked client-side before submit

## UX States
- Empty: at least one variant row always present
- Loaded: variant cards with live variable detection

## Verification
- Test files: `services/api/tests/test_genblaze_signatures.py`
- Quick verify command: `pnpm test:api`
- Full verify command: `pnpm lint && pnpm lint:api && pnpm test:api && pnpm check:structure && pnpm build`
- Pass criteria: signature guard asserts the template is wrapped in a `PromptTemplate`

## Related Docs
- [Showdown Runs](showdown-runs.md)
- [ARCHITECTURE.md](../../ARCHITECTURE.md)
