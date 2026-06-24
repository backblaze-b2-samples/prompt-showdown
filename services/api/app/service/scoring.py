"""Leaderboard + aggregate-stats math for showdown runs. Pure functions."""

from collections import defaultdict

from app.types import (
    RunCell,
    RunSummary,
    ShowdownRun,
    ShowdownStats,
    VariantScore,
    VariantWins,
)


def _avg(values: list[int]) -> float | None:
    return round(sum(values) / len(values), 2) if values else None


def build_leaderboard(
    variant_names: list[str], input_labels: list[str], cells: list[RunCell]
) -> list[VariantScore]:
    """Compute per-variant averages + per-input wins from the grid cells."""
    by_variant: dict[str, list[RunCell]] = defaultdict(list)
    for cell in cells:
        by_variant[cell.variant].append(cell)

    wins: dict[str, int] = defaultdict(int)
    for label in input_labels:
        # Find the variant with the highest judge score for this input row.
        best_variant: str | None = None
        best_score: int | None = None
        for cell in cells:
            if cell.input_label != label or cell.judge_score is None:
                continue
            if best_score is None or cell.judge_score > best_score:
                best_score = cell.judge_score
                best_variant = cell.variant
        if best_variant is not None:
            wins[best_variant] += 1

    leaderboard: list[VariantScore] = []
    for name in variant_names:
        variant_cells = by_variant.get(name, [])
        judge_scores = [c.judge_score for c in variant_cells if c.judge_score is not None]
        human_scores = [c.human_score for c in variant_cells if c.human_score is not None]
        leaderboard.append(
            VariantScore(
                variant=name,
                avg_judge_score=_avg(judge_scores),
                avg_human_score=_avg(human_scores),
                wins=wins.get(name, 0),
            )
        )
    # Sort best-first by judge average (None last), then wins.
    leaderboard.sort(
        key=lambda v: (v.avg_judge_score is not None, v.avg_judge_score or 0, v.wins),
        reverse=True,
    )
    return leaderboard


def best_variant(leaderboard: list[VariantScore]) -> str | None:
    return leaderboard[0].variant if leaderboard else None


def run_avg_judge_score(leaderboard: list[VariantScore]) -> float | None:
    scores = [v.avg_judge_score for v in leaderboard if v.avg_judge_score is not None]
    return _avg([round(s) for s in scores]) if scores else None


def to_summary(run: ShowdownRun) -> RunSummary:
    return RunSummary(
        run_id=run.run_id,
        title=run.title,
        created_at=run.created_at,
        gen_model=run.gen_model,
        variant_count=len(run.variants),
        input_count=len(run.inputs),
        judge_enabled=run.judge_enabled,
        best_variant=best_variant(run.leaderboard),
        avg_judge_score=run_avg_judge_score(run.leaderboard),
    )


def aggregate_stats(runs: list[ShowdownRun]) -> ShowdownStats:
    """Roll up dashboard metrics across every run."""
    total_variants = sum(len(r.variants) for r in runs)
    all_judge: list[float] = [
        v.avg_judge_score
        for r in runs
        for v in r.leaderboard
        if v.avg_judge_score is not None
    ]
    # Best variant globally = highest summed wins across runs.
    win_totals: dict[str, int] = defaultdict(int)
    for r in runs:
        for v in r.leaderboard:
            win_totals[v.variant] += v.wins
    best = max(win_totals.items(), key=lambda kv: kv[1])[0] if win_totals else None
    return ShowdownStats(
        total_runs=len(runs),
        total_variants_compared=total_variants,
        avg_judge_score=_avg([round(s) for s in all_judge]) if all_judge else None,
        best_variant=best,
    )


def variant_wins(runs: list[ShowdownRun]) -> list[VariantWins]:
    """Wins-per-variant chart data, aggregated across all runs."""
    win_totals: dict[str, int] = defaultdict(int)
    for r in runs:
        for v in r.leaderboard:
            win_totals[v.variant] += v.wins
    out = [VariantWins(variant=k, wins=v) for k, v in win_totals.items()]
    out.sort(key=lambda x: x.wins, reverse=True)
    return out
