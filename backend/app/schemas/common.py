"""Shared input schema used by all agent endpoints."""

from pydantic import BaseModel, Field


class UserInput(BaseModel):
    """User-provided context for content strategy generation."""

    business_domain: str = Field(
        ...,
        min_length=2,
        max_length=200,
        description="The business domain or industry (e.g. 'SaaS fintech', 'fashion e-commerce')",
        examples=["SaaS fintech", "health & wellness"],
    )
    content_goal: str = Field(
        ...,
        min_length=5,
        max_length=500,
        description="What the user wants to achieve with their content",
        examples=["Increase brand awareness among Gen-Z", "Drive product launch engagement"],
    )
    target_audience: str = Field(
        ...,
        min_length=3,
        max_length=300,
        description="Description of the intended audience",
        examples=["Tech-savvy millennials aged 25-35", "Small business owners"],
    )
    tone: str = Field(
        default="professional",
        max_length=50,
        description="Desired tone for the content",
        examples=["professional", "casual", "witty", "inspirational"],
    )
