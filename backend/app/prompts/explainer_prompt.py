"""Prompt for the Explainer agent — post-decision LLM narrative."""

from app.schemas.simulation import CandidateSimulation
from app.schemas.decision import DecisionResponse
from app.schemas.interpretation import InterpretationResponse

EXPLAINER_SYSTEM_PROMPT = """\
You are a strategy analyst providing rationale for an AI decision engine's output.

## RULES
1. The decision has ALREADY been made — you are explaining it, not choosing.
2. Reference specific numbers: outcome_score, predicted_conversion, predicted_reach.
3. When uncertainty_flag is True, explicitly address the trade-off.
4. Be concise: 2–3 sentences for reason, 1 sentence for chosen_because.
5. If exploration was triggered, mention why testing the alternative is valuable.

## OUTPUT CONTRACT
Return JSON with:
- reason: 2–3 sentence rationale referencing the outcome gap and key metrics
- chosen_because: 1-sentence summary of why the winner won
- trade_off_narrative: human-readable trade-off (empty if no uncertainty)
- rejection_narratives: brief explanation of why top alternatives lost
"""


def build_explainer_user_prompt(
    decision: DecisionResponse,
    winner: CandidateSimulation,
    runner_up: CandidateSimulation | None,
    interpretation: InterpretationResponse,
) -> str:
    """Build the user message for the explainer agent."""
    lines = [
        f"Business type: {interpretation.business_type}",
        f"Goal type: {interpretation.goal_type}",
        f"Audience: {interpretation.audience_segment}",
        "",
        f"WINNER: {winner.platform} + {winner.format}",
        f"  Topic: {winner.topic}",
        f"  Outcome score: {winner.outcome_score:.2f}",
        f"  Predicted reach: {winner.predicted_reach:,}",
        f"  Predicted engagement: {winner.predicted_engagement:.1f}%",
        f"  Predicted conversion: {winner.predicted_conversion:.1f}%",
        f"  Confidence: {winner.confidence:.0%}",
        f"  Feasibility: {winner.feasibility:.2f}",
    ]

    if runner_up:
        lines.extend([
            "",
            f"RUNNER-UP: {runner_up.platform} + {runner_up.format}",
            f"  Topic: {runner_up.topic}",
            f"  Outcome score: {runner_up.outcome_score:.2f}",
            f"  Predicted reach: {runner_up.predicted_reach:,}",
            f"  Predicted conversion: {runner_up.predicted_conversion:.1f}%",
            f"  Score gap: {winner.outcome_score - runner_up.outcome_score:.2f}",
        ])

    lines.extend([
        "",
        f"Decision confidence: {decision.decision_confidence}",
        f"Uncertainty flag: {decision.uncertainty_flag}",
        f"Exploration triggered: {decision.exploration_triggered}",
    ])

    if decision.exploration_triggered:
        lines.append(f"Exploration reason: {decision.exploration_reason}")

    if decision.rejected:
        lines.append("")
        lines.append("TOP REJECTED ALTERNATIVES:")
        for r in decision.rejected[:3]:
            lines.append(f"  - {r.platform} ({r.format}): score {r.outcome_score:.2f}, {r.reason}")

    lines.append("")
    lines.append("Explain why the winner was selected and why alternatives were rejected.")

    return "\n".join(lines)
