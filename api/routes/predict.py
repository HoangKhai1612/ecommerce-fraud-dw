"""Fraud prediction endpoint."""

from fastapi import APIRouter, Depends, HTTPException, Request, status

from api.config import limiter
from api.inference import InferencePipeline, get_inference_pipeline, MODEL_VERSION
from api.models import PredictionResponse, TransactionRaw

router = APIRouter(prefix="/predict", tags=["Prediction"])


def _risk_level(probability: float) -> str:
    """Classify risk level based on fraud probability.

    Thresholds are operational choices, not statistically optimal values.
    Default threshold (0.5) is used for binary classification.
    """
    if probability >= 0.7:
        return "high"
    if probability >= 0.3:
        return "medium"
    return "low"


@router.post("", response_model=PredictionResponse)
@limiter.limit("10/minute")
def predict_fraud(
    request: Request,
    data: TransactionRaw,
    pipeline: InferencePipeline = Depends(get_inference_pipeline),
):
    """
    Predict fraud probability for a single transaction.

    The input transaction is converted to a DataFrame, passed through
    the full inference pipeline (feature engineering -> frequency encoding
    -> preprocessing -> model), and returns the fraud probability
    and binary prediction using the default 0.5 threshold.

    Note: The 0.5 threshold is an operational choice. The model's
    ROC-AUC on the test set is 0.917. Precision/Recall at 0.5 are
    0.32/0.71 respectively (Phase 17/19 results).
    """
    # Ensure model is loaded
    if not pipeline._loaded:
        try:
            pipeline.load()
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Model not available: {e}",
            )

    # Convert request to DataFrame
    input_dict = data.model_dump()
    transaction_id = input_dict.pop("transaction_id")

    # Create DataFrame with single row
    import pandas as pd
    df = pd.DataFrame([input_dict])

    # Ensure required columns exist
    required_cols = ["transaction_dt", "transaction_amt", "product_cd"]
    for col in required_cols:
        if col not in df.columns or df[col].isna().all():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Missing required field: {col}",
            )

    # Run inference
    try:
        proba = pipeline.predict_proba(df)[0]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Inference failed: {e}",
        )

    # Binary prediction using default threshold
    is_fraud = int(proba >= 0.5)

    return {
        "transaction_id": transaction_id,
        "is_fraud": is_fraud,
        "fraud_probability": float(proba),
        "risk_level": _risk_level(proba),
        "message": (
            "Fraud detected" if is_fraud else "Transaction appears legitimate"
        ),
        "model_version": MODEL_VERSION,
    }