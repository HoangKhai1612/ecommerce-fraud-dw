"""Read-only transaction and prediction endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy import text
from sqlalchemy.engine import Connection

from api.database import get_connection
from api.models import TopPredictionResponse, TransactionResponse

router = APIRouter(prefix="/transactions", tags=["Transactions"])


import json
import os

_MANIFEST_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "evidence", "phase_31", "dw_demo_manifest.json"))

@router.get("/samples")
def get_dw_samples(
    n: int = Query(default=10, ge=1, le=50, description="Number of samples per class"),
    connection: Connection = Depends(get_connection),
):
    """
    Return verified DW demo samples from the manifest.
    Falls back to first N of each class if manifest is invalid/missing.
    """
    from api.inference import MODEL_VERSION, THRESHOLD

    fraud_ids = []
    legit_ids = []

    # Try to load manifest
    try:
        if os.path.exists(_MANIFEST_PATH):
            manifest = json.loads(open(_MANIFEST_PATH, encoding="utf-8").read())
            # Validate manifest matches current model
            if (manifest.get("model_version") == MODEL_VERSION and
                    abs(manifest.get("threshold", 0) - THRESHOLD) < 1e-9):
                fraud_ids = manifest.get("fraud_samples", [])[:n]
                legit_ids = manifest.get("legit_samples", [])[:n]
    except Exception:
        pass

    # Fallback: query first N of each class
    if not fraud_ids or not legit_ids:
        fraud_rows = connection.execute(
            text("SELECT transaction_id FROM marts.fact_transactions WHERE is_fraud = 1 ORDER BY transaction_id LIMIT :limit"),
            {"limit": n},
        ).fetchall()
        legit_rows = connection.execute(
            text("SELECT transaction_id FROM marts.fact_transactions WHERE is_fraud = 0 ORDER BY transaction_id LIMIT :limit"),
            {"limit": n},
        ).fetchall()
        fraud_ids = [r[0] for r in fraud_rows]
        legit_ids = [r[0] for r in legit_rows]

    def fetch_by_ids(ids):
        if not ids:
            return []
        placeholders = ", ".join(f":id{i}" for i in range(len(ids)))
        params = {f"id{i}": tid for i, tid in enumerate(ids)}
        rows = connection.execute(
            text(f"""
                SELECT transaction_id, is_fraud, transaction_amt, product_cd, transaction_dt
                FROM marts.fact_transactions
                WHERE transaction_id IN ({placeholders})
                ORDER BY transaction_id
            """),
            params,
        ).mappings().all()
        return [
            {
                "transaction_id": row["transaction_id"],
                "is_fraud": row["is_fraud"],
                "transaction_amt": float(row["transaction_amt"]),
                "product_cd": row["product_cd"],
                "transaction_dt": row["transaction_dt"],
            }
            for row in rows
        ]

    return {
        "fraud": fetch_by_ids(fraud_ids),
        "legit": fetch_by_ids(legit_ids),
        "model_version": MODEL_VERSION,
        "threshold": THRESHOLD,
        "source": "manifest" if fraud_ids and legit_ids else "fallback",
    }
@router.get("/sample", response_model=list[TransactionResponse])
def get_sample_transactions(
    limit: int = Query(default=5, ge=1, le=20, description="Number of samples"),
    connection: Connection = Depends(get_connection),
):
    """
    Return a few raw transactions from marts.fact_transactions (read-only).

    Intended for mode A (IEEE-CIS model testing): the user can pick a sample
    and run inference without entering 1,014 features manually. Ground truth
    (is_fraud) is returned separately and is never fed into the model.
    """
    rows = connection.execute(
        text(
            """
            SELECT transaction_id, is_fraud, transaction_amt, product_cd, transaction_dt
            FROM marts.fact_transactions
            ORDER BY transaction_id
            LIMIT :limit
            """
        ),
        {"limit": limit},
    ).mappings().all()

    return [
        {
            "transaction_id": row["transaction_id"],
            "is_fraud": row["is_fraud"],
            "transaction_amt": float(row["transaction_amt"]),
            "product_cd": row["product_cd"],
            "transaction_dt": row["transaction_dt"],
        }
        for row in rows
    ]


@router.get("/{transaction_id}")
def get_transaction(
    transaction_id: int = Path(gt=0, description="Transaction ID (must be positive)"),
    connection: Connection = Depends(get_connection),
):
    """Retrieve a full transaction from the warehouse (all columns)."""
    result = connection.execute(
        text(
            """
            SELECT * FROM marts.fact_transactions
            WHERE transaction_id = :transaction_id
            """
        ),
        {"transaction_id": transaction_id},
    ).mappings().first()

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Transaction not found",
        )

    out = {}
    for key, val in result.items():
        if val is None:
            out[key] = None
        elif isinstance(val, (int, float, str, bool)):
            out[key] = val
        else:
            out[key] = str(val)
    return out


@router.get("/predictions/top", response_model=list[TopPredictionResponse])
def get_top_predictions(
    limit: int = Query(default=10, ge=1, le=100, description="Number of predictions to return (1-100)"),
    connection: Connection = Depends(get_connection),
):
    """Retrieve saved predictions ordered by fraud probability."""

    result = connection.execute(
        text(
            """
            SELECT
                p.transaction_id,
                p.is_fraud_actual,
                p.is_fraud_predicted,
                p.fraud_probability,
                f.transaction_amt,
                p.model_version
            FROM marts.predictions p
            JOIN marts.fact_transactions f ON f.transaction_id = p.transaction_id
            ORDER BY p.fraud_probability DESC
            LIMIT :limit
            """
        ),
        {"limit": limit},
    ).mappings().all()

    return [
        {
            "transaction_id": row["transaction_id"],
            "is_fraud_actual": row["is_fraud_actual"],
            "is_fraud_predicted": row["is_fraud_predicted"],
            "fraud_probability": float(row["fraud_probability"]),
            "transaction_amt": float(row["transaction_amt"]),
            "model_version": row["model_version"],
        }
        for row in result
    ]