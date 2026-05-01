"""Feedback service — performance analysis and active learning.

Computes simulation parameter updates from predicted vs actual performance,
persists decisions to strategy memory, and adjusts time synergy multipliers.
"""

import logging
import random
import uuid
from datetime import datetime, timezone

from app.schemas.common import UserInput
from app.schemas.interpretation import InterpretationResponse
from app.schemas.feedback import FeedbackRequest, FeedbackResponse
from app.prompts.feedback_prompt import FEEDBACK_SYSTEM_PROMPT, build_feedback_user_prompt
from app.services.llm_service import invoke_structured
from app.services.simulation_state import simulation_state
from app.services.strategy_memory import strategy_memory, StrategyRecord
from app.constants import TIME_SYNERGY_LEARNING_RATE

logger = logging.getLogger(__name__)


def _compute_simulation_updates(
    predicted: dict, actual: dict,
    platform: str, fmt: str, goal_type: str, time_window: str,
) -> dict[str, dict[str, float]]:
    """Compute simulation parameter adjustments from performance delta."""
    updates: dict[str, dict[str, float]] = {}

    reach_ratio = actual["reach"] / max(predicted["reach"], 1)
    eng_ratio = actual["engagement"] / max(predicted["engagement"], 0.01)
    conv_ratio = actual["conversion"] / max(predicted["conversion"], 0.01)

    # Platform multiplier
    if reach_ratio < 0.70:
        updates.setdefault("platform_multiplier", {})[platform] = -0.05
    elif reach_ratio > 1.30:
        updates.setdefault("platform_multiplier", {})[platform] = +0.05

    # Format multiplier
    if eng_ratio < 0.75:
        updates.setdefault("format_multiplier", {})[fmt] = -0.04
    elif eng_ratio > 1.25:
        updates.setdefault("format_multiplier", {})[fmt] = +0.04

    # CTA multiplier
    if conv_ratio < 0.80:
        updates.setdefault("cta_multiplier", {})[goal_type] = -0.03
    elif conv_ratio > 1.20:
        updates.setdefault("cta_multiplier", {})[goal_type] = +0.03

    # Time synergy learning
    if time_window:
        combined_ratio = (reach_ratio + eng_ratio) / 2
        time_key = f"{platform}|{time_window}"
        if combined_ratio < 0.80:
            updates.setdefault("time_synergy_multiplier", {})[time_key] = -TIME_SYNERGY_LEARNING_RATE
        elif combined_ratio > 1.20:
            updates.setdefault("time_synergy_multiplier", {})[time_key] = +TIME_SYNERGY_LEARNING_RATE

    return updates


def _generate_mock_actuals(
    predicted_reach: int, predicted_engagement: float, predicted_conversion: float,
) -> dict[str, float]:
    """Generate simulated actual metrics for demo/testing."""
    return {
        "reach": int(predicted_reach * random.uniform(0.65, 1.35)),
        "engagement": round(predicted_engagement * random.uniform(0.60, 1.40), 1),
        "conversion": round(predicted_conversion * random.uniform(0.55, 1.45), 1),
    }


def _compute_perf_ratio(predicted: dict, actual: dict) -> float:
    """Compute composite performance ratio (actual / predicted)."""
    ratios = []
    for key in ["reach", "engagement", "conversion"]:
        pred = predicted.get(key, 0)
        act = actual.get(key, 0)
        if pred > 0:
            ratios.append(act / pred)
    return round(sum(ratios) / max(len(ratios), 1), 3) if ratios else 1.0


def _extract_keywords(topic: str) -> list[str]:
    """Extract simple keywords from a topic string."""
    stop = {"the", "a", "an", "for", "to", "of", "in", "and", "with", "that", "this", "on"}
    return [w.lower() for w in topic.split() if w.lower() not in stop and len(w) > 2][:5]


def _fallback_feedback(
    predicted: dict, actual: dict,
    platform: str, fmt: str, goal_type: str,
    sim_updates: dict, state_version: int,
) -> FeedbackResponse:
    """Template fallback — deterministic analysis."""
    delta = {
        "reach": round(actual["reach"] - predicted["reach"], 1),
        "engagement": round(actual["engagement"] - predicted["engagement"], 1),
        "conversion": round(actual["conversion"] - predicted["conversion"], 1),
    }

    reach_ratio = actual["reach"] / max(predicted["reach"], 1)
    eng_ratio = actual["engagement"] / max(predicted["engagement"], 0.01)
    conv_ratio = actual["conversion"] / max(predicted["conversion"], 0.01)

    # What worked
    worked_parts = []
    if reach_ratio >= 1.0:
        worked_parts.append(f"Reach exceeded prediction by {(reach_ratio - 1) * 100:.0f}%")
    if eng_ratio >= 1.0:
        worked_parts.append(f"Engagement exceeded prediction by {(eng_ratio - 1) * 100:.0f}%")
    if conv_ratio >= 1.0:
        worked_parts.append(f"Conversion exceeded prediction by {(conv_ratio - 1) * 100:.0f}%")
    what_worked = "; ".join(worked_parts) if worked_parts else "No metrics exceeded prediction"

    # What underperformed
    under_parts = []
    if reach_ratio < 0.85:
        under_parts.append(f"Reach: {actual['reach']:,} vs predicted {predicted['reach']:,}")
    if eng_ratio < 0.85:
        under_parts.append(f"Engagement: {actual['engagement']:.1f}% vs predicted {predicted['engagement']:.1f}%")
    if conv_ratio < 0.85:
        under_parts.append(f"Conversion: {actual['conversion']:.1f}% vs predicted {predicted['conversion']:.1f}%")
    what_underperformed = "; ".join(under_parts) if under_parts else "All metrics within acceptable range"

    # Why
    why = ""
    if reach_ratio < 0.85:
        why += f"Platform {platform} may have lower organic reach than benchmarked. "
    if conv_ratio < 0.85:
        why += f"The {fmt} format may not drive {goal_type} effectively on {platform}."
    if not why:
        why = "Performance was within expected variance."

    # Platform change suggestion
    should_change = reach_ratio < 0.60 or conv_ratio < 0.60
    change_reason = ""
    if should_change:
        change_reason = f"Significant underperformance on {platform} suggests testing an alternative."

    # Next recommendation
    overall_ratio = (reach_ratio + eng_ratio + conv_ratio) / 3
    if overall_ratio >= 1.1:
        next_rec = f"Double down on {platform} {fmt} — performance exceeded expectations."
    elif overall_ratio >= 0.85:
        next_rec = f"Continue with {platform} {fmt} but test timing or topic variations."
    else:
        next_rec = f"Consider switching platform or format — current approach underperforming."

    return FeedbackResponse(
        actual_reach=int(actual["reach"]),
        actual_engagement=round(actual["engagement"], 1),
        actual_conversion=round(actual["conversion"], 1),
        predicted=predicted,
        actual=actual,
        delta=delta,
        simulation_param_updates=sim_updates,
        state_version=state_version,
        what_worked=what_worked,
        what_underperformed=what_underperformed,
        why_underperformed=why,
        what_should_change=next_rec,
        should_platform_change=should_change,
        platform_change_reason=change_reason,
        next_recommendation=next_rec,
        learning_note=(
            f"Performance ratio: {overall_ratio:.2f}. "
            f"Simulation parameters updated: {len(sim_updates)} categories."
        ),
    )


def run_feedback(
    request: FeedbackRequest,
) -> FeedbackResponse:
    """Execute the feedback loop — analyze, update state, persist memory."""
    predicted = {
        "reach": request.predicted_reach,
        "engagement": request.predicted_engagement,
        "conversion": request.predicted_conversion,
    }

    # Use provided actuals or generate mock
    if request.actual_reach is not None:
        actual = {
            "reach": request.actual_reach,
            "engagement": request.actual_engagement or request.predicted_engagement,
            "conversion": request.actual_conversion or request.predicted_conversion,
        }
    else:
        actual = _generate_mock_actuals(
            request.predicted_reach, request.predicted_engagement, request.predicted_conversion,
        )

    # Compute simulation parameter updates
    sim_updates = _compute_simulation_updates(
        predicted, actual,
        request.platform, request.format, request.goal_type, request.time_window,
    )

    # Apply updates to persistent state
    if sim_updates:
        simulation_state.apply_updates(sim_updates)

    state_version = simulation_state.version

    # Persist to strategy memory
    perf_ratio = _compute_perf_ratio(predicted, actual)
    record = StrategyRecord(
        decision_id=str(uuid.uuid4())[:8],
        timestamp=datetime.now(timezone.utc).isoformat(),
        platform=request.platform,
        format=request.format,
        topic_keywords=_extract_keywords(request.topic),
        goal_type=request.goal_type,
        audience_segment=request.audience_segment,
        business_type=request.business_type,
        predicted=predicted,
        actual=actual,
        outcome_score=request.outcome_score,
        performance_ratio=perf_ratio,
    )
    strategy_memory.save_record(record)

    # Try LLM feedback, fallback if unavailable
    user_prompt = build_feedback_user_prompt(
        business_domain=request.business_domain,
        content_goal=request.content_goal,
        target_audience=request.target_audience,
        tone=request.tone,
        topic=request.topic,
        platform=request.platform,
        predicted_reach=predicted["reach"],
        predicted_engagement=predicted["engagement"],
        predicted_conversion=predicted["conversion"],
        actual_reach=int(actual["reach"]),
        actual_engagement=actual["engagement"],
        actual_conversion=actual["conversion"],
        headline=request.headline,
    )

    result = invoke_structured(
        system_prompt=FEEDBACK_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        schema=FeedbackResponse,
    )

    if result is not None:
        # Override the learning fields with computed values
        result.predicted = predicted
        result.actual = actual
        result.delta = {
            k: round(actual[k] - predicted[k], 1) for k in predicted
        }
        result.simulation_param_updates = sim_updates
        result.state_version = state_version
        return result

    logger.info("Using fallback feedback")
    return _fallback_feedback(
        predicted, actual,
        request.platform, request.format, request.goal_type,
        sim_updates, state_version,
    )
