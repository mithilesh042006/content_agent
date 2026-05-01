"""Schema for the Explainer — post-decision LLM narrative."""

from pydantic import BaseModel, Field


class ExplanationResponse(BaseModel):
    """LLM-generated rationale for a pre-computed decision."""

    reason: str = Field(
        ...,
        description="2–3 sentence rationale referencing the outcome gap and key metrics"
    )
    chosen_because: str = Field(
        ...,
        description="One-sentence high-signal summary of why the winner won"
    )
    trade_off_narrative: str = Field(
        default="",
        description="Human-readable trade-off explanation (when uncertainty is present)"
    )
    rejection_narratives: str = Field(
        default="",
        description="Brief explanation of why top rejected alternatives lost"
    )
