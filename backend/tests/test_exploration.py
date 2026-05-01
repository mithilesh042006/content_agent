"""Tests for exploration logic — stagnation detection and swap."""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.schemas.simulation import CandidateSimulation, FormulaInputs
from app.services.decision_service import _should_explore
from app.services.strategy_memory import StrategyMemory, StrategyRecord
from app.constants import EXPLORE_THRESHOLD, EXPLORE_SWAP_THRESHOLD


def _make_formula_inputs() -> FormulaInputs:
    return FormulaInputs(
        base_reach_ceiling=12000, reach_signal=6.0, engagement_signal=5.5,
        conversion_signal=5.0, format_synergy=1.25, goal_synergy=1.2,
        audience_synergy=1.15, platform_multiplier=1.0, format_multiplier=1.0,
        cta_multiplier=1.0, time_synergy_reach=1.15, time_synergy_engagement=1.25,
        time_learned_multiplier=1.0, feasibility=0.80, complexity_penalty=0.986,
        memory_boost=1.0, signal_consistency=0.88, consistency_multiplier=0.95,
        goal_weight_profile="conversion",
        outcome_weights={"conversion": 0.55, "reach": 0.15, "engagement": 0.10, "feasibility": 0.10, "confidence": 0.10},
    )


def _make_sim(cid: str, score: float, platform: str = "Instagram", fmt: str = "carousel") -> CandidateSimulation:
    return CandidateSimulation(
        candidate_id=cid, platform=platform, topic="Test", format=fmt,
        predicted_reach=5000, predicted_engagement=4.5, predicted_conversion=3.0,
        confidence=0.7, feasibility=0.8, complexity_penalty=0.986,
        outcome_score=score, formula_inputs=_make_formula_inputs(),
    )


def _make_record(platform: str = "Instagram", fmt: str = "carousel") -> StrategyRecord:
    return StrategyRecord(
        decision_id="test", timestamp="2026-01-01T00:00:00Z",
        platform=platform, format=fmt, goal_type="conversion",
        predicted={"reach": 5000, "engagement": 5.0, "conversion": 3.0},
        actual={"reach": 5000, "engagement": 5.0, "conversion": 3.0},
        outcome_score=7.0, performance_ratio=1.0,
    )


class TestExploration:
    """Test exploration trigger logic."""

    def test_no_exploration_without_uncertainty(self):
        winner = _make_sim("c1", 8.0)
        runner = _make_sim("c2", 7.9, platform="TikTok")
        memory = StrategyMemory()
        memory._records = []
        triggered, _ = _should_explore(winner, runner, False, memory)
        assert triggered is False

    def test_no_exploration_large_gap(self):
        winner = _make_sim("c1", 8.0)
        runner = _make_sim("c2", 6.0, platform="TikTok")
        memory = StrategyMemory()
        memory._records = []
        triggered, _ = _should_explore(winner, runner, True, memory)
        assert triggered is False

    def test_exploration_small_gap_with_uncertainty(self):
        winner = _make_sim("c1", 7.5)
        runner = _make_sim("c2", 7.4, platform="TikTok")
        memory = StrategyMemory()
        memory._records = []
        triggered, reason = _should_explore(winner, runner, True, memory)
        assert triggered is True
        assert "equivalent" in reason.lower() or "gap" in reason.lower()

    def test_stagnation_triggers_exploration(self):
        """3+ consecutive wins by same combo → exploration triggered."""
        winner = _make_sim("c1", 7.5)
        runner = _make_sim("c2", 7.2, platform="TikTok", fmt="short-form video")
        memory = StrategyMemory()
        # 3 recent wins by Instagram+carousel
        memory._records = [_make_record() for _ in range(3)]
        triggered, reason = _should_explore(winner, runner, True, memory)
        assert triggered is True
        assert "consecutive" in reason.lower() or "exploration" in reason.lower()

    def test_exploration_reason_has_content(self):
        winner = _make_sim("c1", 7.0)
        runner = _make_sim("c2", 6.95, platform="LinkedIn")
        memory = StrategyMemory()
        memory._records = []
        triggered, reason = _should_explore(winner, runner, True, memory)
        assert triggered is True
        assert len(reason) > 10
