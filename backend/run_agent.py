"""Strategent v3 — CLI runner for the simulation-first pipeline.

Usage:
    python run_agent.py                       # Interactive — prompts for input
    python run_agent.py --sample              # Runs with a sample brief
    python run_agent.py --business "SaaS" --goal "drive signups" --audience "developers" --tone "witty"
"""

import argparse
import json
import logging
import sys
import os

# Force UTF-8 output on Windows
if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

# Add parent to path for app imports
sys.path.insert(0, os.path.dirname(__file__))

from app.schemas.common import UserInput
from app.services.interpretation_service import run_interpretation
from app.services.candidate_service import generate_candidates
from app.services.simulation_service import simulate_all
from app.services.decision_service import run_decision
from app.services.explainer_service import run_explanation
from app.services.content_service import run_content
from app.services.feedback_service import run_feedback
from app.schemas.feedback import FeedbackRequest
from app.schemas.explanation import ExplanationResponse
from app.schemas.content import ContentResponse
from app.schemas.feedback import FeedbackResponse

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

# ── Color helpers ────────────────────────────────────────────────────────
BOLD = "\033[1m"
DIM = "\033[2m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
CYAN = "\033[96m"
MAGENTA = "\033[95m"
RESET = "\033[0m"


def heading(text: str) -> str:
    return f"\n{BOLD}{CYAN}{'═' * 70}{RESET}\n{BOLD}{CYAN}  {text}{RESET}\n{BOLD}{CYAN}{'═' * 70}{RESET}"


def subheading(text: str) -> str:
    return f"\n{BOLD}{MAGENTA}── {text} {'─' * max(0, 60 - len(text))}{RESET}"


def kv(key: str, value, color: str = "") -> str:
    return f"  {DIM}{key}:{RESET} {color}{value}{RESET}"


def main():
    parser = argparse.ArgumentParser(description="Strategent v3 — CLI Runner")
    parser.add_argument("--sample", action="store_true", help="Use sample input")
    parser.add_argument("--business", type=str, default="")
    parser.add_argument("--goal", type=str, default="")
    parser.add_argument("--audience", type=str, default="")
    parser.add_argument("--tone", type=str, default="professional")
    args = parser.parse_args()

    # ── Input ────────────────────────────────────────────────────
    if args.sample:
        user_input = UserInput(
            business_domain="Local grocery store chain",
            content_goal="Increase weekly foot traffic and in-store purchases",
            target_audience="Budget-conscious family shoppers aged 28–45",
            tone="casual",
        )
    elif args.business:
        user_input = UserInput(
            business_domain=args.business,
            content_goal=args.goal or "grow the business",
            target_audience=args.audience or "general audience",
            tone=args.tone,
        )
    else:
        print(heading("STRATEGENT v3 — Adaptive Strategy Engine"))
        bd = input(f"  {CYAN}Business domain:{RESET} ").strip() or "Local coffee shop"
        cg = input(f"  {CYAN}Content goal:{RESET} ").strip() or "Drive foot traffic"
        ta = input(f"  {CYAN}Target audience:{RESET} ").strip() or "Young professionals"
        tone = input(f"  {CYAN}Tone:{RESET} ").strip() or "casual"
        user_input = UserInput(
            business_domain=bd, content_goal=cg,
            target_audience=ta, tone=tone,
        )

    print(heading("STRATEGENT v3 — PIPELINE"))
    print(kv("Business", user_input.business_domain))
    print(kv("Goal", user_input.content_goal))
    print(kv("Audience", user_input.target_audience))
    print(kv("Tone", user_input.tone))

    # ── Stage 1: Interpret ───────────────────────────────────────
    print(subheading("§1 INTERPRETATION"))
    interpretation = run_interpretation(user_input)
    print(kv("Business type", interpretation.business_type))
    print(kv("Goal type", interpretation.goal_type, GREEN))
    print(kv("Audience", interpretation.audience_segment))
    print(kv("Confidence", f"{interpretation.audience_inference_confidence:.0%}"))
    print(kv("Objective", interpretation.inferred_content_objective))
    print(kv("Angles", ""))
    for i, angle in enumerate(interpretation.candidate_angles, 1):
        print(f"    {DIM}{i}.{RESET} {angle}")
    print(kv("Trace", interpretation.reasoning_trace[:120] + "..."))

    # ── Stage 2: Generate Candidates ─────────────────────────────
    print(subheading("§2 CANDIDATES"))
    pool = generate_candidates(user_input, interpretation)
    print(kv("Count", len(pool.candidates)))
    print(kv("Method", pool.generation_method))
    print(f"\n  {'ID':<45} {'Platform':<12} {'Format':<18} {'AudFit':>6} {'GoalFit':>7} {'FmtFit':>6} {'ConvFit':>7}")
    print(f"  {'-'*45} {'-'*12} {'-'*18} {'-'*6} {'-'*7} {'-'*6} {'-'*7}")
    for c in pool.candidates[:12]:
        cid_short = c.candidate_id[:44]
        print(
            f"  {cid_short:<45} {c.platform:<12} {c.format:<18} "
            f"{c.audience_fit:>6.1f} {c.goal_fit:>7.1f} {c.format_fit:>6.1f} {c.conversion_fit:>7.1f}"
        )
    if len(pool.candidates) > 12:
        print(f"  {DIM}... +{len(pool.candidates) - 12} more{RESET}")

    # ── Stage 3: Simulate ALL ────────────────────────────────────
    print(subheading("§3 SIMULATION (all candidates)"))
    simulation = simulate_all(pool.candidates)
    print(f"\n  {'#':>3} {'Platform':<12} {'Format':<18} {'Score':>6} {'Reach':>8} {'Eng%':>6} {'Conv%':>6} {'Conf':>6} {'Feas':>5}")
    print(f"  {'-'*3} {'-'*12} {'-'*18} {'-'*6} {'-'*8} {'-'*6} {'-'*6} {'-'*6} {'-'*5}")
    for i, sc in enumerate(simulation.all_candidates[:15], 1):
        marker = f"{GREEN}→{RESET}" if i == 1 else " "
        print(
            f" {marker}{i:>2} {sc.platform:<12} {sc.format:<18} "
            f"{sc.outcome_score:>6.2f} {sc.predicted_reach:>8,} "
            f"{sc.predicted_engagement:>5.1f}% {sc.predicted_conversion:>5.1f}% "
            f"{sc.confidence:>5.0%} {sc.feasibility:>5.2f}"
        )
    print(f"\n  {DIM}Comparison:{RESET} {simulation.comparison_summary}")
    for line in simulation.score_breakdown:
        print(f"    • {line}")

    # ── Stage 4: Decide ──────────────────────────────────────────
    print(subheading("§4 DECISION"))
    decision = run_decision(user_input, interpretation, simulation.all_candidates, pool)

    if decision.no_viable_strategy:
        print(f"  {RED}{BOLD}⚠ NO VIABLE STRATEGY{RESET}")
        print(kv("Reason", decision.reason))
        print(kv("Best score", f"{decision.outcome_score:.2f}"))
        print(kv("Quality warning", decision.quality_warning_reason))
        print(f"\n{YELLOW}Pipeline terminated — content and feedback skipped.{RESET}")
        return

    print(kv("Winner", f"{GREEN}{decision.platform} + {decision.format}{RESET}"))
    print(kv("Topic", decision.topic[:80]))
    print(kv("Outcome Score", f"{GREEN}{decision.outcome_score:.2f}{RESET}"))
    print(kv("Posting Time", decision.posting_time))
    print(kv("Pred. Reach", f"{decision.predicted_reach:,}"))
    print(kv("Pred. Engagement", f"{decision.predicted_engagement:.1f}%"))
    print(kv("Pred. Conversion", f"{decision.predicted_conversion:.1f}%"))
    print(kv("Confidence", f"{decision.decision_confidence} ({decision.confidence_score:.0%})"))
    print(kv("Relative Score", f"{decision.relative_score:.0%}"))

    if decision.uncertainty_flag:
        print(f"  {YELLOW}⚠ UNCERTAIN — top candidates are close{RESET}")

    if decision.strategy_quality_warning:
        print(f"  {YELLOW}⚠ QUALITY WARNING: {decision.quality_warning_reason}{RESET}")

    if decision.exploration_triggered:
        print(f"  {MAGENTA}🔍 EXPLORATION: {decision.exploration_reason}{RESET}")
        if decision.exploration_swapped:
            print(f"  {MAGENTA}↔ SWAPPED — original winner: {decision.original_winner_id}{RESET}")

    if decision.trade_off_analysis:
        ta = decision.trade_off_analysis
        print(subheading("Trade-off Analysis"))
        print(kv(ta.candidate_a, f"score {ta.candidate_a_score:.2f} (strength: {ta.candidate_a_strength})"))
        print(kv(ta.candidate_b, f"score {ta.candidate_b_score:.2f} (strength: {ta.candidate_b_strength})"))
        print(kv("Delta", f"{ta.delta:.2f}"))
        print(kv("Analysis", ta.trade_off))

    if decision.rejected:
        print(subheading("Top Rejected"))
        for r in decision.rejected[:5]:
            print(f"    ✗ {r.platform} ({r.format}): {r.outcome_score:.2f} — {r.reason[:80]}")

    # ── Stage 5: Explain ─────────────────────────────────────────
    print(subheading("§5 EXPLANATION"))
    explanation = run_explanation(decision, simulation.winner, simulation.runner_up, interpretation)
    decision.reason = explanation.reason
    decision.chosen_because = explanation.chosen_because
    print(kv("Reason", explanation.reason))
    print(kv("Chosen because", explanation.chosen_because))
    if explanation.trade_off_narrative:
        print(kv("Trade-off", explanation.trade_off_narrative))

    # ── Stage 6: Content ─────────────────────────────────────────
    print(subheading("§6 CONTENT"))
    content = run_content(user_input, decision.topic, decision.platform, interpretation)
    print(kv("Headline", f"{GREEN}{content.headline}{RESET}"))
    print(kv("Copy", content.post_copy[:200] + "..."))
    print(kv("CTA", f"{YELLOW}{content.cta}{RESET}"))
    print(kv("Hashtags", ", ".join(f"#{h}" for h in content.hashtags)))

    # ── Stage 7: Feedback ────────────────────────────────────────
    print(subheading("§7 FEEDBACK & LEARNING"))
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
        time_window=pool.candidates[0].time_window if pool.candidates else "",
        outcome_score=decision.outcome_score,
    )
    fb = run_feedback(feedback_request)
    print(kv("Actual Reach", f"{fb.actual_reach:,}"))
    print(kv("Actual Engagement", f"{fb.actual_engagement:.1f}%"))
    print(kv("Actual Conversion", f"{fb.actual_conversion:.1f}%"))
    print(kv("What worked", fb.what_worked))
    print(kv("What underperformed", fb.what_underperformed))
    print(kv("Why", fb.why_underperformed))
    print(kv("Next rec", fb.next_recommendation))
    print(kv("State version", f"v{fb.state_version}"))

    if fb.simulation_param_updates:
        print(subheading("Simulation Updates"))
        for category, deltas in fb.simulation_param_updates.items():
            for key, delta in deltas.items():
                sign = "+" if delta > 0 else ""
                color = GREEN if delta > 0 else RED
                print(f"    {category}.{key}: {color}{sign}{delta:.3f}{RESET}")

    # ── Formula Traceability ─────────────────────────────────────
    print(subheading("§ FORMULA TRACEABILITY (winner)"))
    fi = simulation.winner.formula_inputs
    print(kv("Goal profile", fi.goal_weight_profile))
    print(kv("Weights", json.dumps(fi.outcome_weights, indent=None)))
    print(kv("Format synergy", f"{fi.format_synergy:.2f}"))
    print(kv("Goal synergy", f"{fi.goal_synergy:.2f}"))
    print(kv("Audience synergy", f"{fi.audience_synergy:.2f}"))
    print(kv("Time reach", f"{fi.time_synergy_reach:.3f} (learned: {fi.time_learned_multiplier:.3f})"))
    print(kv("Time engagement", f"{fi.time_synergy_engagement:.3f}"))
    print(kv("Platform mult", f"{fi.platform_multiplier:.3f}"))
    print(kv("Format mult", f"{fi.format_multiplier:.3f}"))
    print(kv("CTA mult", f"{fi.cta_multiplier:.3f}"))
    print(kv("Memory boost", f"{fi.memory_boost:.3f}"))
    print(kv("Complexity penalty", f"{fi.complexity_penalty:.4f}"))
    print(kv("Signal consistency", f"{fi.signal_consistency:.3f}"))
    print(kv("Consistency mult", f"{fi.consistency_multiplier:.3f}"))

    print(f"\n{BOLD}{GREEN}✓ Pipeline complete{RESET}\n")


if __name__ == "__main__":
    main()
