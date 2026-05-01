"""Explainer Service — post-decision LLM narrative.

The explainer receives a pre-computed decision and generates human-readable
rationale. It does NOT influence the decision. If the LLM is unavailable,
a template-based fallback is used.
"""

import logging

from app.schemas.interpretation import InterpretationResponse
from app.schemas.simulation import CandidateSimulation
from app.schemas.decision import DecisionResponse, RejectedAlternative
from app.schemas.explanation import ExplanationResponse
from app.prompts.explainer_prompt import EXPLAINER_SYSTEM_PROMPT, build_explainer_user_prompt
from app.services.llm_service import invoke_structured

logger = logging.getLogger(__name__)


def _fallback_explanation(
    decision: DecisionResponse,
    winner: CandidateSimulation,
    runner_up: CandidateSimulation | None,
) -> ExplanationResponse:
    """Template-based explanation when LLM is unavailable."""
    if runner_up:
        reason = (
            f"{winner.platform} ({winner.format}) selected with outcome score "
            f"{winner.outcome_score:.2f}, beating {runner_up.platform} "
            f"({runner_up.format}) at {runner_up.outcome_score:.2f}. "
            f"Conversion: {winner.predicted_conversion:.1f}% vs "
            f"{runner_up.predicted_conversion:.1f}%. "
            f"Reach: {winner.predicted_reach:,} vs {runner_up.predicted_reach:,}."
        )
        chosen_because = (
            f"{winner.platform} maximizes the {decision.interpretation_used.split('|')[1].strip()} "
            f"objective with {winner.predicted_conversion:.1f}% conversion and "
            f"{winner.predicted_reach:,} predicted reach."
        )
    else:
        reason = (
            f"{winner.platform} ({winner.format}) is the strongest candidate "
            f"with outcome score {winner.outcome_score:.2f}."
        )
        chosen_because = f"{winner.platform} is the optimal platform for this brief."

    trade_off_narrative = ""
    if decision.trade_off_analysis:
        ta = decision.trade_off_analysis
        trade_off_narrative = (
            f"Trade-off: {ta.candidate_a} leads on {ta.candidate_a_strength} "
            f"while {ta.candidate_b} leads on {ta.candidate_b_strength}. "
            f"Gap: {ta.delta:.2f}. {ta.decision_rationale}"
        )

    rejection_narrative = ""
    if decision.rejected:
        top3 = decision.rejected[:3]
        parts = [f"{r.platform} ({r.format}): {r.reason}" for r in top3]
        rejection_narrative = "Rejected: " + " | ".join(parts)

    return ExplanationResponse(
        reason=reason,
        chosen_because=chosen_because,
        trade_off_narrative=trade_off_narrative,
        rejection_narratives=rejection_narrative,
    )


def run_explanation(
    decision: DecisionResponse,
    winner: CandidateSimulation,
    runner_up: CandidateSimulation | None,
    interpretation: InterpretationResponse,
) -> ExplanationResponse:
    """Generate explanation for the computed decision."""
    user_prompt = build_explainer_user_prompt(
        decision=decision,
        winner=winner,
        runner_up=runner_up,
        interpretation=interpretation,
    )

    result = invoke_structured(
        system_prompt=EXPLAINER_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        schema=ExplanationResponse,
    )

    if result is not None:
        return result

    logger.info("Using fallback explanation")
    return _fallback_explanation(decision, winner, runner_up)
