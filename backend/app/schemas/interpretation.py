"""Schema for the Brief Interpretation agent endpoint (Layer A)."""

from typing import List

from pydantic import BaseModel, Field


class InterpretationResponse(BaseModel):
    """Structured interpretation of a raw user brief.

    Converts vague or underspecified user input into precise strategic
    variables that downstream stages (decision, simulation, content,
    feedback) rely on for domain-agnostic reasoning.
    """

    business_type: str = Field(
        ...,
        description=(
            "Inferred business category — e.g. 'local retail', 'B2B SaaS', "
            "'DTC e-commerce', 'professional services'"
        ),
    )
    goal_type: str = Field(
        ...,
        description=(
            "Normalized goal category — one of: conversion, awareness, "
            "lead-generation, retention, traffic, engagement"
        ),
    )
    audience_segment: str = Field(
        ...,
        description=(
            "Refined audience descriptor — more specific than the raw input. "
            "E.g. 'budget-conscious family shoppers' instead of 'normal people'"
        ),
    )
    audience_inference_confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description=(
            "How confident the interpreter is in the audience refinement (0–1). "
            "Low values signal the original input was very vague."
        ),
    )
    inferred_content_objective: str = Field(
        ...,
        description=(
            "One-sentence statement of what the content must accomplish — "
            "e.g. 'drive in-store purchases via limited-time promotions'"
        ),
    )
    candidate_angles: List[str] = Field(
        ...,
        min_length=3,
        max_length=5,
        description=(
            "3–5 possible content directions the agent considered. "
            "These feed into the candidate generator inside the decision stage."
        ),
    )
    reasoning_trace: str = Field(
        ...,
        description=(
            "Human-readable explanation of how the interpreter mapped the raw "
            "brief to structured variables — must mention any inferences made "
            "and why."
        ),
    )
