"""Tests for the full v3 pipeline — end-to-end validation."""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.schemas.common import UserInput
from app.services.interpretation_service import run_interpretation
from app.services.candidate_service import generate_candidates
from app.services.simulation_service import simulate_all
from app.services.decision_service import run_decision


def _make_user_input(**overrides) -> UserInput:
    defaults = dict(
        business_domain="Local coffee shop",
        content_goal="Drive foot traffic and repeat visits",
        target_audience="Young professionals aged 25-35",
        tone="casual",
    )
    defaults.update(overrides)
    return UserInput(**defaults)


class TestPipelineShape:
    """Test that the full pipeline produces valid outputs."""

    def test_full_pipeline_runs(self):
        user_input = _make_user_input()
        interp = run_interpretation(user_input)
        pool = generate_candidates(user_input, interp)
        sim = simulate_all(pool.candidates)
        decision = run_decision(user_input, interp, sim.all_candidates, pool)

        assert interp.goal_type != ""
        assert len(pool.candidates) >= 1
        assert len(sim.all_candidates) >= 1
        assert decision.outcome_score >= 0

    def test_winner_has_highest_outcome_score(self):
        """INVARIANT: winner must have highest outcome_score."""
        user_input = _make_user_input()
        interp = run_interpretation(user_input)
        pool = generate_candidates(user_input, interp)
        sim = simulate_all(pool.candidates)

        # Check simulation winner
        for c in sim.all_candidates:
            assert sim.winner.outcome_score >= c.outcome_score

    def test_pipeline_deterministic(self):
        """Same input = same deterministic computation (no randomness in sim/decision)."""
        user_input = _make_user_input()
        interp = run_interpretation(user_input)
        pool = generate_candidates(user_input, interp)

        sim1 = simulate_all(pool.candidates)
        sim2 = simulate_all(pool.candidates)

        assert sim1.winner.outcome_score == sim2.winner.outcome_score
        assert sim1.winner.predicted_reach == sim2.winner.predicted_reach

    def test_multi_domain_generality(self):
        """Pipeline works for different business domains."""
        domains = [
            ("B2B SaaS platform", "Generate qualified leads", "CTOs and VPs of Engineering"),
            ("Fashion e-commerce", "Increase brand awareness among Gen-Z", "Gen-Z fashion shoppers"),
            ("Local dental clinic", "Book more appointments", "Families in the area"),
        ]
        for biz, goal, audience in domains:
            user_input = _make_user_input(
                business_domain=biz, content_goal=goal, target_audience=audience,
            )
            interp = run_interpretation(user_input)
            pool = generate_candidates(user_input, interp)
            sim = simulate_all(pool.candidates)
            decision = run_decision(user_input, interp, sim.all_candidates, pool)

            assert decision.outcome_score >= 0
            assert decision.platform != ""

    def test_formula_inputs_traceable(self):
        """Every simulation result has populated formula_inputs."""
        user_input = _make_user_input()
        interp = run_interpretation(user_input)
        pool = generate_candidates(user_input, interp)
        sim = simulate_all(pool.candidates)

        for c in sim.all_candidates:
            fi = c.formula_inputs
            assert fi.base_reach_ceiling > 0
            assert fi.goal_weight_profile != ""
            assert len(fi.outcome_weights) == 5
            assert fi.format_synergy > 0
            assert fi.complexity_penalty >= 0.92

    def test_decision_has_rejected_alternatives(self):
        user_input = _make_user_input()
        interp = run_interpretation(user_input)
        pool = generate_candidates(user_input, interp)
        sim = simulate_all(pool.candidates)
        decision = run_decision(user_input, interp, sim.all_candidates, pool)

        if not decision.no_viable_strategy and len(sim.all_candidates) > 1:
            assert len(decision.rejected) >= 1

    def test_reasoning_chain_can_be_built(self):
        """The pipeline produces enough data to build a reasoning chain."""
        user_input = _make_user_input()
        interp = run_interpretation(user_input)
        pool = generate_candidates(user_input, interp)
        sim = simulate_all(pool.candidates)
        decision = run_decision(user_input, interp, sim.all_candidates, pool)

        chain = [
            f"[Interpret] {interp.business_type}",
            f"[Candidates] {len(pool.candidates)} generated",
            f"[Simulate] Winner: {sim.winner.platform}",
            f"[Decide] {decision.platform} score={decision.outcome_score:.2f}",
        ]
        assert len(chain) == 4
        assert all(len(step) > 5 for step in chain)
