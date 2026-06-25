"""Genblaze-backed AI orchestration for showdown runs.

ALL genblaze imports are contained in this module (the repo/ layer). Generation
runs as a real Pipeline step (``NvidiaChatProvider``) fanned across the shared
input set with ``batch_run``; judging uses the structured-output ``chat()``
helper. Outputs + a SHA-256 provenance manifest are persisted to B2 through
``ObjectStorageSink(S3StorageBackend.for_backblaze(...))`` under the run's
``showdowns/<run_id>/cells/`` prefix.

Storage credentials are passed as EXPLICIT kwargs from our standardized
``B2_*`` settings — we do NOT rely on genblaze's own env auto-read, which
expects ``B2_KEY_ID`` / ``B2_APP_KEY``.
"""

import json
import logging

from genblaze_core import (
    KeyStrategy,
    Modality,
    ObjectStorageSink,
    Pipeline,
    PromptTemplate,
)
from genblaze_nvidia import NvidiaChatProvider, chat
from genblaze_s3 import S3StorageBackend
from pydantic import BaseModel

from app.config import settings

logger = logging.getLogger(__name__)

# Concurrency for the per-variant batch fan-out. Kept modest so a default demo
# run stays well under NVIDIA NIM's free-tier rate limit (~40 req/min).
_MAX_CONCURRENCY = 4


class JudgeVerdict(BaseModel):
    """Structured judge output. One per generated cell."""

    score: int  # 1..10
    rationale: str


def _sink(run_id: str) -> ObjectStorageSink:
    """Build a genblaze provenance sink scoped under this run's B2 prefix.

    Explicit kwargs from our standardized ``B2_*`` settings — genblaze-s3
    derives the S3 endpoint from ``region`` itself, so we never pass a raw
    endpoint or hardcode a region.
    """
    backend = S3StorageBackend.for_backblaze(
        settings.b2_bucket_name,
        region=settings.b2_region,
        key_id=settings.b2_application_key_id,
        app_key=settings.b2_application_key,
        public_url_base=settings.b2_public_url_base or None,
        preflight=False,
    )
    return ObjectStorageSink(
        backend,
        prefix=f"showdowns/{run_id}/cells",
        key_strategy=KeyStrategy.HIERARCHICAL,
    )


def _text_from_result(result) -> str:
    """Extract the chat text the NvidiaChatProvider stored on the output asset."""
    steps = getattr(result.run, "steps", [])
    for step in reversed(steps):
        for asset in step.assets:
            text = (asset.metadata or {}).get("text")
            if text:
                return text
    return ""


def run_variant(
    run_id: str, variant_name: str, template_text: str, input_rows: list[dict], model: str
) -> list[str]:
    """Run one prompt variant across the shared input set via a Pipeline.

    ``input_rows`` is a list of variable dicts that fill the ``PromptTemplate``.
    Returns the generated output text per input row, in order. Each cell's
    output + a provenance manifest is persisted to B2 by the sink.
    """
    template = PromptTemplate(template=template_text)
    pipeline = Pipeline(
        f"showdown-{run_id}-{variant_name}", max_concurrency=_MAX_CONCURRENCY
    ).step(
        NvidiaChatProvider(
            api_key=settings.nvidia_api_key or None,
            timeout=settings.showdown_request_timeout,
        ),
        model=model,
        prompt=template,
        modality=Modality.TEXT,
    )
    results = pipeline.batch_run(input_rows, sink=_sink(run_id), raise_on_failure=False)
    return [_text_from_result(r) for r in results]


def judge_cell(output_text: str, criteria: str, model: str) -> JudgeVerdict:
    """Score one generated output with a structured-output judge call.

    Uses genblaze's uniform ``chat()`` surface with ``response_format`` set to
    the ``JudgeVerdict`` Pydantic model. No bare provider SDK is used here.
    """
    resp = chat(
        model,
        system="You are a strict evaluator. Score the candidate output from 1 (poor) to 10 (excellent) and explain briefly.",
        prompt=f"Criteria:\n{criteria}\n\nOutput:\n{output_text}",
        response_format=JudgeVerdict,
        temperature=0,
        api_key=settings.nvidia_api_key or None,
        timeout=settings.showdown_request_timeout,
    )
    data = json.loads(resp.text)
    return JudgeVerdict.model_validate(data)
