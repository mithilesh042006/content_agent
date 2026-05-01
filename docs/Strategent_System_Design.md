# STRATEGENT
### Decision-Driven Strategy Engine — System Design Specification v2.0

> **BEFORE:** LLM that generates and justifies
> **AFTER:** System that calculates → decides → explains

---

## Table of Contents

- [STRATEGENT](#strategent)
    - [Decision-Driven Strategy Engine — System Design Specification v2.0](#decision-driven-strategy-engine--system-design-specification-v20)
  - [Table of Contents](#table-of-contents)
  - [1. Objective](#1-objective)
  - [2. System Pipeline](#2-system-pipeline)
  - [3. Component Specifications](#3-component-specifications)
    - [3.1 Brief Interpreter](#31-brief-interpreter)
    - [3.2 Candidate Generator](#32-candidate-generator)
    - [3.3 Strategy Engine (Core Logic)](#33-strategy-engine-core-logic)
      - [3.3.1 Objective Function](#331-objective-function)
      - [3.3.2 Scoring Dimensions](#332-scoring-dimensions)
      - [3.3.3 Hard Constraints](#333-hard-constraints)
      - [3.3.4 Trade-off Engine](#334-trade-off-engine)
    - [3.4 Decision Layer](#34-decision-layer)
    - [3.5 Content Generator](#35-content-generator)
    - [3.6 Simulation Engine](#36-simulation-engine)
    - [3.7 Feedback Engine](#37-feedback-engine)
    - [3.8 Memory Layer](#38-memory-layer)
  - [4. Master System Prompt](#4-master-system-prompt)
  - [5. Validation Rules](#5-validation-rules)
      - [Decision Quality](#decision-quality)
      - [Consistency](#consistency)
      - [Goal Alignment](#goal-alignment)
      - [Learning](#learning)
  - [6. Failure Modes](#6-failure-modes)
  - [7. Final Standard](#7-final-standard)
  - [8. Implementation Checklist](#8-implementation-checklist)
      - [Brief Interpreter](#brief-interpreter)
      - [Candidate Generator](#candidate-generator)
      - [Strategy Engine](#strategy-engine)
      - [Decision Layer](#decision-layer)
      - [Content Generator](#content-generator)
      - [Simulation Engine](#simulation-engine)
      - [Feedback Engine](#feedback-engine)
      - [Memory Layer](#memory-layer)

---

## 1. Objective

Strategent is a **decision-making engine**, not a content generator. Every output must be the result of calculated trade-offs, not intuition. The system optimizes for measurable business goals and produces explainable, consistent outputs that improve over time via feedback.

The system must:

- Optimize for quantifiable business goals
- Generate and compare multiple strategy candidates before deciding
- Apply explicit scoring with weighted dimensions
- Resolve trade-offs between competing options with documented reasoning
- Generate content **only after** a decision is locked
- Simulate predicted outcomes using calculated formulas
- Update internal weights based on actual vs predicted performance

---

## 2. System Pipeline

All inputs flow through a fixed 9-stage pipeline. **No stage may be skipped.**

```
INPUT → INTERPRETER → CANDIDATES → STRATEGY ENGINE → DECISION → CONTENT → SIMULATION → FEEDBACK → MEMORY
```

| Stage | Name | Role |
|-------|------|------|
| 1 | **Input** | Raw brief from user |
| 2 | **Brief Interpreter** | Normalize and structure input |
| 3 | **Candidate Generator** | Generate 3–5 options per dimension |
| 4 | **Strategy Engine** ⭐ | Score, rank, and select via trade-off |
| 5 | **Decision Layer** | Formalize decision and log rejections |
| 6 | **Content Generator** | Generate content from decision only |
| 7 | **Simulation Engine** | Predict metrics via formulas |
| 8 | **Feedback Engine** | Compare actuals, update weights |
| 9 | **Memory Layer** | Persist decisions and weight states |

> ⭐ The Strategy Engine is the core of the system. All other stages exist to feed it inputs or consume its outputs.

---

## 3. Component Specifications

---

### 3.1 Brief Interpreter

**Purpose:** Convert unstructured user input into normalized, structured variables. This stage does not generate content or make strategic choices — only normalizes and classifies.

**Input schema:**
```json
{
  "domain":   "grocery shop",
  "goal":     "increase sales",
  "audience": "budget-conscious home cooks",
  "tone":     "casual"
}
```

**Output schema:**
```json
{
  "business_type":    "local retail",
  "goal_type":        "conversion",
  "audience_segment": "budget-conscious families",
  "intent":           "drive store visits and purchases"
}
```

**Rules:**
- Normalize all vague inputs to a canonical value
- Infer missing fields from context — do not leave nulls
- **Do NOT generate any content or strategy at this stage**

---

### 3.2 Candidate Generator

**Purpose:** Expand the interpreted brief into multiple discrete options for each strategic dimension. Candidate generation is mandatory — the system must never select a strategy without first generating alternatives to compare.

**Output format:**
```json
{
  "topics":    ["weekly deals", "meal ideas", "product spotlight", "behind the scenes", "customer stories"],
  "platforms": ["Instagram", "Facebook", "TikTok", "WhatsApp Broadcast", "Google Business"],
  "formats":   ["short-form video", "carousel post", "static image"],
  "times":     ["Tue/Thu 6–8 PM", "Sat 10 AM–12 PM"]
}
```

> ⚠️ **CONSTRAINT:** Never skip candidate generation. A strategy selected without candidates is a guess, not a decision. Minimum: 3 topics, 3 platforms, 2 formats, 2 time windows.

---

### 3.3 Strategy Engine (Core Logic)

The Strategy Engine scores, ranks, and selects the optimal strategy from the candidate pool. It is the system's analytical core. All selection logic lives here.

---

#### 3.3.1 Objective Function

Every candidate is ultimately measured against a single composite objective score:

```
objective_score =
    0.40 × conversion_probability
  + 0.30 × reach_potential
  + 0.20 × audience_fit
  + 0.10 × feasibility
```

---

#### 3.3.2 Scoring Dimensions

Each candidate is scored across six independent dimensions on a **0–10 scale**:

| Dimension | Weight | Description |
|-----------|--------|-------------|
| `audience_fit` | 0.25 | How well the option matches the target audience segment |
| `goal_fit` | 0.25 | Direct alignment with the stated business objective |
| `format_fit` | 0.20 | Suitability of content format for the platform and audience |
| `conversion_fit` | 0.20 | Likelihood that the option drives the desired conversion action |
| `tone_fit` | 0.05 | Consistency with the brief's specified tone |
| `timing_fit` | 0.05 | Appropriateness of posting time for audience behavior |

**Weighted score formula:**
```
weighted_score =
    0.25 × audience_fit
  + 0.25 × goal_fit
  + 0.20 × format_fit
  + 0.20 × conversion_fit
  + 0.05 × tone_fit
  + 0.05 × timing_fit
```

---

#### 3.3.3 Hard Constraints

Apply these rules **before** scoring. They adjust weights or eliminate candidates:

```
IF goal = conversion         → multiply conversion_fit weight by 1.5
IF audience = local          → reduce TikTok platform score by 30%
IF product-based business    → boost Instagram / Facebook by 20%
IF B2B segment               → reduce TikTok / Instagram by 40%
IF audience age 45+          → downgrade TikTok reach_potential by 50%
```

---

#### 3.3.4 Trade-off Engine

When the top two candidates are **within 0.10** of each other in `weighted_score`, a full trade-off analysis is mandatory before selection.

**Trade-off output format:**
```json
{
  "candidate_A": { "name": "Instagram", "weighted_score": 0.82, "strength": "conversion" },
  "candidate_B": { "name": "TikTok",    "weighted_score": 0.74, "strength": "reach"       },
  "delta": 0.08,
  "trade_off": "Instagram yields higher conversion (0.82 vs 0.61) but lower viral reach.",
  "decision":  "Instagram selected — objective prioritizes conversion at 40% weight.",
  "rejected":  ["TikTok — strong reach does not compensate for low conversion alignment"]
}
```

---

### 3.4 Decision Layer

**Purpose:** Receive the top-scored candidate from the Strategy Engine and formalize the decision as a structured record. The decision record is **immutable** — content generation must not deviate from it.

**Decision record format:**
```json
{
  "selected_platform": "Instagram",
  "selected_topic":    "weekly grocery deals",
  "selected_format":   "carousel post",
  "selected_time":     "Thursday 6–8 PM",
  "decision_score":    0.82,
  "reason":            "Maximizes conversion score for budget-conscious local audience.",
  "rejected": [
    { "option": "TikTok",   "score": 0.74, "reason": "Reach does not offset low conversion." },
    { "option": "Facebook", "score": 0.68, "reason": "Lower audience_fit for this segment." }
  ]
}
```

**Rules:**
- The selected option must be the one with the highest `weighted_score`
- All rejected alternatives must be listed with explicit reasons
- No contradictions permitted between decision, simulation, and content

---

### 3.5 Content Generator

**Purpose:** Generate the final content asset. Content is strictly constrained by the Decision Record — no creative freedom exists outside those parameters.

**Required content structure:**

| Element | Description |
|---------|-------------|
| **Hook** | Captures attention in the first 3 seconds or first line |
| **Problem** | Surfaces the pain point the audience recognizes |
| **Solution** | Positions the product/offer as the answer |
| **Value** | States a concrete, specific benefit (not generic) |
| **CTA** | A single, specific call-to-action aligned with `goal_type` |

> ⚠️ **CONSTRAINTS:**
> - Content MUST follow strategy. No independent creative choices.
> - CTA must match the conversion goal — never generic (`"Learn more"` is not a conversion CTA).
> - Do NOT generate content before the Decision Record is finalized.

---

### 3.6 Simulation Engine

**Purpose:** Produce predicted performance metrics using deterministic formulas. The engine must never invent numbers — every output must be traceable to inputs and formula parameters.

**Formulas:**
```
reach       = base_platform_reach × audience_alignment_coefficient
engagement  = format_fit_score    × content_relevance_score
conversion  = goal_alignment      × CTA_strength_score

confidence  = score_gap(top_2_candidates)
            + score_consistency(all_dimensions)
            + input_clarity_score
```

**Output format:**
```json
{
  "predicted_reach":      8500,
  "predicted_engagement": 5.5,
  "predicted_conversion": 3.2,
  "confidence":           0.82,
  "formula_inputs": {
    "base_platform_reach":      12000,
    "audience_alignment":       0.71,
    "format_fit_score":         8.2,
    "content_relevance_score":  0.67
  }
}
```

| ❌ Wrong | ✅ Correct |
|----------|-----------|
| LLM invents plausible-sounding numbers | Every number derived from formula inputs |
| No formula, no traceability | Formula inputs logged alongside output |
| Contradicts decision scores silently | Simulation consistent with decision score |

---

### 3.7 Feedback Engine

**Purpose:** Compare predicted simulation outputs to actual performance data. Update scoring weights for future decisions. This is the learning mechanism — without it, the system does not improve.

**Weight update logic:**
```
IF actual_engagement < predicted_engagement:
    format_weight  += 0.05
    topic_weight   -= 0.05

IF actual_reach < predicted_reach:
    virality_weight += 0.05

IF actual_conversion > predicted_conversion:
    CTA_weight      += 0.03    # reinforce what worked
```

**Output format:**
```json
{
  "actual":    { "reach": 6200, "engagement": 4.1, "conversion": 2.8 },
  "predicted": { "reach": 8500, "engagement": 5.5, "conversion": 3.2 },
  "delta":     { "reach": -2300, "engagement": -1.4, "conversion": -0.4 },
  "weight_updates": {
    "format_weight":  "+0.05",
    "topic_weight":   "-0.05"
  },
  "next_strategy_change": "Increase video-based content",
  "platform_change": false
}
```

---

### 3.8 Memory Layer

**Purpose:** Persist decision records, performance outcomes, and weight updates. Enables compounding improvement — each decision is informed by the full history of prior outcomes.

**Memory record format:**
```json
{
  "decision_id":    "2024-11-15-001",
  "decision":       { },
  "simulation":     { },
  "actual":         { },
  "weight_state":   { },
  "weight_updates": { }
}
```

**Rules:**
- Query memory before generating candidates to bias toward historically effective options
- Surface patterns: which platforms outperform simulation for this audience segment?
- Weight state must be versioned — **never mutate historical records**

---

## 4. Master System Prompt

Copy this verbatim into the LLM powering the Strategy Engine:

```
You are NOT a content generator.
You are a decision-making strategy engine.

Your job is to:
  1. Optimize every decision for the stated business objective.
  2. Generate 3–5 candidate options for each strategic dimension.
  3. Score each candidate using the six weighted dimensions.
  4. Apply hard constraints before scoring.
  5. Run trade-off analysis when top candidates are within 0.10.
  6. Select the highest-scoring option and document all rejections.
  7. Generate content ONLY after the Decision Record is finalized.
  8. Ensure Decision, Simulation, and Content are logically consistent.

STRICT RULES:
  - Do NOT skip candidate comparison.
  - Do NOT assign scores above 7 without explicit justification.
  - Do NOT generate content before the Decision Record is complete.
  - Do NOT use generic CTAs (e.g. "Learn more", "Click here").
  - If two candidates score within 0.10, document the uncertainty.
  - All reasoning must reflect calculation, not intuition.
```

---

## 5. Validation Rules

The system output is valid **only when all four categories pass.**

#### Decision Quality
- ✅ Selected option has the highest `weighted_score` of all candidates
- ✅ Trade-off analysis present when delta between top 2 candidates is < 0.10
- ✅ All rejected alternatives listed with explicit reasons

#### Consistency
- ✅ Simulation reach / engagement / conversion directionally match decision scores
- ✅ Content platform, topic, format, and CTA match the Decision Record exactly
- ✅ No contradiction between any two stages

#### Goal Alignment
- ✅ Content CTA directly drives the stated `goal_type`
- ✅ Scoring weights reflect the objective function priorities

#### Learning
- ✅ Feedback delta triggers at least one weight update
- ✅ Weight updates are persisted to the Memory Layer
- ✅ Next-run candidates reflect historical Memory data

---

## 6. Failure Modes

The following failures indicate broken pipeline logic. All must be detected and rejected at validation time.

| Failure Mode | Description |
|---|---|
| **Topic Drift** | Output topic diverges from the decision (e.g. grocery → lifestyle) without a documented reason |
| **Unjustified High Scores** | A candidate scores above 8/10 with no supporting rationale in the scoring record |
| **Simulation Contradiction** | Simulation predicts high conversion while `conversion_fit` in the decision is below 5 |
| **Generic CTA** | Call-to-action uses vague phrases ("Find out more") instead of a specific action tied to the goal |
| **Missing Trade-off** | Top two candidates within 0.10 but no trade-off analysis was performed |
| **Feedback Ignored** | Actual underperformance recorded but no weight updates applied in the Feedback Engine |
| **Content Before Decision** | Content generated before Decision Record is finalized and saved to Memory |

---

## 7. Final Standard

Strategent is evaluated on one criterion: **does it think like a strategist or generate like a model?**

| ❌ Model Output (Rejected) | ✅ Strategent Output (Required) |
|---|---|
| *"Instagram is good for visuals."* | *"Instagram selected (0.82) over TikTok (0.61). Higher conversion despite 30% lower reach. Objective weights conversion at 40%."* |
| No scoring. No alternatives. No trade-offs. | Every number traceable to a formula input. |
| Output driven by pattern matching, not calculation. | Rejection log documents why every alternative was dropped. |

---

## 8. Implementation Checklist

Use this to verify each pipeline stage before shipping.

#### Brief Interpreter
- [ ] Vague inputs normalized to canonical values
- [ ] All fields populated — no nulls
- [ ] No content or strategy generated at this stage

#### Candidate Generator
- [ ] Minimum 3 topics, 3 platforms, 2 formats, 2 time slots generated
- [ ] Candidates are distinct — no near-duplicates

#### Strategy Engine
- [ ] All 6 dimensions scored for every candidate
- [ ] Hard constraints applied before scoring
- [ ] Trade-off analysis present when delta < 0.10

#### Decision Layer
- [ ] Highest-scoring candidate selected
- [ ] All rejections logged with reasons
- [ ] Decision Record immutable after this point

#### Content Generator
- [ ] Content generated from Decision Record only
- [ ] Hook → Problem → Solution → Value → CTA structure followed
- [ ] CTA is specific and tied to `goal_type`

#### Simulation Engine
- [ ] All metrics derived from formula inputs — no invented numbers
- [ ] Formula inputs logged alongside outputs
- [ ] Confidence score computed and attached

#### Feedback Engine
- [ ] Predicted vs actual delta computed for all metrics
- [ ] Weight updates triggered when delta exceeds threshold
- [ ] Updates persisted to Memory Layer

#### Memory Layer
- [ ] Decision Record saved immediately after Decision Layer
- [ ] Weight state versioned — historical records immutable
- [ ] Memory queried before next Candidate Generation

---

*Strategent v2.0 · System Design Specification*