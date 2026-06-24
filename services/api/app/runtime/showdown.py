import logging

from fastapi import APIRouter, HTTPException

from app.service.showdown import (
    RunInputError,
    RunNotFoundError,
    create_run,
    export_run,
    get_run_detail,
    get_stats,
    get_variant_wins,
    list_run_summaries,
    record_human_score,
)
from app.types import (
    CreateRunRequest,
    RunSummary,
    ScoreRequest,
    ShowdownRun,
    ShowdownStats,
    VariantWins,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/runs", response_model=ShowdownRun)
async def create_run_endpoint(req: CreateRunRequest):
    try:
        return create_run(req)
    except RunInputError as e:
        raise HTTPException(status_code=400, detail=e.detail) from None
    except RuntimeError as e:
        logger.error("Showdown run failed: %s", e)
        raise HTTPException(status_code=502, detail="Showdown run failed") from None


@router.get("/runs", response_model=list[RunSummary])
async def list_runs_endpoint():
    return list_run_summaries()


@router.get("/runs/stats", response_model=ShowdownStats)
async def stats_endpoint():
    return get_stats()


@router.get("/runs/stats/wins", response_model=list[VariantWins])
async def wins_endpoint():
    return get_variant_wins()


@router.get("/runs/{run_id}", response_model=ShowdownRun)
async def get_run_endpoint(run_id: str):
    try:
        return get_run_detail(run_id)
    except RunInputError as e:
        raise HTTPException(status_code=400, detail=e.detail) from None
    except RunNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.detail) from None


@router.get("/runs/{run_id}/export")
async def export_run_endpoint(run_id: str):
    try:
        return export_run(run_id)
    except RunInputError as e:
        raise HTTPException(status_code=400, detail=e.detail) from None
    except RunNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.detail) from None


@router.post("/runs/{run_id}/scores", response_model=ShowdownRun)
async def score_run_endpoint(run_id: str, req: ScoreRequest):
    try:
        return record_human_score(run_id, req)
    except RunInputError as e:
        raise HTTPException(status_code=400, detail=e.detail) from None
    except RunNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.detail) from None
