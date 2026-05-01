"""Tests for the Feedback service — delta computation, state updates, memory."""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.services.feedback_service import (
    _compute_simulation_updates, _compute_perf_ratio, run_feedback,
)
from app.schemas.feedback import FeedbackRequest


class TestSimulationUpdates:
    """Test simulation parameter delta computation."""

    def test_reach_underperformance_adjusts_platform(self):
        updates = _compute_simulation_updates(
            predicted={"reach": 10000, "engagement": 5.0, "conversion": 3.0},
            actual={"reach": 5000, "engagement": 5.0, "conversion": 3.0},
            platform="Instagram", fmt="carousel",
            goal_type="conversion", time_window="weekday_evening",
        )
        assert "platform_multiplier" in updates
        assert updates["platform_multiplier"]["Instagram"] < 0

    def test_reach_overperformance_boosts_platform(self):
        updates = _compute_simulation_updates(
            predicted={"reach": 5000, "engagement": 5.0, "conversion": 3.0},
            actual={"reach": 10000, "engagement": 5.0, "conversion": 3.0},
            platform="Instagram", fmt="carousel",
            goal_type="conversion", time_window="weekday_evening",
        )
        assert "platform_multiplier" in updates
        assert updates["platform_multiplier"]["Instagram"] > 0

    def test_engagement_underperformance_adjusts_format(self):
        updates = _compute_simulation_updates(
            predicted={"reach": 5000, "engagement": 10.0, "conversion": 3.0},
            actual={"reach": 5000, "engagement": 5.0, "conversion": 3.0},
            platform="Instagram", fmt="carousel",
            goal_type="conversion", time_window="",
        )
        assert "format_multiplier" in updates
        assert updates["format_multiplier"]["carousel"] < 0

    def test_conversion_underperformance_adjusts_cta(self):
        updates = _compute_simulation_updates(
            predicted={"reach": 5000, "engagement": 5.0, "conversion": 10.0},
            actual={"reach": 5000, "engagement": 5.0, "conversion": 5.0},
            platform="Instagram", fmt="carousel",
            goal_type="conversion", time_window="",
        )
        assert "cta_multiplier" in updates
        assert updates["cta_multiplier"]["conversion"] < 0

    def test_no_updates_when_within_range(self):
        updates = _compute_simulation_updates(
            predicted={"reach": 5000, "engagement": 5.0, "conversion": 3.0},
            actual={"reach": 5500, "engagement": 5.2, "conversion": 3.1},
            platform="Instagram", fmt="carousel",
            goal_type="conversion", time_window="",
        )
        assert len(updates) == 0

    def test_time_synergy_learning(self):
        updates = _compute_simulation_updates(
            predicted={"reach": 5000, "engagement": 5.0, "conversion": 3.0},
            actual={"reach": 2000, "engagement": 2.0, "conversion": 3.0},
            platform="Instagram", fmt="carousel",
            goal_type="conversion", time_window="weekday_evening",
        )
        assert "time_synergy_multiplier" in updates
        time_key = "Instagram|weekday_evening"
        assert updates["time_synergy_multiplier"][time_key] < 0


class TestPerfRatio:
    """Test composite performance ratio."""

    def test_perfect_match_is_1(self):
        ratio = _compute_perf_ratio(
            {"reach": 5000, "engagement": 5.0, "conversion": 3.0},
            {"reach": 5000, "engagement": 5.0, "conversion": 3.0},
        )
        assert ratio == 1.0

    def test_overperformance_above_1(self):
        ratio = _compute_perf_ratio(
            {"reach": 5000, "engagement": 5.0, "conversion": 3.0},
            {"reach": 7000, "engagement": 7.0, "conversion": 4.0},
        )
        assert ratio > 1.0


class TestRunFeedback:
    """Test the full feedback execution."""

    def test_produces_response(self):
        request = FeedbackRequest(
            business_domain="Local grocery",
            content_goal="Drive sales",
            target_audience="Family shoppers",
            topic="Weekly deals",
            platform="Instagram",
            format="carousel",
            predicted_reach=5000,
            predicted_engagement=5.0,
            predicted_conversion=3.0,
            headline="Test headline",
            goal_type="conversion",
            time_window="weekday_evening",
        )
        result = run_feedback(request)
        assert result.actual_reach > 0
        assert "reach" in result.predicted
        assert "reach" in result.actual
        assert "reach" in result.delta
        assert result.state_version >= 0

    def test_with_actual_metrics(self):
        request = FeedbackRequest(
            business_domain="Local grocery",
            content_goal="Drive sales",
            target_audience="Family shoppers",
            topic="Weekly deals",
            platform="Instagram",
            format="carousel",
            predicted_reach=5000,
            predicted_engagement=5.0,
            predicted_conversion=3.0,
            headline="Test headline",
            actual_reach=6000,
            actual_engagement=5.5,
            actual_conversion=3.5,
        )
        result = run_feedback(request)
        assert result.actual_reach == 6000
        assert result.actual_engagement == 5.5
