"""Schemas for the Feedback / learning-loop agent endpoint."""

from typing import Optional, Dict

from pydantic import BaseModel, Field


class FeedbackRequest(BaseModel):
    """Input for the feedback loop — combines user context + prior outputs + mock actuals."""

    # Original user context
    business_domain: str = Field(..., min_length=2, max_length=200)
    content_goal: str = Field(..., min_length=5, max_length=500)
    target_audience: str = Field(..., min_length=3, max_length=300)
    tone: str = Field(default="professional", max_length=50)

    # Prior agent outputs
    topic: str = Field(..., description="Topic from decision stage")
    platform: str = Field(..., description="Platform from decision stage")
    format: str = Field(default="", description="Format from decision stage")
    predicted_reach: int = Field(..., ge=0, description="Reach from simulation stage")
    predicted_engagement: float = Field(..., ge=0.0, le=100.0, description="Engagement from simulation")
    predicted_conversion: float = Field(default=0.0, ge=0.0, le=100.0, description="Conversion from simulation")
    headline: str = Field(..., description="Headline from content stage")

    # Context for memory + learning
    goal_type: str = Field(default="conversion")
    audience_segment: str = Field(default="")
    business_type: str = Field(default="")
    time_window: str = Field(default="")
    outcome_score: float = Field(default=0.0)

    # Optional mock actual metrics (generated server-side if absent)
    actual_reach: Optional[int] = Field(default=None, ge=0)
    actual_engagement: Optional[float] = Field(default=None, ge=0.0, le=100.0)
    actual_conversion: Optional[float] = Field(default=None, ge=0.0, le=100.0)


class FeedbackResponse(BaseModel):
    """Performance analysis with structured simulation parameter updates."""

    actual_reach: int = Field(..., ge=0)
    actual_engagement: float = Field(..., ge=0.0, le=100.0)
    actual_conversion: float = Field(default=0.0, ge=0.0, le=100.0)

    # ── Structured deltas ────────────────────────────────────────
    predicted: Dict[str, float] = Field(
        ..., description="{ reach, engagement, conversion }"
    )
    actual: Dict[str, float] = Field(
        ..., description="{ reach, engagement, conversion }"
    )
    delta: Dict[str, float] = Field(
        ..., description="{ reach, engagement, conversion } — difference"
    )

    # ── Simulation parameter updates ─────────────────────────────
    simulation_param_updates: Dict[str, Dict[str, float]] = Field(
        default_factory=dict,
        description="Multiplier adjustments: { category: { key: delta } }"
    )
    state_version: int = Field(default=0, description="State version after updates")

    # ── Structured strategy-update fields ────────────────────────
    what_worked: str = Field(..., description="Elements of the strategy that performed well")
    what_underperformed: str = Field(..., description="Elements that fell short")
    why_underperformed: str = Field(..., description="Root-cause hypothesis")
    what_should_change: str = Field(..., description="Concrete, actionable change")
    should_platform_change: bool = Field(..., description="Whether to switch platform")
    platform_change_reason: str = Field(default="")

    # ── Preserved for continuity ─────────────────────────────────
    next_recommendation: str = Field(..., description="One-sentence actionable recommendation")
    learning_note: str = Field(..., description="Key learning from predicted vs actual")
