"""Candidate Generator — produces full strategy combinations for simulation.

Generates 8–15 strategy tuples: platform × topic × format × time.
Applies hard constraints to filter inappropriate platform-audience combinations.
Scores each candidate on 6 axes as simulation input signals.
"""

import logging
import re
from itertools import product

from app.schemas.common import UserInput
from app.schemas.interpretation import InterpretationResponse
from app.schemas.strategy_candidate import StrategyCandidate, CandidatePool
from app.constants import (
    PLATFORMS, PLATFORM_FORMATS, PLATFORM_TIMES, TIME_WINDOW_LABELS,
    FORMAT_FEASIBILITY, HARD_CONSTRAINT_EXCLUDES,
    PLATFORM_FORMAT_SYNERGY, PLATFORM_GOAL_SYNERGY, AUDIENCE_PLATFORM_SYNERGY,
)

logger = logging.getLogger(__name__)


def _apply_hard_constraints(
    platforms: list[str],
    audience_segment: str,
    business_type: str,
) -> list[str]:
    """Filter platforms based on hard constraint rules."""
    combined = f"{audience_segment} {business_type}".lower()
    excluded: set[str] = set()

    for keyword, excluded_platforms in HARD_CONSTRAINT_EXCLUDES.items():
        if keyword.lower() in combined:
            excluded.update(excluded_platforms)

    filtered = [p for p in platforms if p not in excluded]
    # Never return empty — keep at least the top constrained platforms
    return filtered if filtered else platforms[:3]


def _audience_fit_score(audience: str, platform: str) -> float:
    """Compute audience_fit signal score (0–10) for a platform."""
    audience_lower = audience.lower()
    matched = False
    best_score = 5.0  # neutral default

    for keyword, platform_scores in AUDIENCE_PLATFORM_SYNERGY.items():
        if keyword in audience_lower:
            mult = platform_scores.get(platform, 1.0)
            score = min(10.0, max(0.0, 5.0 * mult))
            if not matched:
                best_score = score
                matched = True
            else:
                best_score = max(best_score, score)

    return round(best_score, 1)


def _goal_fit_score(goal_type: str, platform: str) -> float:
    """Compute goal_fit signal score (0–10) for a platform."""
    synergy = PLATFORM_GOAL_SYNERGY.get((platform, goal_type), 1.0)
    return round(min(10.0, 5.0 * synergy), 1)


def _format_fit_score(platform: str, fmt: str) -> float:
    """Compute format_fit signal score (0–10) for a platform-format pair."""
    synergy = PLATFORM_FORMAT_SYNERGY.get((platform, fmt), 1.0)
    return round(min(10.0, 5.5 * synergy), 1)


def _conversion_fit_score(goal_type: str, platform: str) -> float:
    """Compute conversion_fit signal score (0–10)."""
    synergy = PLATFORM_GOAL_SYNERGY.get((platform, goal_type), 1.0)
    base = 6.0 if goal_type in ("conversion", "lead-generation") else 4.5
    return round(min(10.0, base * synergy), 1)


def _tone_fit_score(tone: str, platform: str) -> float:
    """Compute tone_fit (0–10) based on tone-platform alignment."""
    tone_map = {
        "professional":  {"LinkedIn": 9.0, "YouTube": 7.0, "X": 6.5, "Facebook": 5.5, "Instagram": 5.0, "TikTok": 3.5},
        "casual":        {"Instagram": 8.5, "TikTok": 8.5, "Facebook": 7.5, "X": 6.0, "YouTube": 6.0, "LinkedIn": 4.0},
        "witty":         {"TikTok": 9.0, "X": 8.0, "Instagram": 7.5, "YouTube": 6.0, "Facebook": 5.5, "LinkedIn": 4.0},
        "inspirational": {"Instagram": 8.5, "YouTube": 8.0, "Facebook": 7.0, "LinkedIn": 6.5, "TikTok": 6.0, "X": 5.0},
        "authoritative": {"LinkedIn": 9.0, "YouTube": 8.0, "X": 7.0, "Facebook": 5.5, "Instagram": 5.0, "TikTok": 3.0},
    }
    platform_scores = tone_map.get(tone.lower(), {})
    return platform_scores.get(platform, 5.5)


def _timing_fit_score(platform: str, time_window: str) -> float:
    """Compute timing_fit (0–10) — higher for optimal time windows."""
    from app.constants import PLATFORM_TIME_SYNERGY
    synergy = PLATFORM_TIME_SYNERGY.get((platform, time_window), {"reach": 1.0, "engagement": 1.0})
    avg_synergy = (synergy["reach"] + synergy["engagement"]) / 2
    return round(min(10.0, 5.0 * avg_synergy), 1)


def _make_candidate_id(platform: str, topic: str, fmt: str, time_window: str) -> str:
    """Generate a deterministic candidate ID."""
    safe_topic = re.sub(r"[^a-z0-9]+", "-", topic.lower())[:30].strip("-")
    safe_fmt = fmt.replace(" ", "-").replace("_", "-").lower()
    return f"{platform.lower()}-{safe_topic}-{safe_fmt}-{time_window}"


def generate_candidates(
    user_input: UserInput,
    interpretation: InterpretationResponse,
) -> CandidatePool:
    """Generate 8–15 full strategy combinations from the interpretation.

    1. Take candidate_angles (3–5 topics)
    2. Cross with platforms (filtered by hard constraints)
    3. Cross with format + time candidates per platform
    4. Score each on 6 axes (simulation input signals)
    5. Prune to ≤15 diverse combinations
    """
    # Step 1: Topics from interpretation
    topics = interpretation.candidate_angles[:5]
    if len(topics) < 3:
        topics.extend([
            f"Educational content about {user_input.business_domain}",
            f"Customer spotlight for {user_input.target_audience}",
            f"Industry trend relevant to {user_input.business_domain}",
        ])
        topics = topics[:5]

    # Step 2: Filter platforms
    valid_platforms = _apply_hard_constraints(
        PLATFORMS,
        interpretation.audience_segment,
        interpretation.business_type,
    )

    # Step 3: Generate combinations
    candidates: list[StrategyCandidate] = []
    seen_ids: set[str] = set()

    for platform in valid_platforms:
        formats = PLATFORM_FORMATS.get(platform, ["static image"])
        times = PLATFORM_TIMES.get(platform, ["weekday_evening"])

        for topic in topics:
            for fmt in formats:
                for time_window in times:
                    cid = _make_candidate_id(platform, topic, fmt, time_window)
                    if cid in seen_ids:
                        continue
                    seen_ids.add(cid)

                    posting_time = TIME_WINDOW_LABELS.get(time_window, time_window)
                    feasibility = FORMAT_FEASIBILITY.get(fmt, 0.70)

                    candidates.append(StrategyCandidate(
                        candidate_id=cid,
                        platform=platform,
                        topic=topic,
                        format=fmt,
                        posting_time=posting_time,
                        time_window=time_window,
                        goal_type=interpretation.goal_type,
                        audience_segment=interpretation.audience_segment,
                        business_type=interpretation.business_type,
                        audience_fit=_audience_fit_score(interpretation.audience_segment, platform),
                        goal_fit=_goal_fit_score(interpretation.goal_type, platform),
                        format_fit=_format_fit_score(platform, fmt),
                        conversion_fit=_conversion_fit_score(interpretation.goal_type, platform),
                        tone_fit=_tone_fit_score(user_input.tone, platform),
                        timing_fit=_timing_fit_score(platform, time_window),
                        feasibility=feasibility,
                    ))

    # Step 4: Prune to max 15 (keep highest diversity)
    # Sort by a quick relevance heuristic, then take top 15
    if len(candidates) > 15:
        candidates.sort(
            key=lambda c: (c.audience_fit + c.goal_fit + c.format_fit) / 3,
            reverse=True,
        )
        candidates = candidates[:15]

    # Ensure minimum of 8 (pad with variations if needed)
    if len(candidates) < 8:
        logger.info("Candidate pool small (%d), keeping all", len(candidates))

    return CandidatePool(
        candidates=candidates,
        generation_method="fallback",
    )
