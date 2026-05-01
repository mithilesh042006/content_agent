"""Content generation agent service — conversion-focused copy."""

import logging

from app.schemas.common import UserInput
from app.schemas.interpretation import InterpretationResponse
from app.schemas.content import ContentResponse
from app.prompts.content_prompt import CONTENT_SYSTEM_PROMPT, build_content_user_prompt
from app.services.llm_service import invoke_structured

logger = logging.getLogger(__name__)


def _goal_matched_cta(business_domain: str, content_goal: str) -> str:
    """Map the content_goal to a goal-matched CTA verb (fallback only)."""
    g = content_goal.lower()
    if any(k in g for k in ("sign", "signup", "register", "subscribe", "waitlist")):
        return f"Sign up today and start with {business_domain}."
    if any(k in g for k in ("sales", "sell", "buy", "purchase", "customer", "revenue", "shop")):
        return f"Shop {business_domain} today — your next order is waiting."
    if any(k in g for k in ("lead", "demo", "book", "contact", "meeting")):
        return f"Book a free demo of {business_domain} this week."
    if any(k in g for k in ("traffic", "visits", "clicks", "readers")):
        return f"Visit {business_domain} for the full guide."
    if any(k in g for k in ("awareness", "brand", "followers", "reach")):
        return f"Follow {business_domain} for more on this."
    return f"Act today with {business_domain}."


def _fallback_content(
    user_input: UserInput,
    topic: str,
    platform: str,
    interpretation: InterpretationResponse | None = None,
) -> ContentResponse:
    """Template fallback — still conversion-scaffolded (hook → pain → value → proof → CTA)."""
    audience = (
        interpretation.audience_segment if interpretation
        else user_input.target_audience
    )
    goal_type = interpretation.goal_type if interpretation else "conversion"

    cta = _goal_matched_cta(user_input.business_domain, user_input.content_goal)

    # Goal-type specific copy framing
    if goal_type == "awareness":
        value_line = f"— A fresh perspective on {topic} that changes how you think about {user_input.business_domain}"
        proof_line = f"Thousands of {audience} are already seeing the difference."
    elif goal_type == "lead-generation":
        value_line = f"— A free resource that solves your {user_input.content_goal} challenge"
        proof_line = f"Join other {audience} who've already signed up."
    elif goal_type == "retention":
        value_line = f"— An insider benefit exclusively for existing {user_input.business_domain} users"
        proof_line = f"Loyal customers are already unlocking these results."
    else:  # conversion, traffic, engagement
        value_line = f"— A direct fix for your {user_input.content_goal} challenge"
        proof_line = (
            f"Teams in {user_input.business_domain} that move first on this are the ones "
            f"compounding results this quarter."
        )

    return ContentResponse(
        headline=f"The {topic} playbook built for {audience}",
        post_copy=(
            f"If you're a {audience} in {user_input.business_domain}, "
            f"you already feel this: {topic} is harder than it should be.\n\n"
            f"Here's what our approach changes:\n"
            f"{value_line}\n"
            f"— Benefits you can measure inside a week\n"
            f"— No fluff, no guesswork, no wasted spend\n\n"
            f"{proof_line}"
        ),
        cta=cta,
        hashtags=[
            user_input.business_domain.replace(" ", ""),
            "Conversion",
            "ContentStrategy",
            platform.replace(" ", ""),
            "Growth",
        ],
    )


def run_content(
    user_input: UserInput,
    topic: str,
    platform: str,
    interpretation: InterpretationResponse | None = None,
) -> ContentResponse:
    """Execute the content generation agent — LLM with structured output, fallback on failure."""
    # Build prompt with interpretation context if available
    extra_kwargs = {}
    if interpretation:
        extra_kwargs.update(
            goal_type=interpretation.goal_type,
            audience_segment=interpretation.audience_segment,
            inferred_content_objective=interpretation.inferred_content_objective,
        )

    user_prompt = build_content_user_prompt(
        business_domain=user_input.business_domain,
        content_goal=user_input.content_goal,
        target_audience=user_input.target_audience,
        tone=user_input.tone,
        topic=topic,
        platform=platform,
        **extra_kwargs,
    )

    result = invoke_structured(
        system_prompt=CONTENT_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        schema=ContentResponse,
    )

    if result is not None:
        return result

    logger.info("Using fallback content generation")
    return _fallback_content(user_input, topic, platform, interpretation)
