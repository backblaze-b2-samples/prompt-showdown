"""Showdown orchestration: build the grid, generate, judge, persist to B2.

Layering: this service calls the repo/ adapters (genblaze for AI, the B2 run
store for the canonical JSON record) and returns Pydantic models. No SDK calls
happen here directly.
"""

import logging
import re
import uuid
from datetime import UTC, datetime

from app.config import settings
from app.repo import get_run, judge_cell, list_runs, put_run, run_variant
from app.service.scoring import (
    aggregate_stats,
    build_leaderboard,
    to_summary,
    variant_wins,
)
from app.types import (
    CreateRunRequest,
    RunCell,
    RunSummary,
    ScoreRequest,
    ShowdownRun,
    ShowdownStats,
    VariantWins,
)

logger = logging.getLogger(__name__)

_RUN_ID_RE = re.compile(r"^[A-Za-z0-9_-]+$")


class RunNotFoundError(Exception):
    def __init__(self, detail: str = "Run not found"):
        self.detail = detail
        super().__init__(detail)


class RunInputError(Exception):
    def __init__(self, detail: str = "Invalid run input"):
        self.detail = detail
        super().__init__(detail)


def _validate_run_id(run_id: str) -> None:
    if not run_id or not _RUN_ID_RE.match(run_id):
        raise RunInputError("Invalid run id")


def create_run(req: CreateRunRequest) -> ShowdownRun:
    """Execute the variant x input grid, judge, assemble, and persist to B2."""
    gen_model = req.gen_model or settings.showdown_gen_model
    judge_model = req.judge_model or settings.showdown_judge_model
    run_id = datetime.now(UTC).strftime("%Y%m%d-%H%M%S-") + uuid.uuid4().hex[:8]

    input_rows = [inp.vars for inp in req.inputs]
    input_labels = [inp.label for inp in req.inputs]
    variant_names = [v.name for v in req.variants]

    cells: list[RunCell] = []
    for variant in req.variants:
        outputs = run_variant(
            run_id, variant.name, variant.template, input_rows, gen_model
        )
        for label, output in zip(input_labels, outputs, strict=True):
            judge_score: int | None = None
            judge_rationale: str | None = None
            if req.judge_enabled and output:
                try:
                    verdict = judge_cell(output, req.criteria, judge_model)
                    judge_score, judge_rationale = verdict.score, verdict.rationale
                except Exception as e:  # judging is best-effort per cell
                    logger.warning("Judge failed for %s/%s: %s", variant.name, label, e)
            cells.append(
                RunCell(
                    variant=variant.name,
                    input_label=label,
                    output=output,
                    judge_score=judge_score,
                    judge_rationale=judge_rationale,
                )
            )

    leaderboard = build_leaderboard(variant_names, input_labels, cells)
    run = ShowdownRun(
        run_id=run_id,
        title=req.title,
        created_at=datetime.now(UTC).isoformat(),
        gen_model=gen_model,
        judge_model=judge_model,
        judge_enabled=req.judge_enabled,
        criteria=req.criteria,
        variants=req.variants,
        inputs=req.inputs,
        cells=cells,
        leaderboard=leaderboard,
    )
    put_run(run_id, run.model_dump())
    logger.info("Showdown run created: run_id=%s variants=%d", run_id, len(req.variants))
    return run


def get_run_detail(run_id: str) -> ShowdownRun:
    _validate_run_id(run_id)
    record = get_run(run_id)
    if record is None:
        raise RunNotFoundError()
    return ShowdownRun.model_validate(record)


def list_run_summaries() -> list[RunSummary]:
    runs = [ShowdownRun.model_validate(r) for r in list_runs()]
    return [to_summary(r) for r in runs]


def export_run(run_id: str) -> dict:
    """Return the full run record as a plain dict for JSON download."""
    return get_run_detail(run_id).model_dump()


def record_human_score(run_id: str, req: ScoreRequest) -> ShowdownRun:
    """Write a human rating into the run record on B2 and recompute leaderboard."""
    run = get_run_detail(run_id)
    matched = False
    for cell in run.cells:
        if cell.variant == req.variant and cell.input_label == req.input_label:
            cell.human_score = req.human_score
            matched = True
            break
    if not matched:
        raise RunInputError("No matching cell for the given variant/input")
    run.leaderboard = build_leaderboard(
        [v.name for v in run.variants],
        [i.label for i in run.inputs],
        run.cells,
    )
    put_run(run_id, run.model_dump())
    return run


def get_stats() -> ShowdownStats:
    runs = [ShowdownRun.model_validate(r) for r in list_runs()]
    return aggregate_stats(runs)


def get_variant_wins() -> list[VariantWins]:
    runs = [ShowdownRun.model_validate(r) for r in list_runs()]
    return variant_wins(runs)
