"""Schema for the Simulation engine — per-candidate results + aggregated response."""

from typing import List, Optional, Dict, Any

from pydantic import BaseModel, Field


class FormulaInputs(BaseModel):
    """Raw formula parameters — every prediction is traceable to these inputs."""

    base_reach_ceiling: int = Field(..., description="Platform reach ceiling")
    reach_signal: float = Field(..., description="Composite reach input signal (pre-saturation)")
    engagement_signal: float = Field(..., description="Composite engagement input signal")
    conversion_signal: float = Field(..., description="Composite conversion input signal")
    format_synergy: float = Field(..., description="Platform × format interaction multiplier")
    goal_synergy: float = Field(..., description="Platform × goal interaction multiplier")
    audience_synergy: float = Field(..., description="Audience × platform interaction multiplier")
    platform_multiplier: float = Field(..., description="Learned platform effectiveness (from state)")
    format_multiplier: float = Field(..., description="Learned format effectiveness (from state)")
    cta_multiplier: float = Field(..., description="Learned CTA effectiveness (from state)")
    time_synergy_reach: float = Field(..., description="Static time reach multiplier")
    time_synergy_engagement: float = Field(..., description="Static time engagement multiplier")
    time_learned_multiplier: float = Field(default=1.0, description="Learned time adjustment")
    feasibility: float = Field(..., description="Format feasibility score")
    complexity_penalty: float = Field(..., description="Format complexity penalty")
    memory_boost: float = Field(..., description="Memory-based performance adjustment")
    signal_consistency: float = Field(..., description="min(signals)/max(signals)")
    consistency_multiplier: float = Field(..., description="Confidence penalty from signal conflict")
    goal_weight_profile: str = Field(..., description="Which weight profile was used")
    outcome_weights: Dict[str, float] = Field(..., description="Actual weights applied")


class CandidateSimulation(BaseModel):
    """Simulation result for one candidate strategy."""

    candidate_id: str = Field(..., description="Links back to StrategyCandidate")
    platform: str = Field(default="")
    topic: str = Field(default="")
    format: str = Field(default="")

    predicted_reach: int = Field(..., ge=0)
    predicted_engagement: float = Field(..., ge=0.0, le=100.0)
    predicted_conversion: float = Field(..., ge=0.0, le=100.0)
    confidence: float = Field(..., ge=0.0, le=1.0)
    feasibility: float = Field(..., ge=0.0, le=1.0)
    complexity_penalty: float = Field(..., ge=0.90, le=1.0)

    outcome_score: float = Field(
        ..., description="THE decision metric — goal-adaptive, memory-adjusted"
    )
    formula_inputs: FormulaInputs = Field(
        ..., description="Full traceability — every number derived from these"
    )


class SimulationResponse(BaseModel):
    """Full simulation results across all candidates + winner comparison."""

    all_candidates: List[CandidateSimulation] = Field(
        ..., description="Simulation results for every candidate, sorted by outcome_score desc"
    )
    winner: CandidateSimulation = Field(
        ..., description="Highest outcome_score candidate"
    )
    runner_up: Optional[CandidateSimulation] = Field(
        default=None, description="Second-highest outcome_score candidate"
    )
    comparison_summary: str = Field(
        ..., description="1–2 sentence comparison between winner and runner-up"
    )
    score_breakdown: List[str] = Field(
        ..., description="3–5 bullet rationale lines"
    )
