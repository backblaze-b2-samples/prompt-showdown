"""Pydantic models for prompt-showdown runs. No logic — boundary types only."""

from pydantic import BaseModel, Field


class PromptVariant(BaseModel):
    """A named prompt template version under comparison."""

    name: str
    template: str  # uses {variable} placeholders filled per input row


class ShowdownInput(BaseModel):
    """One row of the shared input set: a label + the template-variable fills."""

    label: str
    vars: dict[str, str] = Field(default_factory=dict)


class RunCell(BaseModel):
    """One cell of the variant x input grid."""

    variant: str
    input_label: str
    output: str
    judge_score: int | None = None
    judge_rationale: str | None = None
    human_score: int | None = None


class VariantScore(BaseModel):
    """Leaderboard entry: aggregate scores for one variant."""

    variant: str
    avg_judge_score: float | None = None
    avg_human_score: float | None = None
    wins: int = 0  # number of inputs where this variant had the top judge score


class ShowdownRun(BaseModel):
    """The canonical run record persisted as a single JSON object on B2."""

    run_id: str
    title: str
    created_at: str
    gen_model: str
    judge_model: str
    judge_enabled: bool
    criteria: str
    variants: list[PromptVariant]
    inputs: list[ShowdownInput]
    cells: list[RunCell]
    leaderboard: list[VariantScore] = Field(default_factory=list)


class RunSummary(BaseModel):
    """Lightweight summary for the Run History list + dashboard."""

    run_id: str
    title: str
    created_at: str
    gen_model: str
    variant_count: int
    input_count: int
    judge_enabled: bool
    best_variant: str | None = None
    avg_judge_score: float | None = None


class ShowdownStats(BaseModel):
    """Dashboard aggregate metrics across all runs."""

    total_runs: int
    total_variants_compared: int
    avg_judge_score: float | None
    best_variant: str | None


class VariantWins(BaseModel):
    """Wins-per-variant chart datum (aggregated across runs)."""

    variant: str
    wins: int


class CreateRunRequest(BaseModel):
    """Payload to launch a new showdown run."""

    title: str
    variants: list[PromptVariant] = Field(min_length=1)
    inputs: list[ShowdownInput] = Field(min_length=1)
    gen_model: str | None = None
    judge_model: str | None = None
    judge_enabled: bool = True
    criteria: str = "Accuracy, relevance, and clarity of the response."


class ScoreRequest(BaseModel):
    """Human rating written back into a run record."""

    variant: str
    input_label: str
    human_score: int = Field(ge=1, le=10)
