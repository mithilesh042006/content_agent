# Strategent AI — Backend

AI-powered content strategy agent built with **FastAPI**, **LangChain**, and **Groq Llama 3.3 70B Versatile**.

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set up environment
cp .env.example .env
# Edit .env and add your GROQ_API_KEY (get free from https://console.groq.com/keys)

# 3. Run the server
uvicorn app.main:app --reload

# 4. Open API docs
# → http://localhost:8000/docs
```

## Endpoints

| Method | Path                | Description                          |
| ------ | ------------------- | ------------------------------------ |
| GET    | `/health`           | Health check                         |
| POST   | `/agent/decision`   | AI decides topic + platform + time   |
| POST   | `/agent/simulate`   | Predicts performance metrics         |
| POST   | `/agent/generate`   | Generates platform-specific content  |
| POST   | `/agent/feedback`   | Feedback loop — predicted vs actual  |
| POST   | `/agent/pipeline`   | Full pipeline (all 4 stages)         |

## Testing

```bash
pytest tests/ -v
```

## Architecture

All endpoints use LangChain structured output with Pydantic v2 models. Every LLM call has a deterministic fallback — the API never crashes due to LLM downtime.
