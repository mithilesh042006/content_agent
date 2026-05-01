"""Tests for candidate generation service."""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.schemas.common import UserInput
from app.schemas.interpretation import InterpretationResponse
from app.services.candidate_service import (
    generate_candidates, _apply_hard_constraints,
    _audience_fit_score, _goal_fit_score, _format_fit_score,
)


def _make_user_input(**overrides) -> UserInput:
    defaults = dict(
        business_domain="Local grocery store",
        content_goal="Drive weekly sales",
        target_audience="Family shoppers",
        tone="casual",
    )
    defaults.update(overrides)
    return UserInput(**defaults)


def _make_interpretation(**overrides) -> InterpretationResponse:
    defaults = dict(
        business_type="local retail",
        goal_type="conversion",
        audience_segment="budget-conscious family shoppers",
        audience_inference_confidence=0.8,
        inferred_content_objective="Drive in-store purchases",
        candidate_angles=[
            "Weekly deals spotlight",
            "Seasonal recipe ideas",
            "Customer savings stories",
        ],
        reasoning_trace="Test trace",
    )
    defaults.update(overrides)
    return InterpretationResponse(**defaults)


class TestHardConstraints:
    """Test platform filtering by audience."""

    def test_b2b_excludes_tiktok(self):
        result = _apply_hard_constraints(
            ["Instagram", "TikTok", "LinkedIn", "Facebook"],
            "b2b decision makers", "B2B SaaS",
        )
        assert "TikTok" not in result
        assert "LinkedIn" in result

    def test_youth_keeps_tiktok(self):
        result = _apply_hard_constraints(
            ["Instagram", "TikTok", "LinkedIn"],
            "youth aged 18-25", "general business",
        )
        assert "TikTok" in result

    def test_never_returns_empty(self):
        result = _apply_hard_constraints(
            ["TikTok"], "b2b enterprise", "B2B SaaS",
        )
        assert len(result) > 0


class TestSignalScoring:
    """Test individual signal score computations."""

    def test_audience_fit_b2b_linkedin_high(self):
        score = _audience_fit_score("b2b decision makers", "LinkedIn")
        assert score >= 6.0

    def test_audience_fit_b2b_tiktok_low(self):
        score = _audience_fit_score("b2b decision makers", "TikTok")
        assert score < 5.0

    def test_goal_fit_conversion_instagram(self):
        score = _goal_fit_score("conversion", "Instagram")
        assert score >= 5.5

    def test_format_fit_carousel_instagram(self):
        score = _format_fit_score("Instagram", "carousel")
        assert score > _format_fit_score("Instagram", "static image")


class TestCandidateGeneration:
    """Test the full candidate generation pipeline."""

    def test_generates_candidates(self):
        pool = generate_candidates(_make_user_input(), _make_interpretation())
        assert len(pool.candidates) >= 1

    def test_candidates_have_required_fields(self):
        pool = generate_candidates(_make_user_input(), _make_interpretation())
        c = pool.candidates[0]
        assert c.candidate_id != ""
        assert c.platform != ""
        assert c.format != ""
        assert c.time_window != ""
        assert c.goal_type == "conversion"
        assert c.feasibility > 0

    def test_max_15_candidates(self):
        pool = generate_candidates(_make_user_input(), _make_interpretation())
        assert len(pool.candidates) <= 15

    def test_signal_scores_in_range(self):
        pool = generate_candidates(_make_user_input(), _make_interpretation())
        for c in pool.candidates:
            assert 0 <= c.audience_fit <= 10
            assert 0 <= c.goal_fit <= 10
            assert 0 <= c.format_fit <= 10
            assert 0 <= c.conversion_fit <= 10
            assert 0 <= c.tone_fit <= 10
            assert 0 <= c.timing_fit <= 10

    def test_diverse_platforms(self):
        pool = generate_candidates(_make_user_input(), _make_interpretation())
        platforms = {c.platform for c in pool.candidates}
        assert len(platforms) >= 2

    def test_b2b_filters_tiktok(self):
        interp = _make_interpretation(
            audience_segment="b2b enterprise buyers",
            business_type="B2B SaaS",
        )
        pool = generate_candidates(_make_user_input(), interp)
        platforms = {c.platform for c in pool.candidates}
        assert "TikTok" not in platforms
