"""Brief interpretation agent service — Layer A of the reasoning pipeline."""

import logging

from app.schemas.common import UserInput
from app.schemas.interpretation import InterpretationResponse
from app.prompts.interpretation_prompt import (
    INTERPRETATION_SYSTEM_PROMPT,
    build_interpretation_user_prompt,
)
from app.services.llm_service import invoke_structured

logger = logging.getLogger(__name__)

# ── Goal-type keyword mapping (used only by the fallback) ────────────────
_GOAL_KEYWORDS: dict[str, list[str]] = {
    "conversion": [
        "sales", "sell", "buy", "purchase", "revenue", "customer",
        "shopper", "order", "store", "shop",
    ],
    "awareness": [
        "awareness", "brand", "followers", "reach", "visibility",
        "impressions", "recognition",
    ],
    "lead-generation": [
        "signup", "sign up", "register", "subscribe", "waitlist",
        "demo", "trial", "lead", "booking", "book",
    ],
    "retention": [
        "loyalty", "churn", "repeat", "retain", "retention",
        "comeback", "returning",
    ],
    "traffic": [
        "traffic", "visits", "click", "page view", "readers", "site",
    ],
    "engagement": [
        "engage", "comment", "share", "community", "discussion",
        "interact",
    ],
}

# ── Business-type keyword mapping (used only by the fallback) ────────────
_BUSINESS_KEYWORDS: dict[str, list[str]] = {
    "local retail": [
        "shop", "store", "grocery", "bakery", "boutique", "pharmacy",
        "restaurant", "cafe", "salon", "florist",
    ],
    "B2B SaaS": [
        "saas", "platform", "api", "enterprise", "b2b", "software",
        "cloud", "tool", "solution", "crm",
    ],
    "DTC e-commerce": [
        "e-commerce", "ecommerce", "dtc", "d2c", "online store",
        "dropship", "shopify", "woocommerce",
    ],
    "education platform": [
        "education", "course", "tutorial", "learning", "edtech",
        "academy", "school", "university", "training",
    ],
    "healthcare": [
        "health", "medical", "clinic", "hospital", "wellness",
        "therapy", "pharma", "telehealth", "fitness",
    ],
    "finance": [
        "fintech", "banking", "investment", "insurance", "finance",
        "trading", "crypto", "payments", "lending",
    ],
    "media / publishing": [
        "media", "news", "magazine", "blog", "podcast", "publishing",
        "content", "journalism",
    ],
    "professional services": [
        "consulting", "agency", "freelance", "legal", "accounting",
        "advisory", "coaching",
    ],
}


def _infer_goal_type(text: str) -> str:
    """Match the content goal text against known goal keywords."""
    lower = text.lower()
    best, best_hits = "conversion", 0  # default
    for goal_type, keywords in _GOAL_KEYWORDS.items():
        hits = sum(1 for kw in keywords if kw in lower)
        if hits > best_hits:
            best, best_hits = goal_type, hits
    return best


def _infer_business_type(text: str) -> str:
    """Match the business domain text against known business keywords."""
    lower = text.lower()
    best, best_hits = "general business", 0
    for biz_type, keywords in _BUSINESS_KEYWORDS.items():
        hits = sum(1 for kw in keywords if kw in lower)
        if hits > best_hits:
            best, best_hits = biz_type, hits
    return best


def _refine_audience(raw_audience: str, domain: str) -> tuple[str, float]:
    """Refine a vague audience description into a more specific segment.

    Returns (refined_segment, confidence).
    """
    lower = raw_audience.lower().strip()

    # Already specific enough
    specificity_signals = [
        "aged", "age", "year-old", "professional", "founder", "cto",
        "developer", "manager", "parent", "student", "entrepreneur",
        "budget", "income", "urban", "rural",
    ]
    if any(sig in lower for sig in specificity_signals):
        return raw_audience, 0.90

    # Very vague → refine with domain context
    vague_tokens = ["people", "everyone", "anyone", "general", "all", "users", "customers"]
    is_vague = any(tok in lower for tok in vague_tokens) or len(lower) < 12

    domain_lower = domain.lower()
    if is_vague:
        if any(kw in domain_lower for kw in ["grocery", "food", "restaurant", "bakery", "cafe"]):
            return "budget-conscious family shoppers aged 28–45", 0.55
        if any(kw in domain_lower for kw in ["saas", "software", "api", "platform", "b2b"]):
            return "startup founders and engineering leads aged 25–40", 0.50
        if any(kw in domain_lower for kw in ["education", "course", "learning"]):
            return "self-directed learners and career-switchers aged 22–35", 0.50
        if any(kw in domain_lower for kw in ["health", "fitness", "wellness"]):
            return "health-conscious urban professionals aged 25–40", 0.50
        if any(kw in domain_lower for kw in ["fashion", "beauty", "lifestyle"]):
            return "trend-aware women aged 18–34 who follow lifestyle influencers", 0.50
        if any(kw in domain_lower for kw in ["finance", "fintech", "invest"]):
            return "financially active young professionals aged 25–40", 0.50
        # Generic fallback
        return f"digitally active adults aged 22–45 interested in {domain}", 0.40

    # Moderately specific — minor refinement
    return f"{raw_audience} (primarily aged 22–40, digitally active)", 0.70


def _generate_candidate_angles(
    domain: str, goal_type: str, audience: str,
) -> list[str]:
    """Generate 3–5 domain-appropriate candidate content angles."""
    angles = []

    # Goal-driven angles
    if goal_type == "conversion":
        angles.extend([
            f"Limited-time offer or flash deal for {audience}",
            f"Customer success story showing results with {domain}",
            f"Side-by-side comparison: {domain} vs the status quo",
        ])
    elif goal_type == "awareness":
        angles.extend([
            f"Behind-the-scenes look at how {domain} operates",
            f"Industry trend analysis relevant to {audience}",
            f"Myth-busting: common misconceptions about {domain}",
        ])
    elif goal_type == "lead-generation":
        angles.extend([
            f"Free resource or toolkit for {audience}",
            f"Quick-win tutorial that previews {domain}'s value",
            f"Expert Q&A addressing top pain points of {audience}",
        ])
    elif goal_type == "retention":
        angles.extend([
            f"Insider tips that only existing {domain} users know",
            f"Loyalty reward or exclusive offer for repeat customers",
            f"User milestone celebration or community spotlight",
        ])
    elif goal_type == "traffic":
        angles.extend([
            f"Detailed guide with a teaser leading to {domain}",
            f"Curated list or roundup relevant to {audience}",
            f"Data-driven insight with full analysis on the site",
        ])
    else:  # engagement
        angles.extend([
            f"Poll or debate question relevant to {audience}",
            f"User-generated content challenge around {domain}",
            f"Controversial take on a topic that matters to {audience}",
        ])

    # Always add a seasonal/timely angle
    angles.append(f"Seasonal or timely hook tied to current events and {domain}")

    return angles[:5]


def _fallback_interpretation(user_input: UserInput) -> InterpretationResponse:
    """Rule-based fallback interpretation when the LLM is unavailable."""
    business_type = _infer_business_type(user_input.business_domain)
    goal_type = _infer_goal_type(user_input.content_goal)
    audience_segment, confidence = _refine_audience(
        user_input.target_audience, user_input.business_domain,
    )
    candidate_angles = _generate_candidate_angles(
        user_input.business_domain, goal_type, audience_segment,
    )

    objective_map = {
        "conversion": f"drive purchases / revenue via targeted content for {audience_segment}",
        "awareness": f"increase brand visibility and reach among {audience_segment}",
        "lead-generation": f"capture leads and signups from {audience_segment}",
        "retention": f"deepen loyalty and repeat engagement from {audience_segment}",
        "traffic": f"drive qualified traffic to {user_input.business_domain} from {audience_segment}",
        "engagement": f"spark meaningful interaction with {audience_segment}",
    }

    return InterpretationResponse(
        business_type=business_type,
        goal_type=goal_type,
        audience_segment=audience_segment,
        audience_inference_confidence=confidence,
        inferred_content_objective=objective_map.get(
            goal_type,
            f"achieve {user_input.content_goal} for {audience_segment}",
        ),
        candidate_angles=candidate_angles,
        reasoning_trace=(
            f"Business domain '{user_input.business_domain}' mapped to business type "
            f"'{business_type}' via keyword matching. Content goal "
            f"'{user_input.content_goal}' classified as '{goal_type}'. "
            f"Audience '{user_input.target_audience}' refined to "
            f"'{audience_segment}' with confidence {confidence:.0%}. "
            f"(Fallback: LLM unavailable.)"
        ),
    )


def run_interpretation(user_input: UserInput) -> InterpretationResponse:
    """Execute the brief interpretation agent — LLM with structured output, fallback on failure."""
    user_prompt = build_interpretation_user_prompt(
        business_domain=user_input.business_domain,
        content_goal=user_input.content_goal,
        target_audience=user_input.target_audience,
        tone=user_input.tone,
    )

    result = invoke_structured(
        system_prompt=INTERPRETATION_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        schema=InterpretationResponse,
    )

    if result is not None:
        return result

    logger.info("Using fallback interpretation logic")
    return _fallback_interpretation(user_input)
