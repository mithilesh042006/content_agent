"""Schema for strategy candidates — full strategy tuples (platform × topic × format × time)."""

from typing import List, Optional

from pydantic import BaseModel, Field


class StrategyCandidate(BaseModel):
    """One complete strategy combination to be simulated.

    Each candidate is a fully-specified strategy: platform + topic + format + time.
    Signal scores (6-axis) are inputs to simulation, not the decision mechanism.
    """

    candidate_id: str = Field(
        ..., description="Unique identifier, e.g. 'instagram-deals-carousel-evening'"
    )
    platform: str = Field(..., description="Target platform")
    topic: str = Field(..., description="Specific content angle")
    format: str = Field(..., description="Content format: carousel, short-form video, etc.")
    posting_time: str = Field(..., description="Human-readable posting time recommendation")
    time_window: str = Field(
        ..., description="Normalized time category: weekday_morning, weekday_evening, etc."
    )

    # Context from interpretation — drives goal-adaptive scoring + memory matching
    goal_type: str = Field(..., description="From interpretation — drives outcome weight profile")
    audience_segment: str = Field(..., description="From interpretation — drives memory matching")
    business_type: str = Field(default="", description="From interpretation — drives memory matching")

    # Signal scores (6-axis) — INPUTS to simulation, not the decision
    audience_fit: float = Field(default=5.0, ge=0, le=10)
    goal_fit: float = Field(default=5.0, ge=0, le=10)
    format_fit: float = Field(default=5.0, ge=0, le=10)
    conversion_fit: float = Field(default=5.0, ge=0, le=10)
    tone_fit: float = Field(default=5.0, ge=0, le=10)
    timing_fit: float = Field(default=5.0, ge=0, le=10)

    # Feasibility — from format cost model
    feasibility: float = Field(
        default=0.70, ge=0.0, le=1.0,
        description="Production feasibility of this format (0–1, higher = easier)"
    )


class CandidatePool(BaseModel):
    """All candidate strategies generated for a single brief."""

    candidates: List[StrategyCandidate] = Field(
        ..., min_length=1,
        description="8–15 full strategy combinations"
    )
    generation_method: str = Field(
        default="fallback",
        description="'llm' or 'fallback'"
    )
