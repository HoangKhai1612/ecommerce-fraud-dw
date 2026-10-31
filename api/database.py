"""PostgreSQL connection management."""

import json
import os
from collections.abc import Generator
from datetime import datetime
from typing import Any

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.engine import URL

# Load environment variables
load_dotenv()


def get_database_url() -> URL:
    """Build DATABASE_URL from environment variables."""
    return URL.create(
        drivername="postgresql+psycopg2",
        username=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD", "postgres"),
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        database=os.getenv("POSTGRES_DB", "ecommerce_fraud_dw"),
    )


# Create engine lazily
engine: Engine | None = None


def get_engine() -> Engine:
    """Get or create the SQLAlchemy engine."""
    global engine
    if engine is None:
        engine = create_engine(
            get_database_url(),
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=5,
            pool_recycle=1800,
        )
    return engine


def get_connection() -> Generator:
    """Yield a database connection and always close it."""
    eng = get_engine()
    with eng.connect() as connection:
        yield connection


def check_database() -> bool:
    """Return whether PostgreSQL can execute a simple query."""
    try:
        with get_engine().connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Phase 31: prediction history persistence (marts.web_test_history)
# ---------------------------------------------------------------------------

HISTORY_TABLE = "marts.web_test_history"


def ensure_history_table() -> None:
    """Create marts.web_test_history if it does not exist (idempotent).

    Mirrors sql/31_web_test_history.sql so the API can self-initialize
    without requiring an external migration step.
    """
    ddl = f"""
    CREATE TABLE IF NOT EXISTS {HISTORY_TABLE} (
        prediction_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        transaction_id     BIGINT NULL,
        model_version      TEXT NOT NULL,
        input_mode         TEXT NOT NULL CHECK (input_mode IN ('ieee-cis', 'ecommerce-sim')),
        input_payload      JSONB NOT NULL,
        is_fraud_predicted INTEGER NOT NULL CHECK (is_fraud_predicted IN (0, 1)),
        fraud_probability  DOUBLE PRECISION NOT NULL,
        threshold          DOUBLE PRECISION NOT NULL,
        predicted_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
        ai_explanation     TEXT NULL,
        ai_explanation_at  TIMESTAMPTZ NULL,
        ai_available       BOOLEAN NOT NULL DEFAULT FALSE,
        status             TEXT NOT NULL DEFAULT 'ok' CHECK (status IN ('ok', 'error'))
    );
    CREATE INDEX IF NOT EXISTS idx_web_test_history_predicted_at
        ON {HISTORY_TABLE} (predicted_at DESC);
    CREATE INDEX IF NOT EXISTS idx_web_test_history_mode
        ON {HISTORY_TABLE} (input_mode);
    CREATE INDEX IF NOT EXISTS idx_web_test_history_label
        ON {HISTORY_TABLE} (is_fraud_predicted);
    CREATE INDEX IF NOT EXISTS idx_web_test_history_transaction_id
        ON {HISTORY_TABLE} (transaction_id) WHERE transaction_id IS NOT NULL;
    """
    with get_engine().begin() as connection:
        connection.execute(text(ddl))


def insert_prediction_record(
    *,
    prediction_id: str,
    transaction_id: int | None,
    model_version: str,
    input_mode: str,
    input_payload: dict[str, Any],
    is_fraud_predicted: int,
    fraud_probability: float,
    threshold: float,
    predicted_at: datetime,
    ai_available: bool,
    status: str = "ok",
) -> None:
    """Insert one prediction record into marts.web_test_history."""
    with get_engine().begin() as connection:
        connection.execute(
            text(
                f"""
                INSERT INTO {HISTORY_TABLE} (
                    prediction_id, transaction_id, model_version, input_mode,
                    input_payload, is_fraud_predicted, fraud_probability,
                    threshold, predicted_at, ai_available, status
                ) VALUES (
                    :prediction_id, :transaction_id, :model_version, :input_mode,
                    CAST(:input_payload AS jsonb), :is_fraud_predicted, :fraud_probability,
                    :threshold, :predicted_at, :ai_available, :status
                )
                """
            ),
            {
                "prediction_id": prediction_id,
                "transaction_id": transaction_id,
                "model_version": model_version,
                "input_mode": input_mode,
                "input_payload": json.dumps(input_payload, default=str),
                "is_fraud_predicted": is_fraud_predicted,
                "fraud_probability": fraud_probability,
                "threshold": threshold,
                "predicted_at": predicted_at,
                "ai_available": ai_available,
                "status": status,
            },
        )


def get_prediction_record(prediction_id: str) -> dict[str, Any] | None:
    """Fetch one prediction record by ID."""
    with get_engine().connect() as connection:
        row = connection.execute(
            text(
                f"""
                SELECT prediction_id, transaction_id, model_version, input_mode,
                       input_payload, is_fraud_predicted, fraud_probability,
                       threshold, predicted_at, ai_explanation, ai_explanation_at,
                       ai_available, status
                FROM {HISTORY_TABLE}
                WHERE prediction_id = :prediction_id
                """
            ),
            {"prediction_id": prediction_id},
        ).mappings().first()
    return dict(row) if row is not None else None


def list_prediction_records(
    *,
    filter: PredictionsFilter | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[dict[str, Any]], int]:
    """List prediction records with optional filters and pagination."""
    from api.models import PredictionsFilter

    conditions: list[str] = []
    params: dict[str, Any] = {}

    if filter is None:
        filter = PredictionsFilter()

    if filter.input_mode is not None:
        conditions.append("input_mode = :input_mode")
        params["input_mode"] = filter.input_mode
    if filter.is_fraud_predicted is not None:
        conditions.append("is_fraud_predicted = :is_fraud_predicted")
        params["is_fraud_predicted"] = filter.is_fraud_predicted
    if filter.min_probability is not None:
        conditions.append("fraud_probability >= :min_probability")
        params["min_probability"] = filter.min_probability
    if filter.max_probability is not None:
        conditions.append("fraud_probability <= :max_probability")
        params["max_probability"] = filter.max_probability
    if filter.from_predicted_at is not None:
        conditions.append("predicted_at >= :from_predicted_at")
        params["from_predicted_at"] = filter.from_predicted_at
    if filter.to_predicted_at is not None:
        conditions.append("predicted_at <= :to_predicted_at")
        params["to_predicted_at"] = filter.to_predicted_at

    where_clause = ""
    if conditions:
        where_clause = "WHERE " + " AND ".join(conditions)

    count_sql = f"SELECT COUNT(*) FROM {HISTORY_TABLE} {where_clause}"
    items_sql = f"""
        SELECT prediction_id, transaction_id, model_version, input_mode,
               is_fraud_predicted, fraud_probability, threshold,
               predicted_at, ai_available, status
        FROM {HISTORY_TABLE}
        {where_clause}
        ORDER BY predicted_at DESC
        LIMIT :limit OFFSET :offset
    """
    params["limit"] = limit
    params["offset"] = offset

    with get_engine().connect() as connection:
        total = connection.execute(text(count_sql), params).scalar()
        rows = connection.execute(text(items_sql), params).mappings().all()

    return [dict(row) for row in rows], int(total)


def save_ai_explanation(
    *,
    prediction_id: str,
    explanation: str,
    ai_available: bool,
) -> None:
    """Persist AI explanation for an existing prediction record."""
    with get_engine().begin() as connection:
        connection.execute(
            text(
                f"""
                UPDATE {HISTORY_TABLE}
                SET ai_explanation = :explanation,
                    ai_explanation_at = now(),
                    ai_available = :ai_available
                WHERE prediction_id = :prediction_id
                """
            ),
            {
                "prediction_id": prediction_id,
                "explanation": explanation,
                "ai_available": ai_available,
            },
        )