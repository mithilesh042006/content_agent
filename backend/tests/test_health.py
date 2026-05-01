"""Tests for the health check endpoint."""


def test_health_returns_200(client):
    response = client.get("/health")
    assert response.status_code == 200


def test_health_response_body(client):
    data = client.get("/health").json()
    assert data["status"] == "healthy"
    assert data["service"] == "strategent-ai"
    assert data["version"] == "1.0.0"
