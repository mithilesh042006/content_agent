"""Tests for the Decision Service — outcome-driven, uncertainty, exploration."""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.schemas.common import UserInput
from app.schemas.interpretation import InterpretationResponse
from app.schemas.strategy_candidate import StrategyCandidate, CandidatePool
from app.schemas.simulation import CandidateSimulation, FormulaInputs
from app.services.decision_service import (
    run_decision, _classify_confidence, _should_explore, _assess_pool_quality,
)
from app.services.strategy_memory import StrategyMemory, StrategyRecord
from app.constants import MINIMUM_VIABLE_SCORE, EXPLORE_SWAP_THRESHOLD


def _make_user_input() -> UserInput:
    return UserInput(
        business_domain="Local grocery",
        content_goal="Drive sales",
        target_audience="Family shoppers",
        tone="casual",
    )


def _make_interpretation() -> InterpretationResponse:
    return InterpretationResponse(
        business_type="local retail",
        goal_type="conversion",
        audience_segment="budget-conscious family shoppers",
        audience_inference_confidence=0.85,
        inferred_content_objective="Drive in-store purchases",
        candidate_angles=["Weekly deals", "Seasonal promos", "Customer stories"],
        reasoning_trace="Test trace",
    )


def _make_formula_inputs(**overrides) -> FormulaInputs:
    defaults = dict(
        base_reach_ceiling=12000, reach_signal=6.0, engagement_signal=5.5,
        conversion_signal=5.0, format_synergy=1.25, goal_synergy=1.2,
        audience_synergy=1.15, platform_multiplier=1.0, format_multiplier=1.0,
        cta_multiplier=1.0, time_synergy_reach=1.15, time_synergy_engagement=1.25,
        time_learned_multiplier=1.0, feasibility=0.80, complexity_penalty=0.986,
        memory_boost=1.0, signal_consistency=0.88, consistency_multiplier=0.95,
        goal_weight_profile="conversion",
        outcome_weights={"conversion": 0.55, "reach": 0.15, "engagement": 0.10, "feasibility": 0.10, "confidence": 0.10},
    )
    defaults.update(overrides)
    return FormulaInputs(**defaults)


def _make_sim_result(cid: str, score: float, **overrides) -> CandidateSimulation:
    defaults = dict(
        candidate_id=cid, platform="Instagram", topic="Test", format="carousel",
        predicted_reach=5000, predicted_engagement=4.5, predicted_conversion=3.0,
        confidence=0.7, feasibility=0.8, complexity_penalty=0.986,
        outcome_score=score, formula_inputs=_make_formula_inputs(),
    )
    defaults.update(overrides)
    return CandidateSimulation(**defaults)


def _make_candidate(cid: str, **overrides) -> StrategyCandidate:
    defaults = dict(
        candidate_id=cid, platform="Instagram", topic="Test", format="carousel",
        posting_time="Mon–Fri 5–10 PM", time_window="weekday_evening",
        goal_type="conversion", audience_segment="family shoppers",
        business_type="local retail", audience_fit=7.0, goal_fit=7.0,
        format_fit=7.0, conversion_fit=7.0, tone_fit=6.0, timing_fit=7.0,
        feasibility=0.8,
    )
    defaults.update(overrides)
    return StrategyCandidate(**defaults)


class TestConfidenceClassification:
    """Test uncertainty detection and confidence scoring."""

    def test_small_gap_is_low_confidence(self):
        level, flag, score = _classify_confidence(7.5, 7.3, 0.7)
        assert level == "low"
        assert flag is True

    def test_medium_gap_is_medium(self):
        level, flag, score = _classify_confidence(7.5, 6.5, 0.7)
        assert level == "medium"
        assert flag is False

    def test_large_gap_is_high(self):
        level, flag, score = _classify_confidence(8.5, 5.0, 0.8)
        assert level == "high"
        assert flag is False

    def test_confidence_score_in_range(self):
        _, _, score = _classify_confidence(7.5, 7.3, 0.7)
        assert 0.0 <= score <= 1.0


class TestPoolQuality:
    """Test relative score assessment."""

    def test_low_quality_pool(self):
        ranked = [_make_sim_result("c1", 3.0), _make_sim_result("c2", 2.0)]
        rel, warning, reason = _assess_pool_quality(ranked)
        assert rel < 0.6
        assert warning is True
        assert len(reason) > 0

    def test_good_quality_pool(self):
        ranked = [_make_sim_result("c1", 7.5), _make_sim_result("c2", 6.0)]
        rel, warning, _ = _assess_pool_quality(ranked)
        assert rel >= 0.6
        assert warning is False

    def test_empty_pool(self):
        rel, warning, _ = _assess_pool_quality([])
        assert rel == 0.0
        assert warning is True


class TestNoViableStrategy:
    """Test the no-viable-strategy guard."""

    def test_below_threshold_returns_no_viable(self):
        sims = [_make_sim_result("c1", 3.0), _make_sim_result("c2", 2.5)]
        pool = CandidatePool(
            candidates=[_make_candidate("c1"), _make_candidate("c2")],
            generation_method="fallback",
        )
        result = run_decision(
            _make_user_input(), _make_interpretation(), sims, pool,
        )
        assert result.no_viable_strategy is True
        assert result.platform == "None"

    def test_above_threshold_returns_winner(self):
        sims = [_make_sim_result("c1", 7.5), _make_sim_result("c2", 6.0)]
        pool = CandidatePool(
            candidates=[_make_candidate("c1"), _make_candidate("c2")],
            generation_method="fallback",
        )
        result = run_decision(
            _make_user_input(), _make_interpretation(), sims, pool,
        )
        assert result.no_viable_strategy is False
        assert result.platform != "None"


class TestDecisionOutput:
    """Test the full decision response structure."""

    def test_winner_has_highest_score(self):
        sims = [
            _make_sim_result("c1", 8.0),
            _make_sim_result("c2", 6.5, platform="TikTok"),
            _make_sim_result("c3", 5.0, platform="LinkedIn"),
        ]
        pool = CandidatePool(
            candidates=[_make_candidate("c1"), _make_candidate("c2"), _make_candidate("c3")],
            generation_method="fallback",
        )
        result = run_decision(
            _make_user_input(), _make_interpretation(), sims, pool,
        )
        assert result.outcome_score == 8.0

    def test_rejected_alternatives_present(self):
        sims = [_make_sim_result("c1", 8.0), _make_sim_result("c2", 6.5)]
        pool = CandidatePool(
            candidates=[_make_candidate("c1"), _make_candidate("c2")],
            generation_method="fallback",
        )
        result = run_decision(
            _make_user_input(), _make_interpretation(), sims, pool,
        )
        assert len(result.rejected) >= 1

    def test_relative_score_computed(self):
        sims = [_make_sim_result("c1", 7.0)]
        pool = CandidatePool(
            candidates=[_make_candidate("c1")],
            generation_method="fallback",
        )
        result = run_decision(
            _make_user_input(), _make_interpretation(), sims, pool,
        )
        assert result.relative_score == 0.7
