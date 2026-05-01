"""Schema for the Decision layer — outcome-driven, with rejection log and trade-off."""

from typing import List, Optional, Dict, Any

from pydantic import BaseModel, Field
from app.schemas.simulation import CandidateSimulation


# ── Legacy scoring weight definition (kept for signal scoring) ────────────
SCORE_WEIGHTS = {
    "audience_fit": 0.25,
    "goal_fit": 0.25,
    "format_fit": 0.20,
    "conversion_fit": 0.20,
    "tone_fit": 0.05,
    "timing_fit": 0.05,
}


def compute_weighted_total(score: dict[str, float]) -> float:
    """Compute the weighted total from individual axis scores (signal scoring)."""
    return round(sum(score.get(k, 0) * w for k, w in SCORE_WEIGHTS.items()), 2)


class PlatformScore(BaseModel):
    """Signal scores for one platform — used as simulation inputs, not decision drivers."""

    platform: str
    audience_fit: float = Field(default=5.0, ge=0, le=10)
    goal_fit: float = Field(default=5.0, ge=0, le=10)
    format_fit: float = Field(default=5.0, ge=0, le=10)
    conversion_fit: float = Field(default=5.0, ge=0, le=10)
    tone_fit: float = Field(default=5.0, ge=0, le=10)
    timing_fit: float = Field(default=5.0, ge=0, le=10)
    total: float = Field(default=30.0, ge=0, le=60)
    weighted_total: float = Field(default=5.0, ge=0, le=10)
    why: str = Field(default="")


class CandidateTopic(BaseModel):
    """One candidate content angle considered during strategy generation."""

    angle: str
    audience_fit_rationale: str = Field(default="")
    goal_fit_rationale: str = Field(default="")
    selected: bool = Field(default=False)


class RejectedAlternative(BaseModel):
    """A candidate that was not selected, with explicit reason."""

    candidate_id: str
    platform: str
    topic: str
    format: str
    outcome_score: float
    predicted_conversion: float
    reason: str


class TradeOffAnalysis(BaseModel):
    """Analysis when top-2 candidates are within the uncertainty threshold."""

    candidate_a: str
    candidate_a_score: float
    candidate_a_strength: str
    candidate_b: str
    candidate_b_score: float
    candidate_b_strength: str
    delta: float
    trade_off: str
    decision_rationale: str


class DecisionResponse(BaseModel):
    """Outcome-driven decision response — winner selected by computed outcome_score."""

    # ── Winner ────────────────────────────────────────────────────
    topic: str
    platform: str
    format: str = Field(default="")
    posting_time: str
    outcome_score: float = Field(default=0.0, description="THE decision metric")
    decision_score: float = Field(default=0.0, description="Alias for outcome_score (compat)")

    # ── Predicted metrics from simulation ─────────────────────────
    predicted_reach: int = Field(default=0)
    predicted_engagement: float = Field(default=0.0)
    predicted_conversion: float = Field(default=0.0)

    # ── Explanation (from explainer) ──────────────────────────────
    reason: str = Field(default="")
    chosen_because: str = Field(default="")

    # ── Full candidate visibility ─────────────────────────────────
    candidate_topics: List[CandidateTopic] = Field(default_factory=list)
    platform_scores: List[PlatformScore] = Field(default_factory=list)
    all_evaluated: List[CandidateSimulation] = Field(default_factory=list)
    rejected: List[RejectedAlternative] = Field(default_factory=list)
    trade_off_analysis: Optional[TradeOffAnalysis] = None

    interpretation_used: str = Field(default="")

    # ── Uncertainty-aware decision ────────────────────────────────
    decision_confidence: str = Field(
        default="medium", description="'high', 'medium', 'low', or 'none'"
    )
    uncertainty_flag: bool = Field(
        default=False, description="True when top-2 are close"
    )
    confidence_score: float = Field(
        default=0.5, ge=0.0, le=1.0,
        description="Numeric confidence in the decision"
    )

    # ── Exploration ───────────────────────────────────────────────
    exploration_triggered: bool = Field(default=False)
    exploration_reason: str = Field(default="")
    exploration_swapped: bool = Field(default=False)
    original_winner_id: str = Field(default="")
    ab_test_alternative: Optional[Dict[str, Any]] = None

    # ── Quality assessment ────────────────────────────────────────
    relative_score: float = Field(
        default=0.5, ge=0.0, le=1.0,
        description="Winner's score as fraction of theoretical max"
    )
    strategy_quality_warning: bool = Field(default=False)
    quality_warning_reason: str = Field(default="")
    no_viable_strategy: bool = Field(default=False)
