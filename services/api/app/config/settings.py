from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # --- Backblaze B2 (S3-compatible API) ---
    # Standardized B2_* names. The S3 endpoint is DERIVED from the region
    # (https://s3.{region}.backblazeb2.com) so there is exactly one source of
    # truth for the bucket location — no separate endpoint var to drift.
    b2_application_key_id: str = ""
    b2_application_key: str = ""
    b2_bucket_name: str = ""
    b2_region: str = ""
    b2_public_url_base: str = ""

    # --- NVIDIA NIM (LLM generation + judging, via Genblaze) ---
    nvidia_api_key: str = ""
    showdown_gen_model: str = "meta/llama-3.3-70b-instruct"
    showdown_judge_model: str = "meta/llama-3.3-70b-instruct"
    # Per-request HTTP timeout (seconds) for generation + judge calls. The
    # genblaze NVIDIA surfaces default to 60s, which is too short for the
    # default 70B model on NIM's free tier (verbose prompts / structured judge
    # output regularly take 115-180s), causing dropped cells and null judges.
    showdown_request_timeout: float = 300.0

    api_port: int = 8000
    # Explicit allowlist by default — covers Next on :3000 and the
    # fallback :3001 it picks if 3000 is busy. Production deploys should
    # override with the exact frontend origin.
    api_cors_origins: str = "http://localhost:3000,http://localhost:3001"
    # Optional dev-only escape hatch: a regex that matches additional
    # allowed origins. Empty by default — set this to e.g.
    # `^http://localhost:\d+$` to accept any localhost port without
    # listing each one. NEVER ship this to production.
    api_cors_origin_regex: str = ""

    # Upload limits
    max_file_size: int = 100 * 1024 * 1024  # 100MB

    # Small durable counters (downloads, etc). Point at a persistent
    # volume in production if you care about surviving restarts.
    download_count_file: str = "data/download_count.json"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    @property
    def b2_endpoint(self) -> str:
        """Derive the B2 S3 endpoint from the region.

        Backblaze B2's S3-compatible endpoint always follows
        ``https://s3.<region>.backblazeb2.com``, so we never store the
        endpoint separately — it is a pure function of the region.
        """
        return f"https://s3.{self.b2_region}.backblazeb2.com"

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.api_cors_origins.split(",")]


settings = Settings()
