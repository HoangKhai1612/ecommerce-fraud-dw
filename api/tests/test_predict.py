"""Tests for prediction endpoint."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from api.main import app
from api.inference import get_inference_pipeline, InferencePipeline

client = TestClient(app)


def test_predict_valid_request():
    """Test prediction with valid input."""
    mock_pipeline = MagicMock(spec=InferencePipeline)
    mock_pipeline._loaded = True
    mock_pipeline.MODEL_VERSION = "xgboost-v1-phase16"
    mock_pipeline.predict_proba.return_value = [0.85]

    def override_get_inference_pipeline():
        return mock_pipeline

    app.dependency_overrides[get_inference_pipeline] = override_get_inference_pipeline

    try:
        response = client.post(
            "/predict",
            json={
                "transaction_id": 12345,
                "transaction_dt": 86400,
                "transaction_amt": 150.75,
                "product_cd": "W",
                "card1": 1001,
                "card4": "visa",
                "device_type": "mobile",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["transaction_id"] == 12345
        assert data["is_fraud"] == 1  # 0.85 >= 0.5
        assert data["fraud_probability"] == 0.85
        assert data["risk_level"] == "high"  # >= 0.7
        assert data["model_version"] == "xgboost-v1-phase16"
    finally:
        app.dependency_overrides.clear()


def test_predict_low_risk():
    """Test prediction with low fraud probability."""
    mock_pipeline = MagicMock(spec=InferencePipeline)
    mock_pipeline._loaded = True
    mock_pipeline.MODEL_VERSION = "xgboost-v1-phase16"
    mock_pipeline.predict_proba.return_value = [0.15]

    def override_get_inference_pipeline():
        return mock_pipeline

    app.dependency_overrides[get_inference_pipeline] = override_get_inference_pipeline

    try:
        response = client.post(
            "/predict",
            json={
                "transaction_id": 12345,
                "transaction_dt": 86400,
                "transaction_amt": 50.0,
                "product_cd": "W",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_fraud"] == 0  # 0.15 < 0.5
        assert data["fraud_probability"] == 0.15
        assert data["risk_level"] == "low"  # < 0.3
    finally:
        app.dependency_overrides.clear()


def test_predict_medium_risk():
    """Test prediction with medium fraud probability."""
    mock_pipeline = MagicMock(spec=InferencePipeline)
    mock_pipeline._loaded = True
    mock_pipeline.MODEL_VERSION = "xgboost-v1-phase16"
    mock_pipeline.predict_proba.return_value = [0.5]

    def override_get_inference_pipeline():
        return mock_pipeline

    app.dependency_overrides[get_inference_pipeline] = override_get_inference_pipeline

    try:
        response = client.post(
            "/predict",
            json={
                "transaction_id": 12345,
                "transaction_dt": 86400,
                "transaction_amt": 100.0,
                "product_cd": "C",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_fraud"] == 1  # 0.5 >= 0.5
        assert data["risk_level"] == "medium"  # 0.3 <= 0.5 < 0.7
    finally:
        app.dependency_overrides.clear()


def test_predict_missing_required_fields():
    """Test prediction with missing required fields."""
    response = client.post(
        "/predict",
        json={
            "transaction_id": 12345,
            # missing transaction_dt, transaction_amt, product_cd
        },
    )
    assert response.status_code == 422  # Validation error


def test_predict_invalid_types():
    """Test prediction with invalid field types."""
    response = client.post(
        "/predict",
        json={
            "transaction_id": "not_an_int",
            "transaction_dt": 86400,
            "transaction_amt": 100.0,
            "product_cd": "W",
        },
    )
    assert response.status_code == 422


def test_predict_negative_transaction_id():
    """Test prediction with negative transaction_id."""
    response = client.post(
        "/predict",
        json={
            "transaction_id": -1,
            "transaction_dt": 86400,
            "transaction_amt": 100.0,
            "product_cd": "W",
        },
    )
    assert response.status_code == 422


def test_predict_zero_amount():
    """Test prediction with zero transaction amount."""
    response = client.post(
        "/predict",
        json={
            "transaction_id": 12345,
            "transaction_dt": 86400,
            "transaction_amt": 0,
            "product_cd": "W",
        },
    )
    assert response.status_code == 422


def test_predict_model_not_loaded():
    """Test prediction when model is not loaded."""
    mock_pipeline = MagicMock(spec=InferencePipeline)
    mock_pipeline._loaded = False
    mock_pipeline.load.side_effect = Exception("Model file not found")

    def override_get_inference_pipeline():
        return mock_pipeline

    app.dependency_overrides[get_inference_pipeline] = override_get_inference_pipeline

    try:
        response = client.post(
            "/predict",
            json={
                "transaction_id": 12345,
                "transaction_dt": 86400,
                "transaction_amt": 100.0,
                "product_cd": "W",
            },
        )
        assert response.status_code == 503
        assert "Model not available" in response.json()["detail"]
    finally:
        app.dependency_overrides.clear()


def test_predict_inference_error():
    """Test prediction when inference fails."""
    mock_pipeline = MagicMock(spec=InferencePipeline)
    mock_pipeline._loaded = True
    mock_pipeline.MODEL_VERSION = "xgboost-v1-phase16"
    mock_pipeline.predict_proba.side_effect = Exception("Inference error")

    def override_get_inference_pipeline():
        return mock_pipeline

    app.dependency_overrides[get_inference_pipeline] = override_get_inference_pipeline

    try:
        response = client.post(
            "/predict",
            json={
                "transaction_id": 12345,
                "transaction_dt": 86400,
                "transaction_amt": 100.0,
                "product_cd": "W",
            },
        )
        assert response.status_code == 500
        assert "Inference failed" in response.json()["detail"]
    finally:
        app.dependency_overrides.clear()


def test_predict_extra_fields_allowed():
    """Test that extra fields in request are allowed (flexible schema)."""
    mock_pipeline = MagicMock(spec=InferencePipeline)
    mock_pipeline._loaded = True
    mock_pipeline.MODEL_VERSION = "xgboost-v1-phase16"
    mock_pipeline.predict_proba.return_value = [0.5]

    def override_get_inference_pipeline():
        return mock_pipeline

    app.dependency_overrides[get_inference_pipeline] = override_get_inference_pipeline

    try:
        response = client.post(
            "/predict",
            json={
                "transaction_id": 12345,
                "transaction_dt": 86400,
                "transaction_amt": 100.0,
                "product_cd": "W",
                "extra_field": "ignored",
                "v1": 0.5,
                "c1": 100,
            },
        )
        assert response.status_code == 200
    finally:
        app.dependency_overrides.clear()