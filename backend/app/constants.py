"""Strategent v3 — Central constants for simulation, scoring, and decision logic.

All interaction matrices, benchmarks, weight profiles, and thresholds live here.
No service logic — only data.
"""

import math

# ═══════════════════════════════════════════════════════════════════════════
#  PLATFORM BENCHMARKS — ceilings for saturation curves
# ═══════════════════════════════════════════════════════════════════════════
PLATFORM_BENCHMARKS: dict[str, dict[str, float]] = {
    "LinkedIn":  {"reach_ceiling": 8_000,  "engagement_ceiling": 5.5,  "conversion_ceiling": 6.0},
    "X":         {"reach_ceiling": 6_000,  "engagement_ceiling": 3.5,  "conversion_ceiling": 3.0},
    "Instagram": {"reach_ceiling": 12_000, "engagement_ceiling": 7.5,  "conversion_ceiling": 5.0},
    "TikTok":    {"reach_ceiling": 50_000, "engagement_ceiling": 16.0, "conversion_ceiling": 2.5},
    "Facebook":  {"reach_ceiling": 4_000,  "engagement_ceiling": 4.5,  "conversion_ceiling": 4.0},
    "YouTube":   {"reach_ceiling": 25_000, "engagement_ceiling": 9.0,  "conversion_ceiling": 4.5},
}


# ═══════════════════════════════════════════════════════════════════════════
#  PLATFORM × FORMAT INTERACTION MATRIX
# ═══════════════════════════════════════════════════════════════════════════
# Multiplier applied to format_fit BEFORE simulation.
# > 1.0 = synergy, < 1.0 = friction.
PLATFORM_FORMAT_SYNERGY: dict[tuple[str, str], float] = {
    # Instagram
    ("Instagram", "carousel"):          1.25,
    ("Instagram", "short-form video"):  1.15,
    ("Instagram", "static image"):      0.95,
    ("Instagram", "long-form video"):   0.70,
    ("Instagram", "infographic"):       1.00,
    # TikTok
    ("TikTok", "short-form video"):     1.40,
    ("TikTok", "carousel"):             0.60,
    ("TikTok", "static image"):         0.50,
    ("TikTok", "long-form video"):      0.75,
    # LinkedIn
    ("LinkedIn", "long-form text"):     1.30,
    ("LinkedIn", "carousel"):           1.10,
    ("LinkedIn", "short-form video"):   0.80,
    ("LinkedIn", "static image"):       0.90,
    ("LinkedIn", "infographic"):        1.15,
    # Facebook
    ("Facebook", "short-form video"):   1.15,
    ("Facebook", "carousel"):           1.05,
    ("Facebook", "static image"):       0.90,
    ("Facebook", "long-form video"):    0.85,
    # YouTube
    ("YouTube", "long-form video"):     1.35,
    ("YouTube", "short-form video"):    1.10,
    ("YouTube", "static image"):        0.40,
    ("YouTube", "carousel"):            0.50,
    # X (Twitter)
    ("X", "static image"):              1.10,
    ("X", "short-form video"):          1.05,
    ("X", "long-form text"):            0.95,
    ("X", "carousel"):                  0.80,
}


# ═══════════════════════════════════════════════════════════════════════════
#  PLATFORM × GOAL INTERACTION MATRIX
# ═══════════════════════════════════════════════════════════════════════════
PLATFORM_GOAL_SYNERGY: dict[tuple[str, str], float] = {
    # Conversion
    ("Instagram", "conversion"):        1.20,
    ("LinkedIn", "conversion"):         1.15,
    ("Facebook", "conversion"):         1.10,
    ("TikTok", "conversion"):           0.65,
    ("YouTube", "conversion"):          0.90,
    ("X", "conversion"):                0.75,
    # Awareness
    ("TikTok", "awareness"):            1.40,
    ("Instagram", "awareness"):         1.20,
    ("YouTube", "awareness"):           1.15,
    ("X", "awareness"):                 1.05,
    ("LinkedIn", "awareness"):          0.70,
    ("Facebook", "awareness"):          0.85,
    # Lead generation
    ("LinkedIn", "lead-generation"):    1.45,
    ("YouTube", "lead-generation"):     1.10,
    ("Facebook", "lead-generation"):    1.00,
    ("Instagram", "lead-generation"):   0.80,
    ("TikTok", "lead-generation"):      0.50,
    ("X", "lead-generation"):           0.90,
    # Engagement
    ("TikTok", "engagement"):           1.35,
    ("Instagram", "engagement"):        1.25,
    ("YouTube", "engagement"):          1.10,
    ("Facebook", "engagement"):         1.00,
    ("X", "engagement"):                1.05,
    ("LinkedIn", "engagement"):         0.75,
    # Traffic
    ("X", "traffic"):                   1.15,
    ("YouTube", "traffic"):             1.10,
    ("LinkedIn", "traffic"):            1.05,
    ("Facebook", "traffic"):            1.00,
    ("Instagram", "traffic"):           0.90,
    ("TikTok", "traffic"):              0.80,
    # Retention
    ("Facebook", "retention"):          1.20,
    ("Instagram", "retention"):         1.10,
    ("YouTube", "retention"):           1.10,
    ("LinkedIn", "retention"):          1.00,
    ("X", "retention"):                 0.85,
    ("TikTok", "retention"):            0.70,
}


# ═══════════════════════════════════════════════════════════════════════════
#  AUDIENCE × PLATFORM INTERACTION
# ═══════════════════════════════════════════════════════════════════════════
# Key is an audience keyword, value is per-platform multiplier.
AUDIENCE_PLATFORM_SYNERGY: dict[str, dict[str, float]] = {
    "b2b":           {"LinkedIn": 1.40, "X": 1.10, "YouTube": 1.00, "Facebook": 0.70, "Instagram": 0.60, "TikTok": 0.45},
    "local":         {"Facebook": 1.35, "Instagram": 1.15, "YouTube": 0.90, "LinkedIn": 0.80, "X": 0.75, "TikTok": 0.70},
    "youth":         {"TikTok": 1.40, "Instagram": 1.20, "YouTube": 1.10, "X": 0.80, "Facebook": 0.60, "LinkedIn": 0.40},
    "professional":  {"LinkedIn": 1.35, "X": 1.15, "YouTube": 1.00, "Instagram": 0.75, "Facebook": 0.70, "TikTok": 0.50},
    "family":        {"Facebook": 1.30, "Instagram": 1.15, "YouTube": 1.10, "TikTok": 0.85, "LinkedIn": 0.50, "X": 0.60},
    "enterprise":    {"LinkedIn": 1.45, "X": 1.10, "YouTube": 1.00, "Facebook": 0.60, "Instagram": 0.50, "TikTok": 0.35},
}


# ═══════════════════════════════════════════════════════════════════════════
#  PLATFORM × TIME SYNERGY
# ═══════════════════════════════════════════════════════════════════════════
PLATFORM_TIME_SYNERGY: dict[tuple[str, str], dict[str, float]] = {
    # Instagram
    ("Instagram", "weekday_morning"):    {"reach": 1.05, "engagement": 0.90},
    ("Instagram", "weekday_midday"):     {"reach": 1.10, "engagement": 1.05},
    ("Instagram", "weekday_evening"):    {"reach": 1.15, "engagement": 1.25},
    ("Instagram", "weekend_morning"):    {"reach": 1.20, "engagement": 1.15},
    ("Instagram", "weekend_evening"):    {"reach": 1.10, "engagement": 1.10},
    # TikTok
    ("TikTok", "weekday_morning"):       {"reach": 0.80, "engagement": 0.75},
    ("TikTok", "weekday_midday"):        {"reach": 0.95, "engagement": 0.90},
    ("TikTok", "weekday_evening"):       {"reach": 1.25, "engagement": 1.30},
    ("TikTok", "weekend_morning"):       {"reach": 1.05, "engagement": 1.10},
    ("TikTok", "weekend_evening"):       {"reach": 1.30, "engagement": 1.35},
    # LinkedIn
    ("LinkedIn", "weekday_morning"):     {"reach": 1.30, "engagement": 1.25},
    ("LinkedIn", "weekday_midday"):      {"reach": 1.15, "engagement": 1.10},
    ("LinkedIn", "weekday_evening"):     {"reach": 0.80, "engagement": 0.75},
    ("LinkedIn", "weekend_morning"):     {"reach": 0.60, "engagement": 0.55},
    ("LinkedIn", "weekend_evening"):     {"reach": 0.50, "engagement": 0.45},
    # Facebook
    ("Facebook", "weekday_morning"):     {"reach": 1.05, "engagement": 0.95},
    ("Facebook", "weekday_midday"):      {"reach": 1.15, "engagement": 1.10},
    ("Facebook", "weekday_evening"):     {"reach": 1.10, "engagement": 1.15},
    ("Facebook", "weekend_morning"):     {"reach": 1.20, "engagement": 1.20},
    ("Facebook", "weekend_evening"):     {"reach": 1.05, "engagement": 1.00},
    # YouTube
    ("YouTube", "weekday_morning"):      {"reach": 0.85, "engagement": 0.80},
    ("YouTube", "weekday_midday"):       {"reach": 1.00, "engagement": 0.95},
    ("YouTube", "weekday_evening"):      {"reach": 1.10, "engagement": 1.15},
    ("YouTube", "weekend_morning"):      {"reach": 1.15, "engagement": 1.10},
    ("YouTube", "weekend_evening"):      {"reach": 1.25, "engagement": 1.25},
    # X
    ("X", "weekday_morning"):            {"reach": 1.20, "engagement": 1.15},
    ("X", "weekday_midday"):             {"reach": 1.15, "engagement": 1.10},
    ("X", "weekday_evening"):            {"reach": 0.95, "engagement": 0.90},
    ("X", "weekend_morning"):            {"reach": 0.80, "engagement": 0.75},
    ("X", "weekend_evening"):            {"reach": 0.85, "engagement": 0.80},
}


# ═══════════════════════════════════════════════════════════════════════════
#  FORMAT FEASIBILITY & COMPLEXITY
# ═══════════════════════════════════════════════════════════════════════════
FORMAT_FEASIBILITY: dict[str, float] = {
    "static image":       0.95,
    "long-form text":     0.90,
    "carousel":           0.80,
    "infographic":        0.75,
    "short-form video":   0.55,
    "long-form video":    0.35,
    "live stream":        0.30,
}

FORMAT_COMPLEXITY: dict[str, float] = {
    "static image":       0.05,
    "long-form text":     0.08,
    "carousel":           0.12,
    "infographic":        0.15,
    "short-form video":   0.20,
    "long-form video":    0.30,
    "live stream":        0.35,
}

COMPLEXITY_FACTOR = 0.12


def compute_complexity_penalty(format_type: str) -> float:
    """Returns a multiplier in [0.92, 1.0]."""
    complexity = FORMAT_COMPLEXITY.get(format_type, 0.10)
    return round(max(0.92, 1.0 - complexity * COMPLEXITY_FACTOR), 4)


# ═══════════════════════════════════════════════════════════════════════════
#  GOAL-ADAPTIVE WEIGHT PROFILES
# ═══════════════════════════════════════════════════════════════════════════
GOAL_WEIGHT_PROFILES: dict[str, dict[str, float]] = {
    "conversion": {
        "conversion": 0.55, "reach": 0.15, "engagement": 0.10,
        "feasibility": 0.10, "confidence": 0.10,
    },
    "awareness": {
        "conversion": 0.10, "reach": 0.45, "engagement": 0.25,
        "feasibility": 0.10, "confidence": 0.10,
    },
    "lead-generation": {
        "conversion": 0.45, "reach": 0.20, "engagement": 0.10,
        "feasibility": 0.15, "confidence": 0.10,
    },
    "engagement": {
        "conversion": 0.10, "reach": 0.20, "engagement": 0.45,
        "feasibility": 0.10, "confidence": 0.15,
    },
    "traffic": {
        "conversion": 0.15, "reach": 0.40, "engagement": 0.20,
        "feasibility": 0.15, "confidence": 0.10,
    },
    "retention": {
        "conversion": 0.20, "reach": 0.10, "engagement": 0.40,
        "feasibility": 0.15, "confidence": 0.15,
    },
}

DEFAULT_WEIGHT_PROFILE: dict[str, float] = {
    "conversion": 0.35, "reach": 0.25, "engagement": 0.15,
    "feasibility": 0.10, "confidence": 0.15,
}


# ═══════════════════════════════════════════════════════════════════════════
#  6-AXIS SCORING WEIGHTS (signal scoring — feeds simulation)
# ═══════════════════════════════════════════════════════════════════════════
SCORE_WEIGHTS: dict[str, float] = {
    "audience_fit":   0.25,
    "goal_fit":       0.25,
    "format_fit":     0.20,
    "conversion_fit": 0.20,
    "tone_fit":       0.05,
    "timing_fit":     0.05,
}


# ═══════════════════════════════════════════════════════════════════════════
#  DECISION THRESHOLDS
# ═══════════════════════════════════════════════════════════════════════════
UNCERTAINTY_THRESHOLD = 0.50      # outcome_score gap for "low confidence"
HIGH_CONFIDENCE_THRESHOLD = 1.50  # gap for "high confidence"
EXPLORE_THRESHOLD = 0.35          # gap below which exploration is triggered
EXPLORE_SWAP_THRESHOLD = 0.15    # gap below which system swaps to runner-up
STAGNATION_LIMIT = 3              # max consecutive wins before forced exploration
QUALITY_THRESHOLD = 0.60          # relative score below = pool is "low quality"
MINIMUM_VIABLE_SCORE = 4.5       # hard floor — below this = no viable strategy
MEMORY_DECAY_RATE = 0.98          # 2% decay per record-age position
TIME_SYNERGY_LEARNING_RATE = 0.02  # ±2% adjustment per feedback


# ═══════════════════════════════════════════════════════════════════════════
#  PLATFORM-FORMAT DEFAULTS (for candidate generation)
# ═══════════════════════════════════════════════════════════════════════════
PLATFORM_FORMATS: dict[str, list[str]] = {
    "Instagram":  ["carousel", "short-form video", "static image"],
    "TikTok":     ["short-form video"],
    "LinkedIn":   ["carousel", "long-form text", "static image"],
    "Facebook":   ["short-form video", "carousel", "static image"],
    "YouTube":    ["long-form video", "short-form video"],
    "X":          ["static image", "short-form video"],
}

PLATFORM_TIMES: dict[str, list[str]] = {
    "Instagram":  ["weekday_evening", "weekend_morning"],
    "TikTok":     ["weekday_evening", "weekend_evening"],
    "LinkedIn":   ["weekday_morning", "weekday_midday"],
    "Facebook":   ["weekday_midday", "weekend_morning"],
    "YouTube":    ["weekend_evening", "weekday_evening"],
    "X":          ["weekday_morning", "weekday_midday"],
}

PLATFORMS = ["Instagram", "TikTok", "LinkedIn", "Facebook", "YouTube", "X"]

TIME_WINDOW_LABELS: dict[str, str] = {
    "weekday_morning":  "Mon–Fri 6–11 AM",
    "weekday_midday":   "Mon–Fri 11 AM–3 PM",
    "weekday_evening":  "Mon–Fri 5–10 PM",
    "weekend_morning":  "Sat–Sun 8 AM–12 PM",
    "weekend_evening":  "Sat–Sun 4–10 PM",
}


# ═══════════════════════════════════════════════════════════════════════════
#  HARD CONSTRAINTS (pre-scoring filters)
# ═══════════════════════════════════════════════════════════════════════════
# Audience keywords that eliminate or penalize platforms
HARD_CONSTRAINT_EXCLUDES: dict[str, list[str]] = {
    "b2b":     ["TikTok", "Instagram"],
    "enterprise": ["TikTok", "Instagram"],
    "45+":     ["TikTok"],
    "50+":     ["TikTok"],
    "senior":  ["TikTok"],
}


# ═══════════════════════════════════════════════════════════════════════════
#  SATURATION FUNCTION
# ═══════════════════════════════════════════════════════════════════════════
def saturate(signal: float, ceiling: float, steepness: float = 0.25) -> float:
    """Logarithmic saturation — diminishing returns as signal approaches 10.

    signal:    raw composite score (typically 0–10 range after weighting)
    ceiling:   maximum output value (platform-specific)
    steepness: controls how fast growth slows

    Returns a value in [0, ceiling) that grows quickly at low signal
    and flattens near the ceiling.
    """
    normalized = max(0.0, signal) / 10.0
    return ceiling * (1 - math.exp(-steepness * normalized * 10))
