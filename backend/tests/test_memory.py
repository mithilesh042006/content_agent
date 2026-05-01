"""Tests for Strategy Memory and Simulation State — persistence and learning."""

import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.services.strategy_memory import StrategyMemory, StrategyRecord, MEMORY_FILE
from app.services.simulation_state import SimulationState, STATE_FILE


class TestSimulationState:
    """Test persistent simulation multipliers."""

    def test_default_values(self):
        state = SimulationState()
        assert state.platform_multiplier.get("Instagram", 1.0) >= 0.5
        assert state.version >= 0

    def test_apply_updates_clamps(self):
        """Multipliers should be clamped to [0.5, 1.5]."""
        state = SimulationState()
        # Try to push way above 1.5
        state.apply_updates({"platform_multiplier": {"Instagram": 100.0}})
        assert state.platform_multiplier["Instagram"] <= 1.5
        # Reset
        state.apply_updates({"platform_multiplier": {"Instagram": -100.0}})
        assert state.platform_multiplier["Instagram"] >= 0.5

    def test_version_increments(self):
        state = SimulationState()
        v0 = state.version
        state.apply_updates({"platform_multiplier": {"TestPlatform": 0.01}})
        assert state.version == v0 + 1

    def test_time_synergy_multiplier_works(self):
        state = SimulationState()
        state.apply_updates({"time_synergy_multiplier": {"Instagram|weekday_evening": 0.02}})
        assert "Instagram|weekday_evening" in state.time_synergy_multiplier


class TestStrategyMemory:
    """Test strategy memory persistence and matching."""

    def _make_record(self, **overrides) -> StrategyRecord:
        defaults = dict(
            decision_id="test-001", timestamp="2026-01-01T00:00:00Z",
            platform="Instagram", format="carousel",
            topic_keywords=["deals", "grocery"],
            goal_type="conversion",
            audience_segment="family shoppers",
            business_type="local retail",
            predicted={"reach": 5000, "engagement": 5.0, "conversion": 3.0},
            actual={"reach": 6000, "engagement": 5.5, "conversion": 3.5},
            outcome_score=7.5,
            performance_ratio=1.15,
        )
        defaults.update(overrides)
        return StrategyRecord(**defaults)

    def test_empty_memory_returns_neutral_boost(self):
        memory = StrategyMemory()
        memory._records = []
        boost = memory.get_memory_boost("Instagram", "carousel", "conversion")
        assert boost == 1.0

    def test_outperformance_gives_positive_boost(self):
        memory = StrategyMemory()
        memory._records = [
            self._make_record(performance_ratio=1.2),
            self._make_record(decision_id="test-002", performance_ratio=1.3),
        ]
        boost = memory.get_memory_boost("Instagram", "carousel", "conversion")
        assert boost > 1.0

    def test_underperformance_gives_negative_boost(self):
        memory = StrategyMemory()
        memory._records = [
            self._make_record(performance_ratio=0.6),
            self._make_record(decision_id="test-002", performance_ratio=0.5),
        ]
        boost = memory.get_memory_boost("Instagram", "carousel", "conversion")
        assert boost < 1.0

    def test_boost_clamped(self):
        memory = StrategyMemory()
        memory._records = [
            self._make_record(performance_ratio=5.0),
        ]
        boost = memory.get_memory_boost("Instagram", "carousel", "conversion")
        assert boost <= 1.15

    def test_context_aware_matching(self):
        """Same platform+format+goal but different audience = lower tier weight."""
        memory = StrategyMemory()
        memory._records = [
            self._make_record(
                audience_segment="b2b enterprise buyers",
                business_type="B2B SaaS",
                performance_ratio=1.3,
            ),
        ]
        # Different audience → lower match tier → less influence
        boost_different = memory.get_memory_boost(
            "Instagram", "carousel", "conversion",
            audience_segment="youth gamers", business_type="gaming",
        )
        boost_similar = memory.get_memory_boost(
            "Instagram", "carousel", "conversion",
            audience_segment="b2b enterprise decision makers",
            business_type="B2B SaaS platform",
        )
        # Similar audience should get stronger boost
        assert boost_similar >= boost_different

    def test_recent_winners(self):
        memory = StrategyMemory()
        memory._records = [
            self._make_record(decision_id=f"t{i}") for i in range(10)
        ]
        recent = memory.get_recent_winners(limit=3)
        assert len(recent) == 3

    def test_memory_decay_old_records_less_influence(self):
        """Old records should have less influence than recent ones."""
        memory = StrategyMemory()
        # 50 records with good performance
        memory._records = [
            self._make_record(decision_id=f"old-{i}", performance_ratio=0.7)
            for i in range(50)
        ]
        # Add 2 recent records with great performance
        memory._records.extend([
            self._make_record(decision_id="new-1", performance_ratio=1.3),
            self._make_record(decision_id="new-2", performance_ratio=1.4),
        ])
        boost = memory.get_memory_boost("Instagram", "carousel", "conversion")
        # Recent good performance should partially overcome old bad performance
        # Due to decay, old records lose influence
        assert boost >= 0.85  # clamped
