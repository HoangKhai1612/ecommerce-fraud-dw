"""Phase 31 — Integrated platform API tests.

Tests the Phase 31 endpoints using fastapi.testclient.TestClient (no external
server needed). The model is real XGBoost (not mocked). The database is real
PostgreSQL (tests are skipped if the DB is unavailable).

Run from the project root:

    .venv\Scripts\python.exe -m pytest tests/test_phase31_api.py -v
"""

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "api"))

from api.main import app

client = TestClient(app)

VALID_TRANSACTION = {
    "transaction_id": 9000001,
    "transaction_dt": 86400,
    "transaction_amt": 150.75,
    "product_cd": "W",
    "card1": 1001,
    "card4": "visa",
    "device_type": "mobile",
    "device_info": "SM-G950F",
    "p_emaildomain": "gmail.com",
}


def _skip_if_db_unavailable():
    """Skip if PostgreSQL cannot be reached (test env may not have it)."""
    response = client.get("/ready")
    if response.status_code == 200:
        data = response.json()
        if data.get("database") != "ok":
            pytest.skip("Database unavailable in test environment")
    elif response.status_code >= 500:
        pytest.skip("Database unavailable in test environment")


def _skip_if_model_unavailable():
    """Skip if the XGBoost model cannot be loaded."""
    response = client.get("/system/status")
    if response.status_code == 200:
        data = response.json()
        if data.get("model", {}).get("status") != "ok":
            pytest.skip("XGBoost model unavailable in test environment")


class TestSystemStatus:
    def test_system_status_ok(self):
        response = client.get("/system/status")
        assert response.status_code == 200
        data = response.json()
        assert data["api"] == "ok"
        assert "model" in data
        assert "database" in data
        assert "ai" in data
        assert "ollama" in data
        for svc in ("model", "database", "ai", "ollama"):
            assert data[svc]["status"] in ("ok", "degraded", "unavailable")


class TestTransactionSample:
    def test_transactions_sample(self):
        _skip_if_db_unavailable()
        response = client.get("/transactions/sample?limit=3")
        if response.status_code == 503:
            pytest.skip("Database unavailable in test environment")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 3
        for row in data:
            assert "transaction_id" in row
            assert "is_fraud" in row
            assert "transaction_amt" in row
            assert "product_cd" in row
            assert "transaction_dt" in row


class TestPredictionCreate:
    def test_predict_valid_returns_201(self):
        _skip_if_db_unavailable()
        _skip_if_model_unavailable()
        response = client.post("/predictions", json={
            "mode": "ieee-cis",
            "transaction": VALID_TRANSACTION,
        })
        if response.status_code == 503:
            pytest.skip("Model or database unavailable in test environment")
        assert response.status_code == 201
        data = response.json()
        assert "prediction_id" in data
        assert data["transaction_id"] == 9000001
        assert data["model_version"] == "xgboost-v1-phase16"
        assert data["input_mode"] == "ieee-cis"
        assert data["is_fraud_predicted"] in (0, 1)
        assert 0.0 <= data["fraud_probability"] <= 1.0
        assert data["threshold"] == 0.5
        assert data["ai_available"] is False
        assert data["status"] == "ok"
        assert "predicted_at" in data

    def test_predict_missing_required_fields_422(self):
        _skip_if_db_unavailable()
        _skip_if_model_unavailable()
        response = client.post("/predictions", json={
            "mode": "ieee-cis",
            "transaction": {"transaction_id": 12345},
        })
        assert response.status_code in (400, 422, 503)

    def test_predict_invalid_transaction_type_422(self):
        response = client.post("/predictions", json={
            "mode": "ieee-cis",
            "transaction": {"transaction_id": "not_an_int"},
        })
        assert response.status_code == 422


class TestPredictionGet:
    def test_get_prediction_not_found(self):
        response = client.get("/predictions/00000000-0000-0000-0000-000000000000")
        assert response.status_code == 404

    def test_get_prediction_after_create(self):
        _skip_if_db_unavailable()
        _skip_if_model_unavailable()
        create_resp = client.post("/predictions", json={
            "mode": "ieee-cis",
            "transaction": VALID_TRANSACTION,
        })
        if create_resp.status_code == 503:
            pytest.skip("Model or database unavailable in test environment")
        assert create_resp.status_code == 201
        pred_id = create_resp.json()["prediction_id"]

        get_resp = client.get(f"/predictions/{pred_id}")
        if get_resp.status_code == 503:
            pytest.skip("Database unavailable in test environment")
        assert get_resp.status_code == 200
        data = get_resp.json()
        assert data["prediction_id"] == pred_id
        assert data["transaction_id"] == 9000001
        assert "input_payload" in data
        assert "risk_level" in data
        assert data["risk_level"] in ("low", "medium", "high")
        assert data["ai_available"] in (True, False)


class TestPredictionList:
    def test_list_predictions(self):
        _skip_if_db_unavailable()
        response = client.get("/predictions?limit=5&offset=0")
        if response.status_code == 503:
            pytest.skip("Database unavailable in test environment")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "limit" in data
        assert "offset" in data
        assert data["limit"] == 5
        assert data["offset"] == 0
        assert isinstance(data["items"], list)

    def test_list_predictions_filter_mode(self):
        _skip_if_db_unavailable()
        response = client.get("/predictions?input_mode=ieee-cis&limit=5")
        if response.status_code == 503:
            pytest.skip("Database unavailable in test environment")
        assert response.status_code == 200
        data = response.json()
        for item in data["items"]:
            assert item["input_mode"] == "ieee-cis"

    def test_list_predictions_filter_label(self):
        _skip_if_db_unavailable()
        response = client.get("/predictions?is_fraud_predicted=0&limit=5")
        if response.status_code == 503:
            pytest.skip("Database unavailable in test environment")
        assert response.status_code == 200
        data = response.json()
        for item in data["items"]:
            assert item["is_fraud_predicted"] == 0

    def test_list_predictions_limit_validation(self):
        response = client.get("/predictions?limit=0")
        assert response.status_code == 422
        response = client.get("/predictions?limit=201")
        assert response.status_code == 422


class TestPredictionExplain:
    def test_explain_after_create(self):
        _skip_if_db_unavailable()
        _skip_if_model_unavailable()
        create_resp = client.post("/predictions", json={
            "mode": "ieee-cis",
            "transaction": VALID_TRANSACTION,
        })
        if create_resp.status_code == 503:
            pytest.skip("Model or database unavailable in test environment")
        assert create_resp.status_code == 201
        pred_id = create_resp.json()["prediction_id"]

        resp = client.post(f"/predictions/{pred_id}/explain", json={
            "question": "Giai thich ket qua du doan nay."
        })
        if resp.status_code == 503:
            pytest.skip("Database unavailable in test environment")
        assert resp.status_code == 200
        data = resp.json()
        assert data["prediction_id"] == pred_id
        assert isinstance(data["answer"], str)
        assert len(data["answer"]) > 0
        assert data["ai_available"] in (True, False)
        assert data["source"] in ("ai-assistant", "ollama-direct", "unavailable")

    def test_explain_not_found(self):
        resp = client.post(
            "/predictions/00000000-0000-0000-0000-000000000000/explain",
            json={"question": "test"},
        )
        assert resp.status_code == 404


class TestAIChat:
    def test_ai_chat_general(self):
        resp = client.post("/ai/chat", json={"question": "Chao ban"})
        if resp.status_code == 503:
            pytest.skip("Database or AI service unavailable in test environment")
        assert resp.status_code == 200
        data = resp.json()
        assert data["prediction_id"] is None
        assert isinstance(data["answer"], str)
        assert len(data["answer"]) > 0
        assert data["ai_available"] in (True, False)
        assert data["source"] in ("ai-assistant", "ollama-direct", "unavailable")

    def test_ai_chat_missing_question_400(self):
        resp = client.post("/ai/chat", json={})
        assert resp.status_code == 400

    def test_ai_chat_empty_question_400(self):
        resp = client.post("/ai/chat", json={"question": "   "})
        assert resp.status_code == 400

    def test_ai_chat_with_prediction_context(self):
        _skip_if_db_unavailable()
        _skip_if_model_unavailable()
        create_resp = client.post("/predictions", json={
            "mode": "ieee-cis",
            "transaction": VALID_TRANSACTION,
        })
        if create_resp.status_code == 503:
            pytest.skip("Model or database unavailable in test environment")
        assert create_resp.status_code == 201
        pred_id = create_resp.json()["prediction_id"]

        resp = client.post("/ai/chat", params={"prediction_id": pred_id}, json={
            "question": "Du doan nay co tin cahy khong?"
        })
        if resp.status_code == 503:
            pytest.skip("Database unavailable in test environment")
        assert resp.status_code == 200
        data = resp.json()
        assert data["prediction_id"] == pred_id
        assert isinstance(data["answer"], str)
        assert len(data["answer"]) > 0

    def test_ai_chat_prediction_not_found(self):
        resp = client.post("/ai/chat", params={
            "prediction_id": "00000000-0000-0000-0000-000000000000"
        }, json={"question": "test"})
        assert resp.status_code == 404


class TestOpenAPISchema:
    def test_openapi_includes_phase31_paths(self):
        response = client.get("/openapi.json")
        assert response.status_code == 200
        schema = response.json()
        paths = schema["paths"]
        assert "/predictions" in paths
        assert "/predictions/{prediction_id}" in paths
        assert "/predictions/{prediction_id}/explain" in paths
        assert "/ai/chat" in paths
        assert "/system/status" in paths
        assert "/transactions/sample" in paths
