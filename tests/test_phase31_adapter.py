"""Phase 31 — Prediction service and database adapter tests.

Tests the PredictionService and marts.web_test_history database layer directly
(without HTTP). Uses real XGBoost inference and real PostgreSQL.

Run from the project root:

    .venv\Scripts\python.exe -m pytest tests/test_phase31_adapter.py -v
"""

from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import pytest

from api.services.prediction_service import PredictionService
from api.database import (
    ensure_history_table,
    insert_prediction_record,
    get_prediction_record,
    list_prediction_records,
    save_ai_explanation,
    HISTORY_TABLE,
)
from api.models import PredictionsFilter

TEST_TRANSACTION_ID = 9000002


@pytest.fixture(scope="module")
def service():
    """Create a PredictionService (loads real XGBoost pipeline)."""
    svc = PredictionService()
    svc._ensure_loaded()
    return svc


@pytest.fixture(scope="module", autouse=True)
def history_table():
    """Ensure the history table exists before tests."""
    ensure_history_table()


def _cleanup(transaction_id: int):
    """Remove test rows for a given transaction_id."""
    from api.database import get_engine
    from sqlalchemy import text
    eng = get_engine()
    with eng.begin() as conn:
        conn.execute(
            text(f"DELETE FROM {HISTORY_TABLE} WHERE transaction_id = :tid"),
            {"tid": transaction_id},
        )


class TestPredictionService:
    def test_predict_and_save_returns_record(self, service):
        """Real XGBoost inference + persist to database."""
        try:
            record = service.predict_and_save(
                input_mode="ieee-cis",
                transaction={
                    "transaction_id": TEST_TRANSACTION_ID,
                    "transaction_dt": 86400,
                    "transaction_amt": 150.75,
                    "product_cd": "W",
                    "card1": 1001,
                    "card4": "visa",
                    "device_type": "mobile",
                },
                transaction_id_for_history=TEST_TRANSACTION_ID,
            )
        except RuntimeError as exc:
            pytest.skip(f"Model or database unavailable: {exc}")

        assert record["prediction_id"]
        assert record["transaction_id"] == TEST_TRANSACTION_ID
        assert record["model_version"] == "xgboost-v1-phase16"
        assert record["input_mode"] == "ieee-cis"
        assert record["is_fraud_predicted"] in (0, 1)
        assert 0.0 <= record["fraud_probability"] <= 1.0
        assert record["threshold"] == 0.5
        assert record["status"] == "ok"
        assert record["ai_available"] is False

    def test_get_record_by_id(self, service):
        """Round-trip: create then fetch by ID."""
        try:
            created = service.predict_and_save(
                input_mode="ieee-cis",
                transaction={
                    "transaction_id": TEST_TRANSACTION_ID,
                    "transaction_dt": 86400,
                    "transaction_amt": 200.0,
                    "product_cd": "H",
                    "card1": 2002,
                    "card4": "mastercard",
                },
                transaction_id_for_history=TEST_TRANSACTION_ID,
            )
        except RuntimeError as exc:
            pytest.skip(f"Model or database unavailable: {exc}")

        fetched = service.get_record(created["prediction_id"])
        assert fetched is not None
        assert str(fetched["prediction_id"]) == created["prediction_id"]
        assert fetched["transaction_id"] == TEST_TRANSACTION_ID
        assert fetched["input_mode"] == "ieee-cis"

    def test_get_record_not_found(self, service):
        result = service.get_record(str(uuid4()))
        assert result is None

    def test_list_records_pagination(self, service):
        """Create two records, then list with limit/offset."""
        try:
            service.predict_and_save(
                input_mode="ieee-cis",
                transaction={
                    "transaction_id": TEST_TRANSACTION_ID,
                    "transaction_dt": 86400,
                    "transaction_amt": 50.0,
                    "product_cd": "C",
                    "card1": 3003,
                    "card4": "amex",
                },
                transaction_id_for_history=TEST_TRANSACTION_ID,
            )
            service.predict_and_save(
                input_mode="ecommerce-sim",
                transaction={
                    "transaction_id": TEST_TRANSACTION_ID,
                    "transaction_dt": 86400,
                    "transaction_amt": 75.0,
                    "product_cd": "H",
                },
                transaction_id_for_history=TEST_TRANSACTION_ID,
            )
        except RuntimeError as exc:
            pytest.skip(f"Model or database unavailable: {exc}")

        items, total = service.list_records(limit=5, offset=0)
        assert total >= 2
        assert len(items) <= 5
        modes = {it["input_mode"] for it in items}
        assert "ieee-cis" in modes or "ecommerce-sim" in modes

    def test_list_records_filter(self, service):
        items, total = service.list_records(
            filter_params={"input_mode": "ieee-cis"},
            limit=10,
            offset=0,
        )
        for it in items:
            assert it["input_mode"] == "ieee-cis"


class TestDatabaseLayer:
    def test_insert_and_get_roundtrip(self):
        pid = str(uuid4())
        predicted_at = datetime.now(timezone.utc)
        insert_prediction_record(
            prediction_id=pid,
            transaction_id=TEST_TRANSACTION_ID,
            model_version="xgboost-v1-phase16",
            input_mode="ieee-cis",
            input_payload={"transaction_id": TEST_TRANSACTION_ID},
            is_fraud_predicted=0,
            fraud_probability=0.25,
            threshold=0.5,
            predicted_at=predicted_at,
            ai_available=False,
        )
        row = get_prediction_record(pid)
        assert row is not None
        assert str(row["prediction_id"]) == pid
        assert row["transaction_id"] == TEST_TRANSACTION_ID
        assert row["is_fraud_predicted"] == 0
        assert row["fraud_probability"] == 0.25

    def test_save_ai_explanation(self):
        pid = str(uuid4())
        predicted_at = datetime.now(timezone.utc)
        insert_prediction_record(
            prediction_id=pid,
            transaction_id=None,
            model_version="xgboost-v1-phase16",
            input_mode="ecommerce-sim",
            input_payload={},
            is_fraud_predicted=1,
            fraud_probability=0.85,
            threshold=0.5,
            predicted_at=predicted_at,
            ai_available=False,
        )
        save_ai_explanation(
            prediction_id=pid,
            explanation="Giai thich thu",
            ai_available=True,
        )
        row = get_prediction_record(pid)
        assert row is not None
        assert row["ai_explanation"] == "Giai thich thu"
        assert row["ai_available"] is True
        assert row["ai_explanation_at"] is not None

    def test_list_with_filters(self):
        pid1 = str(uuid4())
        pid2 = str(uuid4())
        now = datetime.now(timezone.utc)
        insert_prediction_record(
            prediction_id=pid1, transaction_id=TEST_TRANSACTION_ID,
            model_version="xgboost-v1-phase16", input_mode="ieee-cis",
            input_payload={}, is_fraud_predicted=1,
            fraud_probability=0.9, threshold=0.5,
            predicted_at=now, ai_available=False,
        )
        insert_prediction_record(
            prediction_id=pid2, transaction_id=TEST_TRANSACTION_ID,
            model_version="xgboost-v1-phase16", input_mode="ecommerce-sim",
            input_payload={}, is_fraud_predicted=0,
            fraud_probability=0.1, threshold=0.5,
            predicted_at=now, ai_available=False,
        )
        f = PredictionsFilter(input_mode="ieee-cis", is_fraud_predicted=1)
        items, total = list_prediction_records(filter=f, limit=50, offset=0)
        ids = {str(it["prediction_id"]) for it in items}
        assert pid1 in ids
        assert pid2 not in ids

    def test_cleanup(self):
        _cleanup(TEST_TRANSACTION_ID)
