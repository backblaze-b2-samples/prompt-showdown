<!-- last_verified: 2026-06-24 -->
# Architecture

**Prompt Showdown** runs N prompt variants across a shared input set, scores
each output with an LLM judge (and optionally a human), and preserves the whole
run on Backblaze B2 as the durable system of record.

## Components

- **apps/web/** — Next.js 16 frontend (App Router, Tailwind v4, shadcn/ui)
  - Dashboard with showdown metrics (runs, variants compared, wins-per-variant, recent runs)
  - Run History explorer (`/showdowns`) scoped to the B2 `showdowns/` prefix
  - New Showdown form (`/showdowns/new`) and run-detail grid + leaderboard (`/showdowns/[id]`)
  - Kept from the starter kit: file upload, full-bucket file browser
  - Dark mode via `next-themes`
- **services/api/** — FastAPI backend (layered architecture)
  - REST API for showdown runs (create/list/get/export/score) + files/upload
  - AI generation + judging via the **Genblaze SDK** (NVIDIA NIM)
  - B2 S3 integration via boto3 (run records + file explorer)
  - Health check endpoint with B2 connectivity verification
  - Structured JSON logging with request tracing
  - Prometheus-format metrics endpoint
- **packages/shared/** — TypeScript type definitions
  - Mirrors Pydantic models from the API
  - Consumed by `apps/web/` as workspace dependency

## Backend Layering

The API follows a strict layered architecture:

```
types/     Pydantic models — no logic, no imports from other layers
  |
config/    Settings (pydantic-settings) — depends only on types
  |
repo/      Data access (boto3 B2 client) — no business logic
  |
service/   Business logic — calls repo, returns types
  |
runtime/   FastAPI routes — calls service, never repo directly
```

### Layering Rules

1. Dependencies flow downward only: `types` -> `config` -> `repo` -> `service` -> `runtime`
2. No backward imports (e.g., service must not import from runtime)
3. `boto3` **and** `genblaze*` only allowed in `repo/` layer
4. All boundary data uses Pydantic models (no raw dicts across layers)
5. Each file stays under 300 lines

### Provider orchestration (Genblaze)

All AI-provider calls route through the Genblaze SDK, never a bare provider SDK,
and every genblaze import is contained in `repo/genblaze_repo.py`:

- **Generation** is a real Pipeline step:
  `Pipeline(name, max_concurrency=4).step(NvidiaChatProvider(), model=..., prompt=PromptTemplate(...), modality=Modality.TEXT).batch_run(input_rows, sink=...)`
  fans the shared input set across one pipeline per variant.
- **Judging** uses Genblaze's uniform `chat(model, ..., response_format=JudgeVerdict)`
  structured-output call, producing `{score, rationale}` per cell.
- A no-network signature-guard test (`tests/test_genblaze_signatures.py`)
  monkeypatches the SDK surfaces and asserts our call shapes, so genblaze SDK
  drift fails in CI rather than at runtime.

### Directory Structure

```
services/api/
  main.py                  App entrypoint, middleware, router registration
  app/
    types/                 Pydantic models (FileMetadata, UploadStats, etc.)
    config/                Settings loaded from environment
    repo/                  B2 S3 client (data access layer)
    service/               Business logic (upload, files, metadata)
    runtime/               FastAPI route handlers
  tests/                   pytest tests (structural + integration)
```

## Boundary Invariants

- **No external SDK leakage**: `boto3` and `genblaze*` are only imported in `app/repo/`. All other layers interact with B2 and the AI providers through the repo interface.
- **No raw dicts at boundaries**: All data crossing layer boundaries uses typed Pydantic models.
- **No mutable globals**: Configuration is read-only after init. No module-level mutable state shared between layers.
- **Validated inputs**: All HTTP inputs validated by FastAPI/Pydantic. All file/run keys validated.

### Custom user agent (Standard #2)

- The boto3 S3 client in `repo/b2_client.py` (shared by the file explorer, run
  records, upload) sets `user_agent_extra="b2ai-prompt-showdown"`.
- The Genblaze provenance sink owns its own boto3 client inside `genblaze-s3`
  and sets a `b2ai-genblaze/<version>` user agent; `S3StorageBackend.for_backblaze`
  exposes no UA hook. Overriding it would mean fighting the third-party SDK, so
  this is a **justified deviation** (same class as the PyArrow/PyIceberg case) —
  the sample's per-app identity is still carried by the boto3 client above, the
  `Pipeline(name="showdown-...")`, and the manifests written under the run prefix.

## Deployment

- **Local dev** — `pnpm dev` runs both services via `concurrently`
  - Web: `localhost:3000`
  - API: `localhost:8000`
- **Railway** — two services from the same repo
  - See `infra/railway/README.md` for configuration

## Data Stores

- **Backblaze B2** — object storage (S3-compatible API). No application
  database; B2 is the sole data store. Two cooperating S3 paths under one
  per-run prefix `showdowns/<run_id>/`:
  1. **App run-record store** (`repo/showdown_store.py`, boto3) — the canonical
     record at `showdowns/<run_id>/run.json` holding variants, inputs, per-cell
     outputs, judge + human scores, models, timestamps. Ops: `put_object` (write),
     `get_object` (detail/export), `list_objects_v2` with `Prefix="showdowns/"`
     and a delimiter for the scoped Run History explorer.
  2. **Genblaze provenance sink** (`repo/genblaze_repo.py`, genblaze-s3) — each
     cell's output + a SHA-256 manifest, written under
     `showdowns/<run_id>/cells/...`. This is "every run preserved with full
     inputs/outputs" backed by tamper-evident manifests.
  - The starter-kit full-bucket explorer/upload continue to use the same boto3
    client for put/list/head/delete/presign across the whole bucket.

## External Services

- **Backblaze B2 S3 API** — run-record + file storage, retrieval, deletion, presigned URLs
- **NVIDIA NIM** (via Genblaze) — LLM generation + judging; free tier, no per-token billing

## Trust Boundaries

See [docs/SECURITY.md](docs/SECURITY.md) for full security documentation.

- **Frontend -> API** — CORS-restricted to configured origins
- **API -> B2** — authenticated via application keys, signature v4
- **Client -> B2** — presigned URLs for download (10-min expiry, forced attachment)

## Data Flows

- **Run a showdown**: Browser -> `POST /runs` -> `service/showdown.create_run`
  builds the variant×input grid -> `repo/genblaze_repo.run_variant` (Genblaze
  Pipeline `batch_run`, outputs + manifests to B2) -> `repo/genblaze_repo.judge_cell`
  (structured `chat`) per cell -> `service/scoring` builds the leaderboard ->
  `repo/showdown_store.put_run` writes `showdowns/<run_id>/run.json` -> response.
- **Run History**: Browser -> `GET /runs` -> `repo/showdown_store.list_runs`
  (scoped `Prefix="showdowns/"`) -> summaries.
- **Run detail / export**: Browser -> `GET /runs/{id}` (or `/export`) ->
  `repo/showdown_store.get_run` -> full record.
- **Human score**: Browser -> `POST /runs/{id}/scores` -> service updates the
  matching cell, recomputes the leaderboard, rewrites `run.json` to B2.
- **Upload / List / Download / Delete** (kept): Browser -> files endpoints ->
  service validates -> `repo/b2_client` reads/writes B2 / presigns URLs.

## Observability

- Structured JSON logging on all requests with `request_id`
- Request timing middleware (logs duration per request)
- `/metrics` endpoint (Prometheus format: request count, latency, upload count)
- `/health` endpoint (B2 connectivity check)

## Canonical Files

- Showdown orchestration: `services/api/app/service/showdown.py`
- Genblaze AI repo (contained SDK boundary): `services/api/app/repo/genblaze_repo.py`
- B2 run-record store: `services/api/app/repo/showdown_store.py`
- Showdown API handler: `services/api/app/runtime/showdown.py`
- Layered API handler (kept): `services/api/app/runtime/upload.py`
- B2 data access (repo layer): `services/api/app/repo/b2_client.py`
- Pydantic models: `services/api/app/types/` (`showdown.py`, `files.py`, `upload.py`, `stats.py`)
- Config (pydantic-settings): `services/api/app/config/settings.py`
- Structural + genblaze-guard tests: `services/api/tests/test_structure.py`, `tests/test_genblaze_signatures.py`
- Frontend API client: `apps/web/src/lib/api-client.ts`
- Shared TypeScript types: `packages/shared/src/types.ts`

## Core Features

- [Prompt Variants](docs/features/prompt-variants.md)
- [Showdown Runs](docs/features/showdown-runs.md)
- [LLM Judge](docs/features/llm-judge.md)
- [Run History](docs/features/run-history.md)
- [File Upload](docs/features/file-upload.md)
- [File Browser](docs/features/file-browser.md)
- [Dashboard](docs/features/dashboard.md)
- [Metadata Extraction](docs/features/metadata-extraction.md)

## References

- [docs/SECURITY.md](docs/SECURITY.md) — security principles and implementation
- [docs/RELIABILITY.md](docs/RELIABILITY.md) — reliability expectations
- [AGENTS.md](AGENTS.md) — architectural invariants and agent instructions
