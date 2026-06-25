<!-- last_verified: 2026-06-25 -->
# Reliability

Reliability expectations and practices for this project.

## Long-Running, Blocking Endpoints

Some handlers wrap fully synchronous, long-blocking work (e.g. `POST /runs`
runs many minutes of blocking NVIDIA NIM HTTP calls via Genblaze plus blocking
boto3 B2 writes inside `service.showdown.create_run`).

- Such handlers MUST be declared as plain `def`, not `async def`. FastAPI runs
  non-coroutine path operations in its threadpool, so the long blocking call
  never occupies the asyncio event loop.
- Declaring one of these as `async def` blocks the event loop for the entire
  run on a single-worker uvicorn: every other request returns HTTP 000, the
  server cannot process the client's disconnect/cancellation, and the worker
  has to be SIGKILL'd. The run is lost (never persisted to B2, never returned).
- Short, infrequent blocking calls (the file/upload/list endpoints) tolerate
  `async def` in practice, but the long generation run does not.

## Health Checks

- `GET /health` verifies B2 connectivity and returns `healthy` or `degraded`
- Health endpoint is always available, even when B2 is down

## Error Handling

- HTTP handlers return structured error responses with appropriate status codes
- External service failures (B2) are caught and surfaced as 500/503 responses
- No unhandled exceptions leak stack traces to clients

## Logging

- Structured JSON logging via Python stdlib
- Every request gets a `request_id` for tracing
- Log levels: ERROR for failures, WARNING for degraded state, INFO for requests

## Observability

- Request timing middleware logs duration for every request
- `/metrics` endpoint exposes basic Prometheus-format counters
- Upload success/failure counts tracked

## Graceful Degradation

- File listing returns empty list (not error) when B2 has no objects
- Metadata extraction failures don't block upload (return partial metadata)
- Frontend shows skeleton states while loading, error states on failure

## Deployment

- Railway health checks on `/health`
- Zero-downtime deploys via rolling updates
- Environment-specific configuration via env vars (no config files in prod)
