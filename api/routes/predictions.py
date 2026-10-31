"""
Phase 31: prediction endpoints for the integrated testing platform.

Endpoints:
- POST   /predictions            run real XGBoost inference + persist
- GET    /predictions/{id}       get one prediction record
- GET    /predictions            list history with filters + pagination
- POST   /predictions/{id}/explain AI explanation from the REAL prediction
- GET    /transactions/sample    sample raw transactions for mode A (read-only)

Reuses api.inference.InferencePipeline (real XGBoost) and
api.services.prediction_service.PredictionService.
"""

import logging
from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request, status

from api.config import limiter
from api.database import (
    check_database,
    ensure_history_table,
    get_connection,
    insert_prediction_record,
    list_prediction_records,
    save_ai_explanation,
)
from api.inference import MODEL_VERSION, THRESHOLD, get_inference_pipeline
from api.models import (
    ErrorResponse,
    ExplainRequest,
    ExplainResponse,
    PredictionCreate,
    PredictionDetail,
    PredictionListItem,
    PredictionRecord,
    PredictionsFilter,
    PredictionsListResponse,
)
from api.services.ai_service import AIService
from api.services.prediction_service import PredictionService

router = APIRouter(prefix="/predictions", tags=["Predictions (Phase 31)"])
logger = logging.getLogger(__name__)


def _iso(value: Any) -> str | None:
    if value is None:
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def _get_prediction_service() -> PredictionService:
    return PredictionService()


def _get_ai_service() -> AIService:
    return AIService()


@router.on_event("startup")
def _ensure_history_table_on_startup() -> None:
    ensure_history_table()


@router.post(
    "",
    response_model=PredictionRecord,
    status_code=status.HTTP_201_CREATED,
    responses={400: {"model": ErrorResponse}, 503: {"model": ErrorResponse}},
)
@limiter.limit("10/minute")
def create_prediction(
    request: Request,
    data: PredictionCreate,
    service: PredictionService = Depends(_get_prediction_service),
) -> Any:
    """
    Run real XGBoost inference on one transaction and persist the result.

    The model is NOT mocked: if XGBoost artifacts cannot be loaded or
    inference fails, the endpoint returns 503 and never invents a score.
    """
    try:
        return service.predict_and_save(
            input_mode=data.mode,
            transaction=data.transaction.model_dump(),
            transaction_id_for_history=data.transaction.transaction_id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        ) from exc


@router.get(
    "/{prediction_id}",
    response_model=PredictionDetail,
    responses={404: {"model": ErrorResponse}, 503: {"model": ErrorResponse}},
)
def get_prediction(
    prediction_id: str = Path(..., description="Prediction ID (UUID)"),
    service: PredictionService = Depends(_get_prediction_service),
) -> Any:
    """Get one persisted prediction record by ID."""
    try:
        record = service.get_record(prediction_id)
    except Exception as exc:  # database unavailable
        logger.exception("Failed to read prediction %s", prediction_id)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database unavailable",
        ) from exc

    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prediction not found",
        )

    input_payload = record.get("input_payload")
    if isinstance(input_payload, str):
        import json

        input_payload = json.loads(input_payload)

    return {
        "prediction_id": record["prediction_id"],
        "transaction_id": record.get("transaction_id"),
        "model_version": record["model_version"],
        "input_mode": record["input_mode"],
        "input_payload": input_payload or {},
        "is_fraud_predicted": record["is_fraud_predicted"],
        "fraud_probability": float(record["fraud_probability"]),
        "threshold": float(record["threshold"]),
        "risk_level": (
            "high"
            if record["fraud_probability"] >= 0.7
            else "medium"
            if record["fraud_probability"] >= 0.3
            else "low"
        ),
        "message": (
            "Fraud detected"
            if record["is_fraud_predicted"] == 1
            else "Transaction appears legitimate"
        ),
        "predicted_at": _iso(record["predicted_at"]),
        "ai_available": bool(record.get("ai_available")),
        "ai_explanation": record.get("ai_explanation"),
        "ai_explanation_at": _iso(record.get("ai_explanation_at")),
        "status": record["status"],
    }


@router.get("", response_model=PredictionsListResponse)
def list_predictions(
    input_mode: str | None = Query(
        default=None, description="Filter by input mode"
    ),
    is_fraud_predicted: int | None = Query(
        default=None, ge=0, le=1, description="Filter by prediction label"
    ),
    min_probability: float | None = Query(
        default=None, ge=0.0, le=1.0, description="Min fraud probability"
    ),
    max_probability: float | None = Query(
        default=None, ge=0.0, le=1.0, description="Max fraud probability"
    ),
    from_predicted_at: str | None = Query(
        default=None, description="From predicted_at (ISO-8601)"
    ),
    to_predicted_at: str | None = Query(
        default=None, description="To predicted_at (ISO-8601)"
    ),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> Any:
    """List prediction history with filters and pagination."""
    try:
        items, total = list_prediction_records(
            filter=PredictionsFilter(
                input_mode=input_mode,
                is_fraud_predicted=is_fraud_predicted,
                min_probability=min_probability,
                max_probability=max_probability,
                from_predicted_at=from_predicted_at,
                to_predicted_at=to_predicted_at,
            ),
            limit=limit,
            offset=offset,
        )
    except Exception as exc:
        logger.exception("Failed to list predictions")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database unavailable",
        ) from exc

    return {
        "items": items,
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.post(
    "/{prediction_id}/explain",
    response_model=ExplainResponse,
    responses={404: {"model": ErrorResponse}, 503: {"model": ErrorResponse}},
)
@limiter.limit("5/minute")
def explain_prediction(
    request: Request,
    prediction_id: str = Path(..., description="Prediction ID (UUID)"),
    data: ExplainRequest | None = None,
    service: PredictionService = Depends(_get_prediction_service),
    ai: AIService = Depends(_get_ai_service),
) -> Any:
    """
    Generate an AI explanation for a REAL prediction.

    The AI receives only the prediction context computed from the stored
    record (score, label, model version, input). It cannot override the
    model result. If Ollama/AI Assistant is unavailable, the prediction
    remains valid and ai_available is false.
    """
    try:
        record = service.get_record(prediction_id)
    except Exception as exc:
        logger.exception("Failed to read prediction %s for explain", prediction_id)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database unavailable",
        ) from exc

    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prediction not found",
        )

    try:
        result = ai.explain(
            prediction_id=prediction_id,
            record=record,
            question=(data.question if data else None),
        )
    except Exception as exc:  # never let AI failure break the prediction
        logger.exception("AI explanation failed for %s", prediction_id)
        result = {
            "answer": (
                "AI Assistant thang loi xu ly yeu cau. Du doan XGBoost van luu "
                "tru va co the xem lai, nhung chua co giai thich tu AI."
            ),
            "ai_available": False,
            "source": "unavailable",
        }

    try:
        save_ai_explanation(
            prediction_id=prediction_id,
            explanation=result["answer"],
            ai_available=bool(result.get("ai_available")),
        )
    except Exception as exc:
        logger.exception("Failed to persist AI explanation for %s", prediction_id)

    return {
        "prediction_id": prediction_id,
        "answer": result["answer"],
        "ai_available": bool(result.get("ai_available")),
        "source": result.get("source", "unavailable"),
    }
