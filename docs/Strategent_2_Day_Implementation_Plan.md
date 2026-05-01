# Strategent — 2-Day Implementation Plan
## React + FastAPI + LangChain (Free Tier Only)

> This document contains only the hackathon build plan for the two days leading up to the prototype submission.

---

## 1) Goal of the Prototype

Build a demo-ready AI agent that can:
1. accept a user's business goal and audience context,
2. decide what content should be created,
3. predict which platform is the best fit,
4. generate the content,
5. explain its reasoning,
6. and show a lightweight feedback loop.

The prototype must feel like an **agent** and not a simple text generator.

---

## 2) Recommended Free-Tier AI Model

### **Primary model: Groq Llama 3.3 70B Versatile**
Use **Llama 3.3 70B Versatile on Groq** as the main model for the prototype because Groq offers a **free-tier API** with generous per-minute limits (≈30 requests/min) and industry-leading inference latency via their LPU architecture. Llama 3.3 70B is a strong general-reasoning model well-suited to the decision, simulation, and explanation stages of the agent. LangChain provides official support through `ChatGroq` (package: `langchain-groq`).

### **Why not a smaller Llama variant as the default?**
Groq also serves smaller Llama variants (8B, instant-tier models) that have higher per-minute limits, but Llama 3.3 70B Versatile is the better fit here because the prototype needs stronger reasoning for decisions, simulations, and explanation quality. Smaller models are better for lightweight formatting tasks; 70B is the stronger choice for the core agent brain.

---

## 3) Required Tech Stack

### Frontend
- React
- Simple dashboard layout
- Form + result cards

### Backend
- FastAPI
- REST APIs for each agent step

### Agent Layer
- LangChain
- Groq Llama 3.3 70B Versatile
- Structured prompting
- Lightweight orchestration

### Storage
- Optional local JSON / in-memory store for MVP
- Optional PostgreSQL only if time permits

### Deployment for MVP
- Local run is enough for prototype submission
- Keep the architecture cloud-ready, but do not depend on paid services

---

## 4) What the Prototype Must Show

The prototype must show these five things clearly:

1. **Decision**
   - The agent chooses what content to create.
2. **Prediction**
   - The agent predicts which platform will perform better.
3. **Generation**
   - The agent writes platform-ready content.
4. **Reasoning**
   - The agent explains why it made the decision.
5. **Learning**
   - The agent shows how future recommendations improve using feedback.

---

## 5) Required Features and How Each Must Work

### 5.1 Input Capture
**What is required**
- Business / domain input
- Content goal
- Target audience
- Tone (optional)

**How it works**
- The React form collects the input.
- On submit, the form sends a JSON payload to the backend.
- The backend uses the input as the agent context.

**Expected output**
- A validated JSON object containing the user's request.

---

### 5.2 Decision Agent
**What is required**
- Topic selection
- Platform selection
- Best posting time
- Reasoning explanation

**How it works**
- FastAPI sends the input to the LangChain prompt.
- Groq Llama 3.3 70B Versatile returns a structured decision.
- The response must be JSON, not plain text.
- The decision must reflect business logic, audience fit, and platform fit.

**Expected output**
- JSON response with:
  - `topic`
  - `platform`
  - `posting_time`
  - `reason`

---

### 5.3 Performance Simulation
**What is required**
- Predicted reach
- Predicted engagement
- Confidence score
- Alternative platform comparison

**How it works**
- The backend uses a second agent prompt or a rules-based scoring layer.
- The agent compares the selected platform against at least one alternative.
- This step makes the prototype feel predictive instead of purely generative.

**Expected output**
- JSON response with:
  - `predicted_reach`
  - `predicted_engagement`
  - `confidence`
  - `alternative_platform`
  - `alternative_platform_score`

---

### 5.4 Content Generation
**What is required**
- Final post copy
- Hook
- CTA
- Hashtags or concise formatting if needed

**How it works**
- After the decision and simulation are complete, the backend generates content.
- The generated text must match the chosen platform style.
- The copy should be short, clear, and presentation-friendly.

**Expected output**
- JSON response with:
  - `headline`
  - `post_copy`
  - `cta`
  - `hashtags`

---

### 5.5 Feedback Loop
**What is required**
- Mock post-performance result
- Learning note
- Next-step recommendation

**How it works**
- The system simulates actual performance using mock numbers.
- The agent compares predicted vs actual output.
- The agent then produces a learning summary.

**Expected output**
- JSON response with:
  - `actual_reach`
  - `actual_engagement`
  - `learning_note`
  - `next_recommendation`

---

### 5.6 UI Transparency
**What is required**
- Show the decision clearly
- Show the simulation clearly
- Show the content clearly
- Show the feedback clearly
- Show the reasoning clearly

**How it works**
- The React UI must display each stage in a separate section.
- The judge should understand the flow in one glance.
- The UI should feel like an agent dashboard, not a text editor.

**Expected output**
- A clean dashboard that visually explains the agent's workflow.

---

## 6) Day 1 Plan — Build the Core Agent

### Day 1 Objective
Get the backend and the core agent flow working end-to-end.

### Tasks

#### A. Project Setup
- Create the React app.
- Create the FastAPI app.
- Configure environment variables for the Groq API key.
- Install LangChain Groq integration (`langchain-groq`).
- Define the request / response schema.

#### B. Build the Input Form
- Add fields for domain, goal, audience, and tone.
- Validate required fields.
- Add a submit button that calls the backend.

#### C. Build the Decision Endpoint
- Create `POST /agent/decision`.
- Send the user input to Groq Llama 3.3 70B Versatile.
- Return structured JSON with topic, platform, time, and reason.

#### D. Build the Simulation Endpoint
- Create `POST /agent/simulate`.
- Use Groq or a rules-based scoring function.
- Return predicted reach, engagement, confidence, and alternative platform comparison.

#### E. Build the Content Endpoint
- Create `POST /agent/generate`.
- Generate platform-specific content.
- Return hook, post copy, CTA, and hashtags.

#### F. Build the First UI Output
- Show the three outputs:
  - decision,
  - simulation,
  - generated content.
- Keep styling minimal on Day 1.

### Day 1 Implementation Output
- React form works.
- FastAPI endpoints work.
- LangChain + Groq are connected.
- The agent can produce structured decision output.

---

## 7) Day 2 Plan — Add Feedback, Polish, and Demo Readiness

### Day 2 Objective
Turn the working prototype into a judge-friendly demo.

### Tasks

#### A. Build the Feedback Endpoint
- Create `POST /agent/feedback`.
- Accept mock performance metrics.
- Return a learning note and a next recommendation.

#### B. Connect the Full Flow
- One button should run the complete pipeline:
  1. decision,
  2. simulation,
  3. generation,
  4. feedback.

#### C. Improve the UI
- Add clear card sections.
- Highlight decision, simulation, content, and learning.
- Make the flow easy to scan quickly.

#### D. Add Comparison Mode
- Show the selected platform and the alternative platform side-by-side.
- Make the prediction step visible and understandable.

#### E. Add Demo Data
- Prepare 2–3 sample scenarios:
  - startup launch post,
  - product announcement,
  - educational content post.
- These should be ready for judge demo.

#### F. Final Cleanup
- Remove unnecessary complexity.
- Ensure the app runs locally without failures.
- Make the output deterministic enough for demo stability.

### Day 2 Implementation Output
- Fully connected agent flow.
- Clean dashboard.
- Feedback loop visible.
- Demo scenarios ready.
- Prototype stable enough for submission.

---

## 8) Exact Deliverables by Submission Time

By the end of Day 2, the implementation must output:

### Frontend Deliverable
- A React dashboard with:
  - input form,
  - decision card,
  - simulation card,
  - content card,
  - feedback card.

### Backend Deliverable
- FastAPI endpoints for:
  - decision,
  - simulation,
  - generation,
  - feedback.

### Agent Deliverable
- LangChain-powered Groq agent workflow.
- Structured JSON outputs for each step.

### Demo Deliverable
- A working prototype where the judge can:
  - enter a goal,
  - click one button,
  - see the agent decide,
  - see the prediction,
  - see the generated content,
  - see the feedback learning.

---

## 9) Success Criteria for the Prototype

The prototype is successful if it clearly demonstrates:
- agentic reasoning,
- simulated prediction,
- autonomous recommendation,
- business usefulness,
- and a polished end-to-end flow.

The submission should feel like a product prototype, not a basic AI wrapper.

---

## 10) Final Rule for the Build

Keep everything simple, stable, and explainable.

The priority is:
1. correct agent flow,
2. visible decision-making,
3. judge-friendly UI,
4. free-tier reliability,
5. demo stability.
