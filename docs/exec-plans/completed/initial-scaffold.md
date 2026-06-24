# Build plan — `prompt-showdown`

Source of truth for the starter tree (cloned fresh in Phase 0):
`.claude/scratch/vcsk-3fda7d6f-fa55-4865-bfd0-3f85393a918f/`. Compute every
keep/trim/add against THAT tree only. Parent standards: `../CLAUDE.md`.

---

## 1. Purpose

`prompt-showdown` versions prompts like code: a prompt engineer defines **N
prompt variants** and a **shared input set**, runs them side-by-side through an
LLM, and every output is **scored by an LLM judge (and optionally by a human)**.
Every run is preserved on Backblaze B2 — full inputs, outputs, and scores —
append-only, frequently queried (leaderboard, run diff), occasionally exported
(download a run as JSON). It is for prompt engineers comparing prompt versions,
and it shows off B2 as the durable, query-friendly system of record for AI run
history. It complements (does not duplicate) the eval-runner sample: the focus
here is *side-by-side variant comparison with scoring and preserved run history*,
not a generic batch eval harness.

**Resolved open questions (deterministic defaults — no human gate):**
- *Overlap with eval-runner:* keep separate. Distinct angle = variant-vs-variant
  comparison + per-run history browser, not a generic eval runner.
- *Human judging UI:* **v1, lightweight.** The LLM judge is the automatic default;
  the run-detail grid also exposes a per-cell human rating control that writes the
  score back into the run record on B2 (so "scored by humans or LLM judges" is
  literally true, and human scores are themselves B2 run data).

---

## 2. Architecture delta from vibe-coding-starter-kit

The starter kit is the ceiling — strip what this app doesn't need, keep the
reusable B2 scaffolding, add the showdown surface.

### KEEP (as-is — starter contract, do NOT strip/rename/replace)
- **UI kit / design system:** `apps/web/src/components/ui/**`, design tokens in
  `apps/web/src/app/globals.css`, the `/design` page. Build new screens from
  these primitives; never edit generated `components/ui/` files.
- **Bucket explorer (NON-NEGOTIABLE keep):** `/files` route + `apps/web/src/app/files/`
  + `apps/web/src/components/files/**` + `lib/file-tree.ts` — full-bucket browse stays.
- **Upload:** `/upload` route + `apps/web/src/components/upload/**` + the upload/
  metadata-extraction backend (`service/upload.py`, `service/metadata.py`,
  `runtime/upload.py`). Part of the kept contract.
- **Sidebar nav** (Dashboard, Upload, Files, Settings + Design System link),
  health banner, command palette, TanStack Query data layer, layered FastAPI
  backend, structural tests, JSON logging, `/health`, `/metrics`.

### TRIM (minimal — lower build risk)
- **Dashboard default content** is *adapted*, not deleted (see ADD). The
  upload-centric dashboard components (`components/dashboard/upload-chart.tsx`,
  `recent-uploads-table.tsx`, `stats-cards.tsx`) are repurposed into showdown
  metrics; remove any that no longer have a consumer after the rewrite (don't
  leave unused imports — they break `pnpm build`/lint; see §Known pitfalls).
- **Starter-kit marketing framing** in `README.md` (the "Vibe Coding Starter
  Kit / Stop wiring boilerplate" copy) — rewritten, not kept.
- Nothing else structural is removed.

### ADD (new for prompt-showdown)
- **Sample-specific scoped explorer (NON-NEGOTIABLE add):** a **Run History**
  view at `/showdowns` scoped to the sample's own B2 prefix `showdowns/` — lists
  past runs (the "Library" of this sample), distinct from the full-bucket `/files`
  explorer which stays. Note: the bucket explorer and this scoped explorer
  coexist by design.
- **New Showdown form** (`/showdowns/new`): define N prompt variants (name +
  template text) + the shared input set (list of input rows / template-variable
  fills) + pick the generation model + judge on/off → launch a run.
- **Run detail** (`/showdowns/[id]`): the N×M grid — variants as columns, inputs
  as rows; each cell shows the generated output, the LLM judge score+rationale,
  and a human rating control. Plus a per-variant leaderboard summary.
- **Adapted Dashboard** (`/`): showdown metrics — total runs, variants compared,
  best-performing variant, avg judge score, recent runs table, wins-per-variant
  chart. Flows through `runtime -> service -> repo` + TanStack Query hooks.
- **Backend showdown stack** (layered): see §B2 surface + §Genblaze.

---

## 3. B2 surface (S3-compatible only — no b2-native)

All B2 access is S3 API. Two cooperating S3 paths, both under the sample's
`showdowns/<run_id>/` prefix:

1. **App run-record store (boto3, `repo/b2_client.py`)** — the canonical run
   record. One JSON per run at `showdowns/<run_id>/run.json` holding variants,
   inputs, per-cell outputs, judge scores, human scores, model+params, timestamps.
   Ops: `put_object` (write run), `get_object` (detail/export), `list_objects_v2`
   (scoped `Prefix="showdowns/"` for the Run History explorer). Reuses the
   existing presigned-URL/list/delete helpers.
2. **Genblaze provenance sink (genblaze-s3, `repo/genblaze_repo.py`)** — the
   generation Pipeline persists each cell's output + a SHA-256 provenance manifest
   to B2 via `ObjectStorageSink(S3StorageBackend.for_backblaze(...))` under the
   same run prefix (`showdowns/<run_id>/cells/...`). This is "every run preserved
   with full inputs/outputs" backed by tamper-evident manifests.

The existing full-bucket explorer/upload continue to exercise put/list/head/
delete/presign as before. **No b2-native API anywhere.**

**Standard #2 — custom user agent:** the boto3 client in `repo/b2_client.py`
keeps a custom `user_agent_extra` (value `b2ai-prompt-showdown`). For the
genblaze-s3 backend, set a custom UA if `S3StorageBackend.for_backblaze` exposes
the hook; if it does not, that is a **justified deviation** (third-party SDK owns
its client, same class of deviation as the PyArrow/PyIceberg case) — record it in
`docs/SECURITY.md` or the feature doc, don't fight the SDK.

---

## 4. Key features (seed README list + `docs/features/<feature>.md` stubs)

1. **Prompt variants** — version named prompt templates (`PromptTemplate` vars),
   stored per run on B2. → `docs/features/prompt-variants.md`
2. **Showdown runs** — execute the variant×input grid through a Genblaze Pipeline
   (`batch_run`), persist outputs + manifests to B2. → `docs/features/showdown-runs.md`
3. **LLM judge** — score each output with a structured-output judge call,
   producing `{score, rationale}` per cell. → `docs/features/llm-judge.md`
4. **Run history explorer** — the scoped `/showdowns` library + run detail grid +
   leaderboard. → `docs/features/run-history.md`
5. **Human scoring** — per-cell human rating written back into the run record on
   B2 (lightweight v1). → folded into `run-history.md` (or its own stub).
6. **Export** — download any run as a single JSON. → folded into `showdown-runs.md`.

### External API provider (read `api-provider-selection.md` — recorded here)
- **Provider/model:** **NVIDIA NIM via Genblaze** (`genblaze-nvidia`). This is a
  **core** API (LLM generation + judging is the thing the app shows) and it is
  wired for real.
  - Generation default model: `meta/llama-3.3-70b-instruct`.
  - Judge default model: `meta/llama-3.3-70b-instruct` (same provider → one key).
  - Both env-overridable (`SHOWDOWN_GEN_MODEL`, `SHOWDOWN_JUDGE_MODEL`).
- **Why NVIDIA:** `api-provider-selection.md` Step 2 rule 2 prefers a provider
  whose **free tier covers a full run**. NVIDIA NIM's free tier has **no
  per-token billing** (rate-limited ~40 req/min) → **effective cost ≈ $0.00 per
  full demo run**. It is also the only Genblaze provider that exposes chat as a
  first-class **Pipeline step** (`NvidiaChatProvider`), so it satisfies the
  skill's `Pipeline(...).step(Provider(), ...)` mandate for *text* natively.
- **Estimated cost for one full demo run:** **$0.00** (free tier, no per-token
  billing). Default demo size kept small (e.g. 3 variants × 3 inputs = 9
  generation calls + 9 judge calls = 18 calls, well under the rate limit).
- **Env var for the key:** `NVIDIA_API_KEY` (`nvapi-...`). Placeholder in
  `.env.example`; documented in README ("get it at build.nvidia.com"); never
  committed. Separate from all `B2_*` vars.

### Provider orchestration via Genblaze (MANDATORY — stack says Genblaze)
All AI-provider calls route through the **Genblaze SDK**, never a bare provider
SDK, and **all genblaze imports stay in `services/api/app/repo/`**.

Packages (add to `services/api/requirements.txt`):
```
genblaze-core
genblaze-s3
genblaze-nvidia[chat]      # the [chat] extra pulls the OpenAI-wire SDK for LLM calls
```

**Generation = a real Pipeline step (`NvidiaChatProvider`) over the grid:**
```python
# services/api/app/repo/genblaze_repo.py  (genblaze imports live ONLY here)
from genblaze_core import KeyStrategy, ObjectStorageSink, Pipeline, PromptTemplate
from genblaze_nvidia import NvidiaChatProvider, chat
from genblaze_s3 import S3StorageBackend

from app.config import settings

def _sink(run_id: str) -> ObjectStorageSink:
    # Explicit kwargs from our standardized B2_* settings — do NOT rely on
    # genblaze's own env auto-read (it expects B2_KEY_ID/B2_APP_KEY).
    backend = S3StorageBackend.for_backblaze(
        settings.b2_bucket_name,
        key_id=settings.b2_application_key_id,
        application_key=settings.b2_application_key,
        region=settings.b2_region,
    )
    return ObjectStorageSink(backend, key_strategy=KeyStrategy.HIERARCHICAL)

def run_grid(run_id, variants, inputs, model):
    # One Pipeline per variant; batch_run fans the shared input set across it.
    # max_concurrency is a Pipeline() CTOR kwarg, NOT a .run()/.batch_run() kwarg.
    results = []
    for v in variants:
        template = PromptTemplate(v.template)          # vars filled per input row
        out = (
            Pipeline(f"showdown-{run_id}-{v.name}", max_concurrency=4)
            .step(NvidiaChatProvider(), model=model, prompt=template)
            .batch_run([row.vars for row in inputs], sink=_sink(run_id))
        )
        results.append(out)
    return results
```

**Judge = structured-output `chat()` (uniform `ChatResponse`):**
```python
from pydantic import BaseModel
class JudgeVerdict(BaseModel):
    score: int           # 1..10
    rationale: str

def judge(output_text: str, criteria: str, model: str) -> JudgeVerdict:
    resp = chat(
        model,
        system="You are a strict evaluator. Score the candidate output.",
        prompt=f"Criteria:\n{criteria}\n\nOutput:\n{output_text}",
        response_format=JudgeVerdict,
        temperature=0,
    )
    import json
    return JudgeVerdict.model_validate(json.loads(resp.text))
```
`chat()` / `NvidiaChatProvider` / `ChatResponse` are the genblaze response
surfaces — no bare `openai`/`requests` LLM calls anywhere.

**No-network signature-guard test (REQUIRED):** add a unit test that
monkeypatches `genblaze_nvidia.chat` / `NvidiaChatProvider` (and the Pipeline) so
nothing hits the network, then asserts our repo functions call them with the
expected arguments (model, prompt template, `response_format`, sink). This
protects the sample from genblaze SDK drift. Goes in `services/api/tests/`.

---

## 5. Doc transforms

**Rewrite (re-theme to prompt-showdown):**
- `README.md` — full rewrite: purpose, screenshots placeholders, Genblaze+NVIDIA
  quickstart, B2 run-history story, standardized `B2_*` setup, `NVIDIA_API_KEY`.
- `AGENTS.md` — keep §2 "Building on This Starter Kit" contract verbatim; update
  repo identity, repo map (add showdown modules), feature list, commands.
- `ARCHITECTURE.md` — add the showdown data flow (grid → Genblaze Pipeline →
  B2 sink + run-record JSON), document the two cooperating S3 paths and the
  genblaze-in-repo/ boundary; note the genblaze-s3 UA deviation if it applies.
- `docs/features/dashboard.md` — adapt to showdown metrics.
- `docs/app-workflows.md` — add the "create variants → run showdown → judge →
  browse history → export" journey.

**Keep (still apply):** `docs/features/file-upload.md`,
`docs/features/file-browser.md`, `docs/features/metadata-extraction.md`,
`docs/design-system.md`, `docs/SECURITY.md`, `docs/RELIABILITY.md`,
`docs/dev-workflows.md`, `LICENSE`.

**New stubs:** `docs/features/prompt-variants.md`, `docs/features/showdown-runs.md`,
`docs/features/llm-judge.md`, `docs/features/run-history.md` (use
`docs/features/_template.md` as the shape).

**Delete:** none required.

---

## 6. Rename table (`vibe-coding-starter-kit` → `prompt-showdown`)

| Kind | From | To |
|---|---|---|
| kebab slug | `vibe-coding-starter-kit` | `prompt-showdown` |
| snake | `vibe_coding_starter_kit` | `prompt_showdown` |
| Title Case | `Vibe Coding Starter Kit` / `OSS Starter Kit` | `Prompt Showdown` |
| app name (`apps/web/src/lib/app-config.ts` `APP_NAME`) | `OSS Starter Kit` | `Prompt Showdown` |
| app description (`APP_DESCRIPTION`) | `File management dashboard…` | `Compare prompt variants side-by-side, scored and preserved on Backblaze B2` |
| web pkg (`apps/web/package.json`, `pnpm-workspace`, README `--filter`) | `@vibe-coding-starter-kit/web` | `@prompt-showdown/web` |
| shared pkg | `@vibe-coding-starter-kit/shared` | `@prompt-showdown/shared` |
| root pkg name (`package.json`) | `vibe-coding-starter-kit` | `prompt-showdown` |
| FastAPI title (`services/api/main.py`) | `OSS Starter Kit API` | `Prompt Showdown API` |
| image tags / workflow slugs / railway service names | `*vibe-coding-starter-kit*` | `*prompt-showdown*` |
| UTM content tag (README + sidebar B2 links) | `b2ai-oss-start` | `b2ai-prompt-showdown` |
| boto3 `user_agent_extra` | `b2ai-oss-start` | `b2ai-prompt-showdown` |

**Also fix the known branding leak:** `apps/web/src/components/layout/header.tsx`
hardcodes the app name + a "Page" fallback for unlisted routes — derive the title
from `APP_NAME` + the pathname so `/showdowns` etc. render correctly (don't leave
"oss-starter-kit"/"Page" anywhere).

---

## Known pitfalls — MUST address (from prior builds)

1. **Standardize env vars to Parent CLAUDE.md #3** (the starter kit ships the OLD
   names — this is the #1 recurring defect):
   - `B2_KEY_ID` → **`B2_APPLICATION_KEY_ID`**
   - `B2_ENDPOINT` → **`B2_REGION`** (derive endpoint
     `https://s3.{B2_REGION}.backblazeb2.com` in `settings.py`/`b2_client.py`)
   - `B2_PUBLIC_URL` → **`B2_PUBLIC_URL_BASE`**
   - keep `B2_APPLICATION_KEY`, `B2_BUCKET_NAME`
   - Update EVERY site: `.env.example`, `services/api/app/config/settings.py`,
     `services/api/app/repo/b2_client.py`, `services/api/main.py`
     (`REQUIRED_B2_SETTINGS`, `PLACEHOLDER_VALUES`), `README.md`,
     `infra/railway/**`, and `scripts/doctor.mjs` if it checks env names. Wire
     `B2_REGION` into `S3StorageBackend.for_backblaze(region=...)` too.
2. **Finish the LAST phases** (timeouts historically skip these): complete the
   **frontend wiring** (no 404 routes, `/showdowns` + nav entry present, the
   create→run→detail path reachable, NO unused imports) **and** the **doc
   re-theme**. These are first-class deliverables, not afterthoughts.
3. **Gates that must pass before "done":**
   `pnpm lint && pnpm lint:api && pnpm test:api && pnpm check:structure && pnpm build`.
4. **Layering:** genblaze + boto3 imports ONLY in `repo/`; no business logic in
   `runtime/`; Pydantic models at every boundary; each file < 300 lines; new
   endpoints touch exactly `runtime/<router>.py` + `lib/api-client.ts` +
   `lib/queries.ts` (no bare `useEffect+fetch`).
5. **Genblaze gotchas:** `max_concurrency` is a `Pipeline()` ctor kwarg (not
   `run()`/`batch_run()`); pass `S3StorageBackend.for_backblaze` creds as explicit
   kwargs from settings; install the `genblaze-nvidia[chat]` extra; add the
   no-network signature-guard test.

---

## Backend module map (target)

```
services/api/app/
  types/showdown.py     PromptVariant, ShowdownInput, RunCell, JudgeVerdict,
                        ShowdownRun, RunSummary  (Pydantic, no logic)
  config/settings.py    + b2_application_key_id, b2_region, b2_public_url_base,
                        nvidia_api_key, showdown_gen_model, showdown_judge_model
  repo/genblaze_repo.py genblaze Pipeline/NvidiaChatProvider/chat/s3 (contained here)
  repo/b2_client.py     + run-record put/get/list (scoped "showdowns/" prefix)
  service/showdown.py   orchestrate run (build grid → repo.run_grid → repo.judge
                        → assemble ShowdownRun → persist), list/get/export/score
  runtime/showdown.py   POST /runs, GET /runs, GET /runs/{id},
                        GET /runs/{id}/export, POST /runs/{id}/scores
  main.py               register showdown router; rename title; new B2 env checks
```

Frontend: `/showdowns` (list), `/showdowns/new` (form), `/showdowns/[id]`
(grid+leaderboard); adapt `/` dashboard; add sidebar entry; `lib/api-client.ts`
+ `lib/queries.ts` hooks. Keep `/files`, `/upload`, `/design`, `/settings`.
