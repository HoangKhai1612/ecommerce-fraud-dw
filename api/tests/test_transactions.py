"""Tests for transaction endpoints."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from api.main import app
from api.database import get_connection

client = TestClient(app)


def mock_connection():
    """Create a mock database connection."""
    mock = MagicMock()
    return mock


def test_get_transaction_found():
    """Test retrieving an existing transaction."""
    mock_conn = MagicMock()
    mock_result = MagicMock()
    mock_result.mappings().first.return_value = {
        "transaction_id": 12345,
        "is_fraud": 0,
        "transaction_amt": 100.50,
        "product_cd": "W",
        "transaction_dt": 86400,
    }
    mock_conn.execute.return_value = mock_result

    def override_get_connection():
        yield mock_conn

    app.dependency_overrides[get_connection] = override_get_connection

    try:
        response = client.get("/transactions/12345")
        assert response.status_code == 200
        data = response.json()
        assert data["transaction_id"] == 12345
        assert data["is_fraud"] == 0
        assert data["transaction_amt"] == 100.50
        assert data["product_cd"] == "W"
    finally:
        app.dependency_overrides.clear()


def test_get_transaction_not_found():
    """Test retrieving a non-existent transaction."""
    mock_conn = MagicMock()
    mock_result = MagicMock()
    mock_result.mappings().first.return_value = None
    mock_conn.execute.return_value = mock_result

    def override_get_connection():
        yield mock_conn

    app.dependency_overrides[get_connection] = override_get_connection

    try:
        response = client.get("/transactions/999999999")
        assert response.status_code == 404
        assert response.json()["detail"] == "Transaction not found"
    finally:
        app.dependency_overrides.clear()


def test_get_transaction_invalid_id():
    """Test with invalid transaction ID (negative)."""
    response = client.get("/transactions/-1")
    assert response.status_code == 422  # Validation error from Path(gt=0)


def test_get_top_predictions_default():
    """Test getting top predictions with default limit."""
    mock_conn = MagicMock()
    mock_result = MagicMock()
    mock_result.mappings().all.return_value = [
        {
            "transaction_id": 111,
            "is_fraud_actual": 1,
            "is_fraud_predicted": 1,
            "fraud_probability": 0.99,
            "transaction_amt": 500.0,
            "model_version": "xgboost-v1-phase16",
        },
        {
            "transaction_id": 222,
            "is_fraud_actual": 1,
            "is_fraud_predicted": 1,
            "fraud_probability": 0.95,
            "transaction_amt": 300.0,
            "model_version": "xgboost-v1-phase16",
        },
    ]
    mock_conn.execute.return_value = mock_result

    def override_get_connection():
        yield mock_conn

    app.dependency_overrides[get_connection] = override_get_connection

    try:
        response = client.get("/transactions/predictions/top")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["transaction_id"] == 111
        assert data[0]["fraud_probability"] == 0.99
        assert data[1]["transaction_id"] == 222
    finally:
        app.dependency_overrides.clear()


def test_get_top_predictions_custom_limit():
    """Test getting top predictions with custom limit."""
    mock_conn = MagicMock()
    mock_result = MagicMock()
    mock_result.mappings().all.return_value = []
    mock_conn.execute.return_value = mock_result

    def override_get_connection():
        yield mock_conn

    app.dependency_overrides[get_connection] = override_get_connection

    try:
        response = client.get("/transactions/predictions/top?limit=5")
        assert response.status_code == 200
        assert response.json() == []
        # Verify the limit parameter was passed
        mock_conn.execute.assert_called_once()
        call_args = mock_conn.execute.call_args
        # call_args is a tuple (args, kwargs)
        params = call_args.kwargs if call_args.kwargs else call_args.args[1] if len(call_args.args) > 1 else {}
        assert params.get("limit") == 5 or params.get(":limit") == 5
    finally:
        app.dependency_overrides.clear()


def test_get_top_predictions_invalid_limit():
    """Test with invalid limit values."""
    # limit < 1
    response = client.get("/transactions/predictions/top?limit=0")
    assert response.status_code == 422

    # limit > 100
    response = client.get("/transactions/predictions/top?limit=101")
    assert response.status_code == 422