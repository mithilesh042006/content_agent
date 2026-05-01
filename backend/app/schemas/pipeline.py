"""Schema for the full Pipeline endpoint (all stages)."""

from typing import List

from pydantic import BaseModel, Field

from app.schemas.interpretation import InterpretationResponse
from app.schemas.strategy_candidate import CandidatePool
from app.schemas.simulation import SimulationResponse
from app.schemas.decision import DecisionResponse
from app.schemas.explanation import ExplanationResponse
from app.schemas.content import ContentResponse
from app.schemas.feedback import FeedbackResponse


class PipelineResponse(BaseModel):
    """Aggregated output from the simulation-first pipeline."""

    interpretation: InterpretationResponse = Field(
        ..., description="Stage 1 — Brief interpretation"
    )
    candidates: CandidatePool = Field(
        ..., description="Stage 2 — Candidate strategy combinations"
    )
    simulation: SimulationResponse = Field(
        ..., description="Stage 3 — Simulation of all candidates"
    )
    decision: DecisionResponse = Field(
        ..., description="Stage 4 — Outcome-driven decision"
    )
    explanation: ExplanationResponse = Field(
        ..., description="Stage 5 — Post-decision explanation"
    )
    content: ContentResponse = Field(
        ..., description="Stage 6 — Content generation (skipped if no viable strategy)"
    )
    feedback: FeedbackResponse = Field(
        ..., description="Stage 7 — Feedback & learning"
    )
    reasoning_chain: List[str] = Field(
        ...,
        description="Ordered trace of the reasoning pipeline"
    )
