"""Schema for the Content Generation agent endpoint."""

from pydantic import BaseModel, Field
from typing import List


class ContentResponse(BaseModel):
    """AI-generated content piece for the target platform."""

    headline: str = Field(
        ...,
        description="Attention-grabbing headline or hook",
    )
    post_copy: str = Field(
        ...,
        description="Full post body copy, formatted for the target platform",
    )
    cta: str = Field(
        ...,
        description="Call-to-action line",
    )
    hashtags: List[str] = Field(
        default_factory=list,
        description="Relevant hashtags (without leading #)",
    )
