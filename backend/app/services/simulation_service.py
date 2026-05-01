"""Simulation Engine — non-linear, interaction-aware, per-candidate simulation.

Runs BEFORE decision for ALL candidates. Uses saturation curves, interaction
matrices, and memory-adjusted multipliers. Every prediction is deterministic
and traceable via FormulaInputs.
"""

import logging

from app.schemas.strategy_candidate import StrategyCandidate
from app.schemas.simulation import (
    CandidateSimulation, FormulaInputs, SimulationResponse,
)
from app.constants import (
    PLATFORM_BENCHMARKS, PLATFORM_FORMAT_SYNERGY, PLATFORM_GOAL_SYNERGY,
    AUDIENCE_PLATFORM_SYNERGY, PLATFORM_TIME_SYNERGY,
    FORMAT_FEASIBILITY, GOAL_WEIGHT_PROFILES, DEFAULT_WEIGHT_PROFILE,
    saturate, compute_complexity_penalty,
)
from app.services.simulation_state import SimulationState, simulation_state
from app.services.strategy_memory import StrategyMemory, strategy_memory

logger = logging.getLogger(__name__)


def _get_audience_synergy(audience_segment: str, platform: str) -> float:
    """Look up audience-platform synergy multiplier."""
    audience_lower = audience_segment.lower()
    best = 1.0
    for keyword, platform_scores in AUDIENCE_PLATFORM_SYNERGY.items():
        if keyword in audience_lower:
            mult = platform_scores.get(platform, 1.0)
            if mult != 1.0:
                best = mult
    return best


def _compute_confidence(signals: list[float]) -> tuple[float, float, float]:
    """Enhanced confidence model with consistency penalty.

    Returns (confidence, consistency, consistency_multiplier).
    """
    if not signals:
        return 0.5, 1.0, 1.0

    mean_sig = sum(signals) / len(signals)
    spread = (sum((s - mean_sig) ** 2 for s in signals) / len(signals)) ** 0.5

    min_sig = min(signals)
    max_sig = max(signals)
    consistency = min_sig / max(max_sig, 0.01)

    raw_confidence = 0.45 + mean_sig * 0.035 - spread * 0.05

    consistency_multiplier = 0.6 + 0.4 * consistency

    confidence = round(max(0.20, min(0.95, raw_confidence * consistency_multiplier)), 2)
    return confidence, round(consistency, 3), round(consistency_multiplier, 3)


def _compute_outcome_score(
    norm_conversion: float,
    norm_reach: float,
    norm_engagement: float,
    feasibility: float,
    confidence: float,
    goal_type: str,
    memory_boost: float,
    complexity_penalty: float,
) -> tuple[float, dict[str, float], str]:
    """Goal-adaptive outcome score. Returns (score, weights, profile_name)."""
    weights = GOAL_WEIGHT_PROFILES.get(goal_type, DEFAULT_WEIGHT_PROFILE)
    profile_name = goal_type if goal_type in GOAL_WEIGHT_PROFILES else "default"

    raw = (
        weights["conversion"]  * norm_conversion * 10
        + weights["reach"]       * norm_reach * 10
        + weights["engagement"]  * norm_engagement * 10
        + weights["feasibility"] * feasibility * 10
        + weights["confidence"]  * confidence * 10
    )

    final = round(raw * memory_boost * complexity_penalty, 2)
    return final, weights, profile_name


def simulate_candidate(
    candidate: StrategyCandidate,
    state: SimulationState | None = None,
    memory: StrategyMemory | None = None,
) -> CandidateSimulation:
    """Non-linear, interaction-aware simulation for one candidate strategy."""
    if state is None:
        state = simulation_state
    if memory is None:
        memory = strategy_memory

    platform = candidate.platform
    fmt = candidate.format
    goal_type = candidate.goal_type

    # ── Interaction multipliers ──────────────────────────────────
    format_synergy = PLATFORM_FORMAT_SYNERGY.get((platform, fmt), 1.0)
    goal_synergy = PLATFORM_GOAL_SYNERGY.get((platform, goal_type), 1.0)
    audience_synergy = _get_audience_synergy(candidate.audience_segment, platform)

    # ── Memory-adjusted multipliers ──────────────────────────────
    platform_mult = state.platform_multiplier.get(platform, 1.0)
    format_mult = state.format_multiplier.get(fmt, 1.0)
    cta_mult = state.cta_multiplier.get(goal_type, 1.0)

    # ── Time synergy (static + learned) ──────────────────────────
    time_synergy = PLATFORM_TIME_SYNERGY.get(
        (platform, candidate.time_window),
        {"reach": 1.0, "engagement": 1.0},
    )
    time_key = f"{platform}|{candidate.time_window}"
    time_learned = state.time_synergy_multiplier.get(time_key, 1.0)
    effective_time_reach = time_synergy["reach"] * time_learned
    effective_time_eng = time_synergy["engagement"] * time_learned

    # ── Adjusted signal scores ───────────────────────────────────
    adj_audience_fit = candidate.audience_fit * audience_synergy * platform_mult
    adj_format_fit = candidate.format_fit * format_synergy * format_mult
    adj_goal_fit = candidate.goal_fit * goal_synergy
    adj_conversion_fit = candidate.conversion_fit * goal_synergy * cta_mult

    # ── Platform benchmarks ──────────────────────────────────────
    bench = PLATFORM_BENCHMARKS.get(platform, PLATFORM_BENCHMARKS["Instagram"])

    # ── Composite signals (with time synergy) ────────────────────
    reach_signal = (
        0.35 * adj_audience_fit
        + 0.30 * adj_format_fit
        + 0.20 * candidate.timing_fit
        + 0.15 * candidate.tone_fit
    ) * effective_time_reach

    eng_signal = (
        0.35 * adj_format_fit
        + 0.30 * adj_audience_fit
        + 0.20 * adj_goal_fit
        + 0.15 * candidate.tone_fit
    ) * effective_time_eng

    conv_signal = (
        0.40 * adj_conversion_fit
        + 0.30 * adj_goal_fit
        + 0.20 * adj_audience_fit
        + 0.10 * adj_format_fit
    )

    # ── Non-linear predictions (saturated) ───────────────────────
    predicted_reach = int(saturate(reach_signal, ceiling=bench["reach_ceiling"], steepness=0.22))
    predicted_engagement = round(
        saturate(eng_signal, ceiling=bench["engagement_ceiling"], steepness=0.28), 1
    )
    predicted_conversion = round(
        saturate(conv_signal, ceiling=bench["conversion_ceiling"], steepness=0.20), 1
    )

    # ── Feasibility + complexity ─────────────────────────────────
    feasibility = FORMAT_FEASIBILITY.get(fmt, 0.70)
    complexity_penalty = compute_complexity_penalty(fmt)

    # ── Confidence (enhanced w/ consistency) ─────────────────────
    signals = [
        candidate.audience_fit, candidate.goal_fit, candidate.format_fit,
        candidate.conversion_fit, candidate.tone_fit, candidate.timing_fit,
    ]
    confidence, consistency, consistency_mult = _compute_confidence(signals)

    # ── Memory boost ─────────────────────────────────────────────
    memory_boost = memory.get_memory_boost(
        platform=platform,
        fmt=fmt,
        goal_type=goal_type,
        audience_segment=candidate.audience_segment,
        business_type=candidate.business_type,
    )

    # ── Outcome score (goal-adaptive) ────────────────────────────
    norm_reach = min(1.0, predicted_reach / max(bench["reach_ceiling"], 1))
    norm_eng = predicted_engagement / max(bench["engagement_ceiling"], 0.01)
    norm_conv = predicted_conversion / max(bench["conversion_ceiling"], 0.01)

    outcome_score, weights, profile_name = _compute_outcome_score(
        norm_conv, norm_reach, norm_eng,
        feasibility, confidence,
        goal_type, memory_boost, complexity_penalty,
    )

    # ── Formula inputs (full traceability) ───────────────────────
    formula_inputs = FormulaInputs(
        base_reach_ceiling=int(bench["reach_ceiling"]),
        reach_signal=round(reach_signal, 2),
        engagement_signal=round(eng_signal, 2),
        conversion_signal=round(conv_signal, 2),
        format_synergy=format_synergy,
        goal_synergy=goal_synergy,
        audience_synergy=audience_synergy,
        platform_multiplier=platform_mult,
        format_multiplier=format_mult,
        cta_multiplier=cta_mult,
        time_synergy_reach=round(effective_time_reach, 3),
        time_synergy_engagement=round(effective_time_eng, 3),
        time_learned_multiplier=time_learned,
        feasibility=feasibility,
        complexity_penalty=complexity_penalty,
        memory_boost=memory_boost,
        signal_consistency=consistency,
        consistency_multiplier=consistency_mult,
        goal_weight_profile=profile_name,
        outcome_weights=weights,
    )

    return CandidateSimulation(
        candidate_id=candidate.candidate_id,
        platform=platform,
        topic=candidate.topic,
        format=fmt,
        predicted_reach=predicted_reach,
        predicted_engagement=predicted_engagement,
        predicted_conversion=predicted_conversion,
        confidence=confidence,
        feasibility=feasibility,
        complexity_penalty=complexity_penalty,
        outcome_score=outcome_score,
        formula_inputs=formula_inputs,
    )


def simulate_all(
    candidates: list[StrategyCandidate],
    state: SimulationState | None = None,
    memory: StrategyMemory | None = None,
) -> SimulationResponse:
    """Simulate ALL candidates and return sorted results."""
    results = [simulate_candidate(c, state, memory) for c in candidates]
    results.sort(key=lambda r: r.outcome_score, reverse=True)

    winner = results[0]
    runner_up = results[1] if len(results) > 1 else None

    # Comparison summary
    if runner_up:
        comparison = (
            f"{winner.platform} ({winner.format}) scores {winner.outcome_score:.2f} vs "
            f"{runner_up.platform} ({runner_up.format}) at {runner_up.outcome_score:.2f}. "
            f"Predicted conversion: {winner.predicted_conversion:.1f}% vs "
            f"{runner_up.predicted_conversion:.1f}%."
        )
    else:
        comparison = f"{winner.platform} is the only viable candidate."

    # Score breakdown
    breakdown = [
        f"Winner: {winner.platform} + {winner.format} → outcome {winner.outcome_score:.2f}",
        f"Reach: {winner.predicted_reach:,} (ceiling: {winner.formula_inputs.base_reach_ceiling:,})",
        f"Engagement: {winner.predicted_engagement:.1f}%, Conversion: {winner.predicted_conversion:.1f}%",
        f"Confidence: {winner.confidence:.0%} (consistency: {winner.formula_inputs.signal_consistency:.2f})",
        f"Memory boost: {winner.formula_inputs.memory_boost:.3f}, "
        f"Complexity penalty: {winner.complexity_penalty:.4f}",
    ]

    return SimulationResponse(
        all_candidates=results,
        winner=winner,
        runner_up=runner_up,
        comparison_summary=comparison,
        score_breakdown=breakdown,
    )
