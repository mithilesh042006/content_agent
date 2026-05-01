"""Tests for the Brief Interpretation service (unit tests — no HTTP)."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.schemas.common import UserInput
from app.services.interpretation_service import run_interpretation


def _make_input(**overrides) -> UserInput:
    defaults = dict(
        business_domain="SaaS fintech",
        content_goal="Increase brand awareness among tech professionals",
        target_audience="Tech-savvy millennials aged 25-35",
        tone="professional",
    )
    defaults.update(overrides)
    return UserInput(**defaults)


def test_interpret_response_shape():
    result = run_interpretation(_make_input())
    assert result.business_type != ""
    assert result.goal_type != ""
    assert result.audience_segment != ""
    assert result.inferred_content_objective != ""
    assert len(result.candidate_angles) >= 3
    assert result.reasoning_trace != ""


def test_interpret_goal_type_is_valid():
    result = run_interpretation(_make_input())
    valid = {"conversion", "awareness", "lead-generation", "retention", "traffic", "engagement"}
    assert result.goal_type in valid


def test_interpret_candidate_angles_count():
    result = run_interpretation(_make_input())
    assert 3 <= len(result.candidate_angles) <= 5


def test_interpret_confidence_in_range():
    result = run_interpretation(_make_input())
    assert 0.0 <= result.audience_inference_confidence <= 1.0


def test_interpret_vague_audience_refinement():
    result = run_interpretation(_make_input(
        business_domain="grocery shop",
        content_goal="increase sales and customers",
        target_audience="normal people",
    ))
    assert result.audience_segment != "normal people"
    assert len(result.audience_segment) > len("normal people")


def test_interpret_saas_domain():
    result = run_interpretation(_make_input(
        business_domain="B2B SaaS platform",
        content_goal="generate leads from enterprise buyers",
        target_audience="CTOs and engineering managers",
    ))
    assert "saas" in result.business_type.lower() or "b2b" in result.business_type.lower()


def test_interpret_healthcare_domain():
    result = run_interpretation(_make_input(
        business_domain="telehealth clinic",
        content_goal="increase patient bookings",
        target_audience="busy parents",
    ))
    assert "health" in result.business_type.lower()


def test_interpret_conversion_goal():
    result = run_interpretation(_make_input(
        business_domain="online store",
        content_goal="increase sales and revenue",
        target_audience="shoppers aged 25-40",
    ))
    assert result.goal_type == "conversion"


def test_interpret_lead_gen_goal():
    result = run_interpretation(_make_input(
        business_domain="SaaS startup",
        content_goal="drive signups for our free trial",
        target_audience="startup founders",
    ))
    assert result.goal_type == "lead-generation"
