"""Shared test fixtures."""

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def sample_user_input():
    """Standard test payload."""
    return {
        "business_domain": "SaaS fintech",
        "content_goal": "Increase brand awareness among tech professionals",
        "target_audience": "Tech-savvy millennials aged 25-35",
        "tone": "professional",
    }


@pytest.fixture
def sample_feedback_input():
    """Standard test payload for feedback endpoint."""
    return {
        "business_domain": "SaaS fintech",
        "content_goal": "Increase brand awareness among tech professionals",
        "target_audience": "Tech-savvy millennials aged 25-35",
        "tone": "professional",
        "topic": "Why Fintech APIs Are the Future of Banking",
        "platform": "LinkedIn",
        "predicted_reach": 5000,
        "predicted_engagement": 4.2,
        "headline": "🚀 The API Revolution in Fintech Is Here",
        "actual_reach": 6200,
        "actual_engagement": 5.1,
    }


@pytest.fixture(autouse=True)
def mock_llm():
    """Mock the LLM dependency so tests never call the real Groq API.

    Patches at the *import site* (llm_service) rather than the definition
    site (dependencies), so the mock intercepts calls even when an .env
    file with a real API key is present.
    """
    from app.dependencies import get_llm
    get_llm.cache_clear()
    with patch("app.services.llm_service.get_llm", return_value=None):
        yield
    get_llm.cache_clear()

