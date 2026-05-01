"""Agent router — Strategent v3 simulation-first pipeline.

Pipeline order:
  1. Interpret    → structured strategic variables
  2. Generate     → 8–15 candidate strategy tuples
  3. Simulate ALL → non-linear, interaction-aware predictions
  4. Decide       → outcome-driven selection (deterministic)
  5. Explain      → post-decision LLM narrative
  6. Content      → copy generation (skipped if no viable strategy)
  7. Feedback     → active learning + memory persistence
"""

import logging

from fastapi import APIRouter, HTTPException

from app.schemas.common import UserInput
from app.schemas.feedback import FeedbackRequest
from app.schemas.pipeline import PipelineResponse
from app.schemas.explanation import ExplanationResponse
from app.schemas.content import ContentResponse
from app.schemas.feedback import FeedbackResponse
from app.services.interpretation_service import run_interpretation
from app.services.candidate_service import generate_candidates
from app.services.simulation_service import simulate_all
from app.services.decision_service import run_decision
from app.services.explainer_service import run_explanation
from app.services.content_service import run_content
from app.services.feedback_service import run_feedback

logger = logging.getLogger(__name__)

router = APIRouter(tags=["agent"])


@router.post("/pipeline", response_model=PipelineResponse)
async def run_pipeline(user_input: UserInput) -> PipelineResponse:
    """Execute the full v3 simulation-first pipeline."""

    reasoning_chain: list[str] = []

    # ── Stage 1: Interpret ───────────────────────────────────────
    try:
        interpretation = run_interpretation(user_input)
        reasoning_chain.append(
            f"[Interpret] {interpretation.business_type} | {interpretation.goal_type} | "
            f"{interpretation.audience_segment} (confidence: {interpretation.audience_inference_confidence:.0%})"
        )
    except Exception as e:
        logger.error("Interpretation failed: %s", e)
        raise HTTPException(status_code=500, detail=f"Interpretation failed: {e}")

    # ── Stage 2: Generate Candidates ─────────────────────────────
    try:
        candidate_pool = generate_candidates(user_input, interpretation)
        reasoning_chain.append(
            f"[Candidates] Generated {len(candidate_pool.candidates)} strategy combinations "
            f"({candidate_pool.generation_method})"
        )
    except Exception as e:
        logger.error("Candidate generation failed: %s", e)
        raise HTTPException(status_code=500, detail=f"Candidate generation failed: {e}")

    # ── Stage 3: Simulate ALL ────────────────────────────────────
    try:
        simulation = simulate_all(candidate_pool.candidates)
        reasoning_chain.append(
            f"[Simulate] Evaluated {len(simulation.all_candidates)} candidates. "
            f"Winner: {simulation.winner.platform} ({simulation.winner.format}) "
            f"score={simulation.winner.outcome_score:.2f}"
        )
    except Exception as e:
        logger.error("Simulation failed: %s", e)
        raise HTTPException(status_code=500, detail=f"Simulation failed: {e}")

    # ── Stage 4: Decide ──────────────────────────────────────────
    try:
        decision = run_decision(
            user_input, interpretation,
            simulation.all_candidates, candidate_pool,
        )
        if decision.no_viable_strategy:
            reasoning_chain.append(
                f"[Decide] NO VIABLE STRATEGY — all candidates below threshold. "
                f"Best: {decision.outcome_score:.2f}"
            )
        else:
            reasoning_chain.append(
                f"[Decide] Selected {decision.platform} ({decision.format}) "
                f"score={decision.outcome_score:.2f} "
                f"confidence={decision.decision_confidence}"
            )
            if decision.exploration_swapped:
                reasoning_chain.append(
                    f"[Decide] EXPLORATION SWAP — original winner replaced. "
                    f"Reason: {decision.exploration_reason}"
                )
    except Exception as e:
        logger.error("Decision failed: %s", e)
        raise HTTPException(status_code=500, detail=f"Decision failed: {e}")

    # ── Stage 5: Explain ─────────────────────────────────────────
    try:
        explanation = run_explanation(
            decision, simulation.winner, simulation.runner_up, interpretation,
        )
        # Inject explanation into decision
        decision.reason = explanation.reason
        decision.chosen_because = explanation.chosen_because
        reasoning_chain.append(f"[Explain] {explanation.chosen_because}")
    except Exception as e:
        logger.error("Explanation failed (non-fatal): %s", e)
        explanation = ExplanationResponse(
            reason="Explanation unavailable.",
            chosen_because="Selected by highest outcome score.",
        )
        reasoning_chain.append("[Explain] Fallback — LLM unavailable")

    # ── Stage 6: Content (skip if no viable strategy) ────────────
    if decision.no_viable_strategy:
        content = ContentResponse(
            headline="No viable strategy",
            post_copy="Unable to generate content — all strategy candidates scored below the viability threshold.",
            cta="Refine your brief and try again.",
            hashtags=[],
        )
        reasoning_chain.append("[Content] SKIPPED — no viable strategy")
    else:
        try:
            content = run_content(
                user_input, decision.topic, decision.platform, interpretation,
            )
            reasoning_chain.append(f"[Content] Generated: {content.headline[:50]}...")
        except Exception as e:
            logger.error("Content generation failed: %s", e)
            raise HTTPException(status_code=500, detail=f"Content generation failed: {e}")

    # ── Stage 7: Feedback (skip if no viable strategy) ───────────
    if decision.no_viable_strategy:
        feedback_response = FeedbackResponse(
            actual_reach=0, actual_engagement=0.0, actual_conversion=0.0,
            predicted={"reach": 0, "engagement": 0.0, "conversion": 0.0},
            actual={"reach": 0, "engagement": 0.0, "conversion": 0.0},
            delta={"reach": 0, "engagement": 0.0, "conversion": 0.0},
            simulation_param_updates={}, state_version=0,
            what_worked="N/A", what_underperformed="N/A",
            why_underperformed="No strategy was executed.",
            what_should_change="Refine the input brief.",
            should_platform_change=False,
            next_recommendation="Refine brief: narrow audience, clarify goal, reconsider platform.",
            learning_note="No strategy executed — no learning possible.",
        )
        reasoning_chain.append("[Feedback] SKIPPED — no viable strategy")
    else:
        try:
            feedback_request = FeedbackRequest(
                business_domain=user_input.business_domain,
                content_goal=user_input.content_goal,
                target_audience=user_input.target_audience,
                tone=user_input.tone,
                topic=decision.topic,
                platform=decision.platform,
                format=decision.format,
                predicted_reach=decision.predicted_reach,
                predicted_engagement=decision.predicted_engagement,
                predicted_conversion=decision.predicted_conversion,
                headline=content.headline,
                goal_type=interpretation.goal_type,
                audience_segment=interpretation.audience_segment,
                business_type=interpretation.business_type,
                time_window=candidate_pool.candidates[0].time_window if candidate_pool.candidates else "",
                outcome_score=decision.outcome_score,
            )
            feedback_response = run_feedback(feedback_request)
            reasoning_chain.append(
                f"[Feedback] State v{feedback_response.state_version}. "
                f"Updates: {len(feedback_response.simulation_param_updates)} categories."
            )
        except Exception as e:
            logger.error("Feedback failed: %s", e)
            raise HTTPException(status_code=500, detail=f"Feedback failed: {e}")

    return PipelineResponse(
        interpretation=interpretation,
        candidates=candidate_pool,
        simulation=simulation,
        decision=decision,
        explanation=explanation,
        content=content,
        feedback=feedback_response,
        reasoning_chain=reasoning_chain,
    )
