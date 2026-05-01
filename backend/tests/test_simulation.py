"""Tests for the Simulation Engine — non-linear, interaction-aware simulation."""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.constants import saturate, compute_complexity_penalty
from app.schemas.strategy_candidate import StrategyCandidate
from app.services.simulation_service import simulate_candidate, simulate_all, _compute_confidence
from app.services.simulation_state import SimulationState


def _make_candidate(**overrides) -> StrategyCandidate:
    """Helper to create a test candidate."""
    defaults = dict(
        candidate_id="test-candidate-1",
        platform="Instagram",
        topic="Weekly deals for families",
        format="carousel",
        posting_time="Mon–Fri 5–10 PM",
        time_window="weekday_evening",
        goal_type="conversion",
        audience_segment="budget-conscious family shoppers",
        business_type="local retail",
        audience_fit=7.5,
        goal_fit=7.0,
        format_fit=8.0,
        conversion_fit=6.5,
        tone_fit=6.0,
        timing_fit=7.0,
        feasibility=0.80,
    )
    defaults.update(overrides)
    return StrategyCandidate(**defaults)


class TestSaturation:
    """Test the saturate() function for diminishing returns."""

    def test_never_reaches_ceiling(self):
        assert saturate(10.0, 10000) < 10000

    def test_zero_gives_zero(self):
        assert saturate(0.0, 10000) == 0.0

    def test_diminishing_returns(self):
        """Going from 8→10 should gain less than going from 2→4."""
        gain_low = saturate(4.0, 10000) - saturate(2.0, 10000)
        gain_high = saturate(10.0, 10000) - saturate(8.0, 10000)
        assert gain_low > gain_high

    def test_positive_for_positive_input(self):
        assert saturate(1.0, 10000) > 0

    def test_steepness_matters(self):
        """Higher steepness = faster growth at low values."""
        slow = saturate(3.0, 10000, steepness=0.15)
        fast = saturate(3.0, 10000, steepness=0.35)
        assert fast > slow


class TestComplexityPenalty:
    """Test FORMAT_COMPLEXITY penalty."""

    def test_static_image_negligible(self):
        assert compute_complexity_penalty("static image") > 0.99

    def test_live_stream_meaningful(self):
        assert compute_complexity_penalty("live stream") < 0.96

    def test_clamped_above_092(self):
        assert compute_complexity_penalty("live stream") >= 0.92

    def test_carousel_between(self):
        p = compute_complexity_penalty("carousel")
        assert 0.92 <= p <= 0.99


class TestConfidence:
    """Test the enhanced confidence model with consistency."""

    def test_uniform_high_signals(self):
        """Uniform high signals → high confidence."""
        conf, _, _ = _compute_confidence([8, 8, 7, 8, 7, 8])
        assert conf > 0.60

    def test_conflicting_signals_low_confidence(self):
        """Conflicting signals → low confidence."""
        conf, _, _ = _compute_confidence([9, 2, 8, 3, 7, 2])
        assert conf < 0.40

    def test_consistency_detects_conflict(self):
        """Consistency ratio should be low when signals disagree."""
        _, consistency, _ = _compute_confidence([9, 2, 8, 3, 7, 2])
        assert consistency < 0.30

    def test_uniform_signals_high_consistency(self):
        """Uniform signals → high consistency."""
        _, consistency, _ = _compute_confidence([5, 5, 5, 5, 5, 5])
        assert consistency == 1.0


class TestSimulateCandidate:
    """Test individual candidate simulation."""

    def test_produces_result(self):
        c = _make_candidate()
        result = simulate_candidate(c)
        assert result.outcome_score > 0
        assert result.predicted_reach > 0
        assert result.predicted_engagement > 0

    def test_formula_inputs_populated(self):
        c = _make_candidate()
        result = simulate_candidate(c)
        fi = result.formula_inputs
        assert fi.format_synergy > 0
        assert fi.goal_weight_profile != ""
        assert len(fi.outcome_weights) == 5

    def test_instagram_carousel_synergy(self):
        """Instagram + carousel should show format synergy > 1.0."""
        c = _make_candidate(platform="Instagram", format="carousel")
        result = simulate_candidate(c)
        assert result.formula_inputs.format_synergy > 1.0

    def test_tiktok_static_friction(self):
        """TikTok + static image should show format synergy < 1.0."""
        c = _make_candidate(platform="TikTok", format="static image")
        result = simulate_candidate(c)
        assert result.formula_inputs.format_synergy < 1.0

    def test_time_synergy_applied(self):
        """Verify time synergy enters formula inputs."""
        c = _make_candidate(time_window="weekday_evening")
        result = simulate_candidate(c)
        assert result.formula_inputs.time_synergy_reach > 0

    def test_feasibility_from_format(self):
        """Carousel should be less feasible than static image."""
        c_carousel = _make_candidate(format="carousel")
        c_static = _make_candidate(format="static image")
        r_carousel = simulate_candidate(c_carousel)
        r_static = simulate_candidate(c_static)
        assert r_static.feasibility > r_carousel.feasibility


class TestSimulateAll:
    """Test bulk simulation and ranking."""

    def test_sorted_by_outcome_score(self):
        candidates = [
            _make_candidate(candidate_id="c1", platform="Instagram", format="carousel"),
            _make_candidate(candidate_id="c2", platform="TikTok", format="short-form video"),
            _make_candidate(candidate_id="c3", platform="LinkedIn", format="long-form text"),
        ]
        result = simulate_all(candidates)
        scores = [c.outcome_score for c in result.all_candidates]
        assert scores == sorted(scores, reverse=True)

    def test_winner_has_highest_score(self):
        candidates = [
            _make_candidate(candidate_id="c1", platform="Instagram", format="carousel"),
            _make_candidate(candidate_id="c2", platform="TikTok", format="short-form video"),
        ]
        result = simulate_all(candidates)
        assert result.winner.outcome_score >= result.all_candidates[-1].outcome_score

    def test_runner_up_exists(self):
        candidates = [
            _make_candidate(candidate_id="c1"),
            _make_candidate(candidate_id="c2", platform="LinkedIn"),
        ]
        result = simulate_all(candidates)
        assert result.runner_up is not None

    def test_comparison_summary_present(self):
        candidates = [
            _make_candidate(candidate_id="c1"),
            _make_candidate(candidate_id="c2", platform="TikTok", format="short-form video"),
        ]
        result = simulate_all(candidates)
        assert len(result.comparison_summary) > 10


class TestGoalAdaptiveWeights:
    """Test that goal_type changes outcome_score weights."""

    def test_conversion_goal_favors_conversion(self):
        c = _make_candidate(goal_type="conversion")
        result = simulate_candidate(c)
        assert result.formula_inputs.outcome_weights["conversion"] == 0.55

    def test_awareness_goal_favors_reach(self):
        c = _make_candidate(goal_type="awareness")
        result = simulate_candidate(c)
        assert result.formula_inputs.outcome_weights["reach"] == 0.45
