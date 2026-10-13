"""Read-only transaction and prediction endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy import text
from sqlalchemy.engine import Connection

from api.database import get_connection
from api.models import TopPredictionResponse, TransactionResponse

router = APIRouter(prefix="/transactions", tags=["Transactions"])


@router.get("/{transaction_id}", response_model=TransactionResponse)
def get_transaction(
    transaction_id: int = Path(gt=0, description="Transaction ID (must be positive)"),
    connection: Connection = Depends(get_connection),
):
    """Retrieve a transaction from the warehouse."""

    result = connection.execute(
        text(
            """
            SELECT
                transaction_id,
                is_fraud,
                transaction_amt,
                product_cd,
                transaction_dt
            FROM marts.fact_transactions
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

    return {
        "transaction_id": result["transaction_id"],
        "is_fraud": result["is_fraud"],
        "transaction_amt": float(result["transaction_amt"]),
        "product_cd": result["product_cd"],
        "transaction_dt": result["transaction_dt"],
    }


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