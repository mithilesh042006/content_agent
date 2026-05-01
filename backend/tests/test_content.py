"""Tests for the Content Generation service (unit tests — no HTTP)."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.schemas.common import UserInput
from app.schemas.interpretation import InterpretationResponse
from app.services.content_service import run_content


def _make_input() -> UserInput:
    return UserInput(
        business_domain="SaaS fintech",
        content_goal="Increase brand awareness among tech professionals",
        target_audience="Tech-savvy millennials aged 25-35",
        tone="professional",
    )


def _make_interp() -> InterpretationResponse:
    return InterpretationResponse(
        business_type="finance",
        goal_type="awareness",
        audience_segment="tech-savvy professionals aged 25-35",
        audience_inference_confidence=0.85,
        inferred_content_objective="Increase fintech visibility",
        candidate_angles=["Fintech trends", "API innovations", "Banking disruption"],
        reasoning_trace="Test trace",
    )


def test_generate_response_shape():
    result = run_content(_make_input(), "Fintech APIs", "LinkedIn", _make_interp())
    assert result.headline != ""
    assert result.post_copy != ""
    assert result.cta != ""
    assert isinstance(result.hashtags, list)


def test_generate_headline_not_empty():
    result = run_content(_make_input(), "Fintech APIs", "LinkedIn", _make_interp())
    assert len(result.headline) > 0


def test_generate_hashtags_is_list():
    result = run_content(_make_input(), "Fintech APIs", "LinkedIn", _make_interp())
    assert isinstance(result.hashtags, list)
    assert len(result.hashtags) > 0


def test_generate_post_copy_contains_domain():
    result = run_content(_make_input(), "Fintech APIs", "LinkedIn", _make_interp())
    assert "fintech" in result.post_copy.lower() or "saas" in result.post_copy.lower()
