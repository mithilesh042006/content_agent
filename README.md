# ReachCraft

An AI content-strategy agent that takes a business brief and returns a full four-stage strategy report — platform decision, performance simulation, conversion-focused copy, and a feedback/learning loop — in a single call.

Built with **React**, **FastAPI**, **LangChain**, and **Groq Llama 3.3 70B Versatile**.

---

## What it does

Given a brief (business domain, content goal, target audience, tone), the agent produces:

| Stage | Output |
| --- | --- |
| 01 · Decision   | Topic, platform (chosen via a 6-platform scoring table), posting time, and rationale that references the scoring gap. |
| 02 · Simulation | Reach + engagement predictions **derived from** four explicit sub-scores (audience alignment, goal alignment, format suitability, virality potential), with a breakdown of how the sub-scores produced the numbers. |
| 03 · Generation | Platform-native copy scaffolded as hook → pain → value → proof → CTA. The CTA verb is pinned to the stated goal (signup goals get "Sign up at…", sales goals get "Shop now at…", etc.). |
| 04 · Feedback   | Mock-actual performance vs. predicted, a learning note, and a next-step recommendation. |

The decision's runner-up platform is passed directly into the simulation, so the two stages cannot contradict each other by construction.

---

## Repository layout

```
ReachCraft/
├── backend/           FastAPI service, LangChain agents, Groq integration
│   ├── app/
│   │   ├── main.py              App entry point + CORS
│   │   ├── config.py            Settings (env-driven)
│   │   ├── dependencies.py      LLM singleton (ChatGroq)
│   │   ├── schemas/             Pydantic request/response models
│   │   ├── prompts/             System + user prompt templates per stage
│   │   ├── services/            One service per agent stage (with fallbacks)
│   │   └── routers/             /health + /agent endpoints
│   ├── tests/                   pytest suite (LLM is mocked)
│   ├── run_agent.py             Interactive terminal client
│   ├── test_live.py             Live pipeline smoke test
│   └── .env.example
├── frontend/          React 19 + Vite + Tailwind v4
│   ├── src/
│   │   ├── App.jsx              Single-page UI (all components colocated)
│   │   ├── index.css            Theme tokens + animations
│   │   └── main.jsx
│   ├── index.html
│   └── vite.config.js
└── docs/              Planning, analysis, and fix-ticket documents
```

---

## Prerequisites

- **Python 3.11+**
- **Node.js 20+** and **npm**
- A **Groq API key** — free tier is sufficient. Get one at https://console.groq.com/keys.

---

## Quick start

### 1. Backend

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
# edit .env and paste your GROQ_API_KEY
uvicorn app.main:app --port 8000 --reload
```

Health check: http://localhost:8000/health
Swagger UI:   http://localhost:8000/docs

### 2. Frontend

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173. CORS is already configured on the backend for this origin.

---

## Testing the agent

Four ways to exercise the pipeline, from easiest to most automated:

### Interactive terminal client

From `backend/`:

```bash
python run_agent.py             # prompts for the four brief fields
python run_agent.py --sample    # runs a pre-filled grocery-shop brief
python run_agent.py --json      # dumps raw JSON instead of styled output
```

Renders the full input + four-stage output inline with bar graphs for the simulation sub-scores. Calls the agent in-process, so the backend server does not need to be running.

### Swagger UI

With the backend running, open http://localhost:8000/docs. Click any endpoint, "Try it out", paste a JSON body, and Execute.

### curl

```bash
curl -X POST http://localhost:8000/agent/pipeline \
  -H "Content-Type: application/json" \
  -d '{
    "business_domain": "SaaS fintech",
    "content_goal": "increase signups for our new API product",
    "target_audience": "startup founders and CTOs",
    "tone": "authoritative"
  }'
```

On Windows PowerShell, use `curl.exe` (the `curl` alias is `Invoke-WebRequest` and takes different flags).

### Automated test suite

```bash
cd backend
pytest tests/ -v
```

32 tests covering all endpoints. The LLM is mocked to `None` in `tests/conftest.py`, so tests exercise the deterministic fallback paths — fast (~45 s), reproducible, and safe to run without a Groq key.

---

## API surface

All agent endpoints live under `/agent/`.

| Method | Path              | Body              | Description |
| ------ | ----------------- | ----------------- | ----------- |
| GET    | `/health`         | —                 | Health check. |
| POST   | `/agent/decision` | UserInput         | Stage 01 only — platform scoring + choice. |
| POST   | `/agent/simulate` | UserInput         | Runs decision then simulation; returns simulation only. |
| POST   | `/agent/generate` | UserInput         | Runs decision then content generation; returns content only. |
| POST   | `/agent/feedback` | FeedbackRequest   | Stage 04 — requires prior stages' outputs as input. |
| POST   | `/agent/pipeline` | UserInput         | All four stages in one call (~9–12 s). |

### UserInput

```json
{
  "business_domain": "string (2–200 chars)",
  "content_goal":    "string (5–500 chars)",
  "target_audience": "string (3–300 chars)",
  "tone":            "professional | casual | witty | authoritative | inspirational"
}
```

### PipelineResponse (shape)

```json
{
  "decision":  { "topic", "platform", "posting_time", "reason", "platform_scores": [...], "chosen_because" },
  "simulation":{ "audience_alignment", "goal_alignment", "format_suitability", "virality_potential",
                 "predicted_reach", "predicted_engagement", "confidence",
                 "alternative_platform", "alternative_platform_score", "comparison_summary",
                 "score_breakdown": [...] },
  "content":   { "headline", "post_copy", "cta", "hashtags": [...] },
  "feedback":  { "actual_reach", "actual_engagement", "learning_note", "next_recommendation" }
}
```

Full schemas live in [backend/app/schemas/](backend/app/schemas/).

---

## Architecture notes

### Scoring-first decisions

The decision stage scores all six candidate platforms (LinkedIn, X, Instagram, TikTok, Facebook, YouTube) across four axes:
`audience_fit`, `goal_fit`, `format_fit`, `conversion_fit`. The platform with the highest total (0–40) wins; its runner-up is passed into the simulation stage as the alternative platform. Decision and simulation cannot disagree on what the alternative is.

### Derived simulation numbers

The simulation prompt requires the four sub-scores to be computed first, then derives `predicted_reach` and `predicted_engagement` inside the platform's organic benchmark range using explicit formulas. The `score_breakdown` field records how the sub-scores produced the numbers — no free-floating magic values.

### Conversion-aware content

The content prompt maps goal keywords to CTA verbs. A goal containing "signup" gets "Sign up at…"; "sales/buy/customer" gets "Shop now at…"; "demo/leads" gets "Book a demo at…". Engagement filler CTAs ("Learn more", "Drop a fire", "Tag a friend") are explicitly rejected unless the goal is engagement itself. The `post_copy` follows a hook → pain → value → proof scaffolding.

### Deterministic fallbacks

Every stage has a fully deterministic fallback path that produces schema-valid output without calling Groq. If the LLM fails, retries are exhausted, or the API key is missing, the agent still responds — just with rule-based output instead of generative copy. This makes the API robust enough to demo offline.

---

## Configuration

Environment variables (all in `backend/.env`):

| Variable              | Default                     | Description |
| --------------------- | --------------------------- | ----------- |
| `GROQ_API_KEY`        | *(required for live calls)* | Groq API key. |
| `MODEL_NAME`          | `llama-3.3-70b-versatile`   | Groq model ID. |
| `MODEL_TEMPERATURE`   | `0.7`                       | LLM temperature. |
| `CORS_ORIGINS`        | `http://localhost:5173,http://localhost:3000` | Comma-separated allowed origins. |
| `LOG_LEVEL`           | `INFO`                      | Python logging level. |

Frontend reads `VITE_API_URL` at build time (defaults to `http://localhost:8000`).

---

## Tech stack

**Backend**
- FastAPI · Pydantic v2
- LangChain + `langchain-groq`
- Groq SDK 1.x
- pytest · pytest-asyncio

**Frontend**
- React 19
- Vite 8
- Tailwind CSS v4 (CSS-first via `@theme`)
- Fraunces · Instrument Sans · JetBrains Mono (Google Fonts)

**Model**
- Groq Llama 3.3 70B Versatile (function-calling for structured output)

---

## Development

### Adding a new agent stage

1. Define the response schema in `backend/app/schemas/`.
2. Write system + user prompts in `backend/app/prompts/`.
3. Create a service in `backend/app/services/` — must include a deterministic fallback.
4. Add an endpoint in `backend/app/routers/agent.py`.
5. Wire it into `pipeline_endpoint` if it belongs in the full flow.
6. Add tests in `backend/tests/` — LLM is auto-mocked to `None` via the `mock_llm` fixture.

### Running without a Groq key

The backend logs `GROQ_API_KEY not set — LLM calls will use fallback responses` and every stage uses rule-based logic. Responses remain schema-valid; strategy quality drops to "plausible template" rather than "reasoned copy". Useful for wiring work and test-driving the frontend.

---

## License

Internal project. Not published.
