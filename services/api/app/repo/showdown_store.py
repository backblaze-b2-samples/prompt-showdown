"""B2 run-record store for showdown runs (S3-compatible API, boto3).

The canonical record for every showdown run is a single JSON object at
``showdowns/<run_id>/run.json``. This module owns the small put/get/list
surface for those records; the heavier file-explorer / upload helpers live in
``b2_client.py`` and the genblaze provenance sink lives in ``genblaze_repo.py``.

All three share the same bucket and the same ``showdowns/<run_id>/`` prefix.
"""

import io
import json
import logging

from botocore.exceptions import ClientError

from app.config import settings
from app.repo.b2_client import get_s3_client

logger = logging.getLogger(__name__)

# Every run record lives under this single prefix. The scoped Run History
# explorer lists exactly this prefix; the full-bucket /files explorer still
# sees everything.
RUN_PREFIX = "showdowns/"


def _run_key(run_id: str) -> str:
    return f"{RUN_PREFIX}{run_id}/run.json"


def put_run(run_id: str, record: dict) -> None:
    """Write (or overwrite) the canonical run record JSON to B2."""
    client = get_s3_client()
    body = json.dumps(record, separators=(",", ":")).encode("utf-8")
    try:
        client.put_object(
            Bucket=settings.b2_bucket_name,
            Key=_run_key(run_id),
            Body=io.BytesIO(body),
            ContentType="application/json",
        )
    except ClientError as e:
        raise RuntimeError(f"B2 run-record write failed for '{run_id}': {e}") from e


def get_run(run_id: str) -> dict | None:
    """Read a single run record JSON from B2, or None if it does not exist."""
    client = get_s3_client()
    try:
        response = client.get_object(
            Bucket=settings.b2_bucket_name, Key=_run_key(run_id)
        )
    except ClientError as e:
        code = e.response.get("Error", {}).get("Code", "")
        if code in ("404", "NoSuchKey"):
            return None
        raise RuntimeError(f"B2 run-record read failed for '{run_id}': {e}") from e
    return json.loads(response["Body"].read())


def list_runs(max_keys: int = 1000) -> list[dict]:
    """List run record summaries scoped to the ``showdowns/`` prefix.

    Returns the parsed run records (newest first). Uses a delimiter so each
    run folder is discovered once, then fetches its ``run.json``.
    """
    client = get_s3_client()
    summaries: list[dict] = []
    try:
        paginator = client.get_paginator("list_objects_v2")
        for page in paginator.paginate(
            Bucket=settings.b2_bucket_name,
            Prefix=RUN_PREFIX,
            Delimiter="/",
            PaginationConfig={"MaxItems": max_keys},
        ):
            for cp in page.get("CommonPrefixes", []):
                # cp["Prefix"] == "showdowns/<run_id>/"
                run_id = cp["Prefix"][len(RUN_PREFIX):].rstrip("/")
                record = get_run(run_id)
                if record is not None:
                    summaries.append(record)
    except ClientError as e:
        raise RuntimeError(f"B2 run-record list failed: {e}") from e
    summaries.sort(key=lambda r: r.get("created_at", ""), reverse=True)
    return summaries
