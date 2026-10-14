"""Phase 25 — FastAPI Endpoint Tests.

Tests the FastAPI endpoints using TestClient (no external server needed).
Run from the project root:

    .venv\Scripts\python.exe -m pytest tests/test_api.py -v

Design:
- Uses fastapi.testclient.TestClient for unit/integration testing.
- Does not require running API container.
- Tests input validation, response structure, and HTTP status codes.
"""

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Add api to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "api"))

from api.main import app


client = TestClient(app)


class TestHealthEndpoints:
    """Test health and readiness endpoints."""

    def test_health_check(self):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "fraud-detection-api"

    def test_readiness_check(self):
        response = client.get("/ready")
        assert response.status_code == 200
        data = response.json()
        # Database may or may not be available in test env
        assert data["status"] in ("ready", "not_ready")
        assert data["database"] in ("ok", "unavailable")

    def test_root_endpoint(self):
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "fraud-detection-api"
        assert "docs" in data
        assert "health" in data
        assert "ready" in data


class TestPredictionEndpoint:
    """Test the /predict endpoint."""

    def test_predict_valid_request(self):
        payload = {
            "transaction_id": 12345,
            "transaction_dt": 86400,
            "transaction_amt": 150.75,
            "product_cd": "W",
            "card1": 1001,
            "card4": "visa",
            "device_type": "mobile",
        }
        response = client.post("/predict", json=payload)
        # May return 503 if model not loaded in test env
        if response.status_code == 503:
            pytest.skip("Model not loaded in test environment")
        assert response.status_code == 200
        data = response.json()
        assert "transaction_id" in data
        assert data["transaction_id"] == 12345
        assert "is_fraud" in data
        assert data["is_fraud"] in (0, 1)
        assert "fraud_probability" in data
        assert 0.0 <= data["fraud_probability"] <= 1.0
        assert "risk_level" in data
        assert data["risk_level"] in ("low", "medium", "high")
        assert "model_version" in data
        assert data["model_version"] == "xgboost-v1-phase16"

    def test_predict_invalid_request_rejected(self):
        # Missing required fields
        response = client.post("/predict", json={"transaction_id": "not_an_int"})
        assert response.status_code == 422

    def test_predict_missing_required_fields(self):
        # Missing transaction_dt, transaction_amt, product_cd
        response = client.post("/predict", json={"transaction_id": 12345})
        # Should be rejected with 400 or 422
        assert response.status_code in (400, 422, 503)


class TestTransactionEndpoints:
    """Test transaction lookup endpoints."""

    def test_get_transaction_not_found(self):
        response = client.get("/transactions/999999999")
        # Returns 404 if not found, or 503 if DB not available
        if response.status_code == 503:
            pytest.skip("Database not available in test environment")
        assert response.status_code == 404

    def test_get_top_predictions(self):
        response = client.get("/transactions/predictions/top?limit=5")
        if response.status_code == 503:
            pytest.skip("Database not available in test environment")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 5
        for row in data:
            assert "transaction_id" in row
            assert "fraud_probability" in row
            assert 0.0 <= row["fraud_probability"] <= 1.0
            assert "model_version" in row

    def test_get_top_predictions_limit_validation(self):
        # Limit must be 1-100
        response = client.get("/transactions/predictions/top?limit=0")
        assert response.status_code == 422

        response = client.get("/transactions/predictions/top?limit=101")
        assert response.status_code == 422


class TestOpenAPISchema:
    """Test OpenAPI schema generation."""

    def test_openapi_json(self):
        response = client.get("/openapi.json")
        assert response.status_code == 200
        schema = response.json()
        assert "openapi" in schema
        assert "paths" in schema
        assert "/predict" in schema["paths"]
        assert "/health" in schema["paths"]
        assert "/ready" in schema["paths"]