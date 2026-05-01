"""Decision Service — outcome-driven selection from simulated candidates.

The decision layer does NOT score or think. It receives fully simulated
candidates, picks the highest outcome_score, and structures the decision record.
Includes uncertainty classification, exploration logic, quality assessment,
and no-viable-strategy guard.
"""

import logging
from typing import Optional

from app.schemas.common import UserInput
from app.schemas.interpretation import InterpretationResponse
from app.schemas.simulation import CandidateSimulation
from app.schemas.strategy_candidate import CandidatePool, StrategyCandidate
from app.schemas.decision import (
    DecisionResponse, RejectedAlternative, TradeOffAnalysis,
    CandidateTopic, PlatformScore, compute_weighted_total,
)
from app.constants import (
    UNCERTAINTY_THRESHOLD, HIGH_CONFIDENCE_THRESHOLD,
    EXPLORE_THRESHOLD, EXPLORE_SWAP_THRESHOLD, STAGNATION_LIMIT,
    QUALITY_THRESHOLD, MINIMUM_VIABLE_SCORE,
)
from app.services.strategy_memory import StrategyMemory, strategy_memory

logger = logging.getLogger(__name__)


def _classify_confidence(
    winner_score: float,
    runner_up_score: float,
    winner_confidence: float,
) -> tuple[str, bool, float]:
    """Classify decision confidence based on score gap and prediction quality."""
    gap = winner_score - runner_up_score

    if gap < UNCERTAINTY_THRESHOLD:
        cs = max(0.3, min(0.6, 0.3 + gap * 0.6))
        return "low", True, round(cs, 2)
    elif gap < HIGH_CONFIDENCE_THRESHOLD:
        cs = max(0.5, min(0.8, 0.5 + gap * 0.2))
        return "medium", False, round(cs, 2)
    else:
        cs = max(0.7, min(0.95, 0.7 + winner_confidence * 0.25))
        return "high", False, round(cs, 2)


def _should_explore(
    winner: CandidateSimulation,
    runner_up: CandidateSimulation,
    uncertainty_flag: bool,
    memory: StrategyMemory,
) -> tuple[bool, str]:
    """Determine if the system should explore the runner-up."""
    if not uncertainty_flag:
        return False, ""

    gap = winner.outcome_score - runner_up.outcome_score
    if gap > EXPLORE_THRESHOLD:
        return False, ""

    # Stagnation check
    recent = memory.get_recent_winners(limit=STAGNATION_LIMIT)
    winner_key = f"{winner.platform}|{winner.format}"
    stagnation_count = sum(
        1 for r in recent if f"{r.platform}|{r.format}" == winner_key
    )

    if stagnation_count >= STAGNATION_LIMIT:
        return True, (
            f"Exploration triggered: {winner.platform}+{winner.format} selected "
            f"{stagnation_count} consecutive times. Runner-up {runner_up.platform}+"
            f"{runner_up.format} recommended."
        )

    if gap < EXPLORE_SWAP_THRESHOLD:
        return True, (
            f"Score gap is only {gap:.2f} — strategies are statistically equivalent. "
            f"A/B testing recommended."
        )

    return False, ""


def _assess_pool_quality(
    ranked: list[CandidateSimulation],
) -> tuple[float, bool, str]:
    """Assess whether the candidate pool has viable strategies."""
    if not ranked:
        return 0.0, True, "Empty candidate pool."

    max_score = ranked[0].outcome_score
    theoretical_max = 10.0
    relative_score = max_score / theoretical_max if theoretical_max > 0 else 0.0

    if relative_score < QUALITY_THRESHOLD:
        return round(relative_score, 3), True, (
            f"Best candidate scores {max_score:.2f} ({relative_score:.0%} of theoretical max). "
            f"All strategies have low predicted outcomes. Consider refining the brief."
        )

    return round(relative_score, 3), False, ""


def _find_candidate(
    pool: CandidatePool, candidate_id: str,
) -> Optional[StrategyCandidate]:
    """Find a candidate in the pool by ID."""
    for c in pool.candidates:
        if c.candidate_id == candidate_id:
            return c
    return None


def _generate_rejection_reason(
    winner: CandidateSimulation,
    candidate: CandidateSimulation,
) -> str:
    """Generate rejection reason for a non-winning candidate."""
    parts = []
    if candidate.predicted_conversion < winner.predicted_conversion:
        parts.append(
            f"Lower conversion ({candidate.predicted_conversion:.1f}% vs "
            f"{winner.predicted_conversion:.1f}%)"
        )
    if candidate.predicted_reach < winner.predicted_reach:
        parts.append(
            f"Lower reach ({candidate.predicted_reach:,} vs {winner.predicted_reach:,})"
        )
    if candidate.confidence < winner.confidence:
        parts.append(f"Lower confidence ({candidate.confidence:.0%})")
    if candidate.feasibility < winner.feasibility:
        parts.append(f"Lower feasibility ({candidate.feasibility:.2f})")

    return "; ".join(parts) if parts else (
        f"Lower outcome score ({candidate.outcome_score:.2f} vs {winner.outcome_score:.2f})"
    )


def _build_trade_off(
    winner: CandidateSimulation,
    runner_up: CandidateSimulation,
) -> TradeOffAnalysis:
    """Build trade-off analysis between top-2 candidates."""
    # Determine strengths
    w_strength = "conversion" if winner.predicted_conversion > runner_up.predicted_conversion else "reach"
    r_strength = "reach" if runner_up.predicted_reach > winner.predicted_reach else "conversion"

    return TradeOffAnalysis(
        candidate_a=winner.candidate_id,
        candidate_a_score=winner.outcome_score,
        candidate_a_strength=w_strength,
        candidate_b=runner_up.candidate_id,
        candidate_b_score=runner_up.outcome_score,
        candidate_b_strength=r_strength,
        delta=round(winner.outcome_score - runner_up.outcome_score, 2),
        trade_off=(
            f"{winner.platform} ({winner.format}) yields {w_strength} "
            f"({winner.predicted_conversion:.1f}% conversion, {winner.predicted_reach:,} reach) "
            f"vs {runner_up.platform} ({runner_up.format}) with stronger {r_strength} "
            f"({runner_up.predicted_conversion:.1f}% conversion, {runner_up.predicted_reach:,} reach)."
        ),
        decision_rationale=(
            f"{winner.platform} selected — outcome score {winner.outcome_score:.2f} "
            f"vs {runner_up.outcome_score:.2f} (delta: "
            f"{winner.outcome_score - runner_up.outcome_score:.2f})."
        ),
    )


def _build_candidate_topics(pool: CandidatePool) -> list[CandidateTopic]:
    """Extract unique topics from the candidate pool for UI display."""
    seen: set[str] = set()
    topics: list[CandidateTopic] = []
    for c in pool.candidates:
        if c.topic not in seen:
            seen.add(c.topic)
            topics.append(CandidateTopic(
                angle=c.topic,
                audience_fit_rationale=f"Targets {c.audience_segment}",
                goal_fit_rationale=f"Supports {c.goal_type} goal",
                selected=False,
            ))
    return topics[:5]


def _build_platform_scores(pool: CandidatePool) -> list[PlatformScore]:
    """Aggregate signal scores by platform for UI display."""
    platform_data: dict[str, list[StrategyCandidate]] = {}
    for c in pool.candidates:
        platform_data.setdefault(c.platform, []).append(c)

    scores: list[PlatformScore] = []
    for platform, cands in platform_data.items():
        n = len(cands)
        avg = lambda attr: round(sum(getattr(c, attr) for c in cands) / n, 1)
        aud = avg("audience_fit")
        goal = avg("goal_fit")
        fmt = avg("format_fit")
        conv = avg("conversion_fit")
        tone = avg("tone_fit")
        timing = avg("timing_fit")
        total = aud + goal + fmt + conv + tone + timing
        wt = compute_weighted_total({
            "audience_fit": aud, "goal_fit": goal, "format_fit": fmt,
            "conversion_fit": conv, "tone_fit": tone, "timing_fit": timing,
        })
        scores.append(PlatformScore(
            platform=platform, audience_fit=aud, goal_fit=goal,
            format_fit=fmt, conversion_fit=conv, tone_fit=tone,
            timing_fit=timing, total=round(total, 1), weighted_total=wt,
            why=f"Signal average across {n} candidates",
        ))

    scores.sort(key=lambda s: s.weighted_total, reverse=True)
    return scores


def run_decision(
    user_input: UserInput,
    interpretation: InterpretationResponse,
    simulated_candidates: list[CandidateSimulation],
    candidate_pool: CandidatePool,
    memory: StrategyMemory | None = None,
) -> DecisionResponse:
    """Select the highest outcome_score candidate. Deterministic — no heuristics."""
    if memory is None:
        memory = strategy_memory

    ranked = sorted(simulated_candidates, key=lambda c: c.outcome_score, reverse=True)

    interp_summary = (
        f"{interpretation.business_type} | {interpretation.goal_type} | "
        f"{interpretation.audience_segment}"
    )

    # ── NO-VIABLE-STRATEGY GUARD ─────────────────────────────────
    if not ranked or ranked[0].outcome_score < MINIMUM_VIABLE_SCORE:
        best = ranked[0].outcome_score if ranked else 0.0
        return DecisionResponse(
            topic="No viable strategy identified",
            platform="None", format="None", posting_time="N/A",
            outcome_score=best, decision_score=best,
            reason=(
                f"All {len(ranked)} candidates scored below the minimum viability "
                f"threshold ({MINIMUM_VIABLE_SCORE}). Best score: {best:.2f}."
            ),
            chosen_because="No candidate met the minimum outcome threshold.",
            all_evaluated=ranked,
            interpretation_used=interp_summary,
            decision_confidence="none", uncertainty_flag=True,
            confidence_score=0.0, no_viable_strategy=True,
            relative_score=round(best / 10.0, 3),
            strategy_quality_warning=True,
            quality_warning_reason=(
                f"Best outcome score ({best:.2f}) below threshold ({MINIMUM_VIABLE_SCORE})."
            ),
        )

    winner = ranked[0]
    runner_up = ranked[1] if len(ranked) > 1 else None

    # ── QUALITY ASSESSMENT ───────────────────────────────────────
    relative_score, quality_warning, quality_reason = _assess_pool_quality(ranked)

    # ── UNCERTAINTY & CONFIDENCE ─────────────────────────────────
    if runner_up:
        decision_conf, uncertainty_flag, conf_score = _classify_confidence(
            winner.outcome_score, runner_up.outcome_score, winner.confidence,
        )
    else:
        decision_conf, uncertainty_flag, conf_score = "high", False, 0.85

    # ── TRADE-OFF ANALYSIS ───────────────────────────────────────
    trade_off = None
    if runner_up and uncertainty_flag:
        trade_off = _build_trade_off(winner, runner_up)

    # ── EXPLORATION ──────────────────────────────────────────────
    exploration_triggered = False
    exploration_reason = ""
    exploration_swapped = False
    original_winner_id = ""

    if runner_up:
        exploration_triggered, exploration_reason = _should_explore(
            winner, runner_up, uncertainty_flag, memory,
        )

        # Controlled swap when gap is negligible
        if exploration_triggered:
            gap = winner.outcome_score - runner_up.outcome_score
            if gap < EXPLORE_SWAP_THRESHOLD:
                original_winner_id = winner.candidate_id
                original_winner = winner
                winner = runner_up
                runner_up = original_winner
                exploration_swapped = True
                exploration_reason += (
                    f" Decision SWAPPED: gap of {gap:.2f} is below {EXPLORE_SWAP_THRESHOLD}."
                )

    # ── REJECTION LOG ────────────────────────────────────────────
    rejected = []
    for cand in ranked:
        if cand.candidate_id == winner.candidate_id:
            continue
        rejected.append(RejectedAlternative(
            candidate_id=cand.candidate_id,
            platform=cand.platform,
            topic=cand.topic,
            format=cand.format,
            outcome_score=cand.outcome_score,
            predicted_conversion=cand.predicted_conversion,
            reason=_generate_rejection_reason(winner, cand),
        ))
        if len(rejected) >= 10:
            break

    # ── FIND WINNER IN POOL ──────────────────────────────────────
    winner_candidate = _find_candidate(candidate_pool, winner.candidate_id)
    posting_time = winner_candidate.posting_time if winner_candidate else "N/A"

    # ── BUILD LEGACY DISPLAY DATA ────────────────────────────────
    candidate_topics = _build_candidate_topics(candidate_pool)
    for ct in candidate_topics:
        if ct.angle == (winner_candidate.topic if winner_candidate else ""):
            ct.selected = True

    platform_scores = _build_platform_scores(candidate_pool)

    # ── AB TEST ALTERNATIVE ──────────────────────────────────────
    ab_test = None
    if exploration_triggered and runner_up:
        ab_test = {
            "candidate_id": runner_up.candidate_id,
            "platform": runner_up.platform,
            "format": runner_up.format,
            "topic": runner_up.topic,
            "outcome_score": runner_up.outcome_score,
            "predicted_conversion": runner_up.predicted_conversion,
        }

    return DecisionResponse(
        topic=winner_candidate.topic if winner_candidate else winner.topic,
        platform=winner.platform,
        format=winner.format,
        posting_time=posting_time,
        outcome_score=winner.outcome_score,
        decision_score=winner.outcome_score,
        predicted_reach=winner.predicted_reach,
        predicted_engagement=winner.predicted_engagement,
        predicted_conversion=winner.predicted_conversion,
        reason="",  # Filled by explainer
        chosen_because="",  # Filled by explainer
        candidate_topics=candidate_topics,
        platform_scores=platform_scores,
        all_evaluated=ranked[:15],
        rejected=rejected,
        trade_off_analysis=trade_off,
        interpretation_used=interp_summary,
        decision_confidence=decision_conf,
        uncertainty_flag=uncertainty_flag,
        confidence_score=conf_score,
        exploration_triggered=exploration_triggered,
        exploration_reason=exploration_reason,
        exploration_swapped=exploration_swapped,
        original_winner_id=original_winner_id,
        ab_test_alternative=ab_test,
        relative_score=relative_score,
        strategy_quality_warning=quality_warning,
        quality_warning_reason=quality_reason,
    )
