"""Tests for health endpoints."""

from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["service"] == "fraud-detection-api"


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["service"] == "fraud-detection-api"


def test_ready():
    response = client.get("/ready")
    assert response.status_code == 200
    # Ready status depends on DB availability
    assert response.json()["status"] in ["ready", "not_ready"]
    assert response.json()["database"] in ["ok", "unavailable"]


def test_openapi():
    response = client.get("/openapi.json")
    assert response.status_code == 200

    schema = response.json()
    assert "paths" in schema
    assert "/health" in schema["paths"]
    assert "/ready" in schema["paths"]
    assert "/predict" in schema["paths"]
    assert "/transactions/{transaction_id}" in schema["paths"]
    assert "/transactions/predictions/top" in schema["paths"]