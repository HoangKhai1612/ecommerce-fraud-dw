"""
Phase 31: prediction service.

Encapsulates online inference (XGBoost via api.inference) and persistence
of prediction records to marts.web_test_history.
"""

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

import pandas as pd

from api.database import insert_prediction_record
from api.inference import (
    InferencePipeline,
    MODEL_VERSION,
    THRESHOLD,
    get_inference_pipeline,
)
from api.inference_manual import (
    ManualInferencePipeline,
    MANUAL_MODEL_VERSION,
    get_manual_pipeline,
)


class PredictionService:
    """Run real XGBoost inference and persist the result."""

    def __init__(self, pipeline=None, manual_pipeline=None):
        self.pipeline = pipeline or get_inference_pipeline()
        self.manual_pipeline = manual_pipeline or get_manual_pipeline()

    def _ensure_loaded(self, manual=False):
        if manual:
            if not self.manual_pipeline._loaded:
                self.manual_pipeline.load()
        else:
            if not self.pipeline._loaded:
                self.pipeline.load()

    def predict_and_save(
        self,
        *,
        input_mode: str,
        transaction: dict[str, Any],
        transaction_id_for_history: int | None = None,
    ) -> dict[str, Any]:
        """
        Run inference on one raw transaction and persist the record.

        For 'ieee-cis' mode: uses the full XGBoost model (1014 features).
        For 'ecommerce-sim' mode: uses the manual-input model (40 features).

        Returns a dict matching PredictionRecord schema.
        Raises RuntimeError if the model is unavailable.
        """
        manual = (input_mode == "ecommerce-sim")
        self._ensure_loaded(manual=manual)

        if manual:
            pipeline = self.manual_pipeline
            model_version = MANUAL_MODEL_VERSION
            threshold = pipeline.threshold
        else:
            pipeline = self.pipeline
            model_version = MODEL_VERSION
            threshold = THRESHOLD

        df = pd.DataFrame([transaction])

        # Required raw columns
        required_cols = ["transaction_amt"]
        missing = [c for c in required_cols if c not in df.columns or (c in df.columns and df[c].isna().all())]
        if missing:
            raise ValueError(f"Missing required field: {', '.join(missing)}")

        try:
            if manual:
                proba = pipeline.predict_proba(transaction)
            else:
                required_raw = ["transaction_dt", "transaction_amt", "product_cd"]
                missing_raw = [c for c in required_raw if c not in df.columns or df[c].isna().all()]
                if missing_raw:
                    raise ValueError(f"Missing required field: {', '.join(missing_raw)}")
                proba = float(pipeline.predict_proba(df)[0])
        except ValueError:
            raise
        except Exception as exc:
            raise RuntimeError(f"Inference failed: {exc}") from exc

        is_fraud = int(proba >= threshold)
        prediction_id = str(uuid4())
        predicted_at = datetime.now(timezone.utc)

        tid = transaction_id_for_history
        if tid is None:
            tid = transaction.get("transaction_id")
        if tid is not None:
            try:
                tid = int(tid)
            except (ValueError, TypeError):
                tid = None
        if not tid:
            tid = None

        try:
            insert_prediction_record(
                prediction_id=prediction_id,
                transaction_id=tid,
                model_version=model_version,
                input_mode=input_mode,
                input_payload=transaction,
                is_fraud_predicted=is_fraud,
                fraud_probability=proba,
                threshold=threshold,
                predicted_at=predicted_at,
                ai_available=False,
                status="ok",
            )
        except Exception as exc:
            raise RuntimeError(f"Failed to persist prediction: {exc}") from exc

        return {
            "prediction_id": prediction_id,
            "transaction_id": tid,
            "model_version": model_version,
            "input_mode": input_mode,
            "is_fraud_predicted": is_fraud,
            "fraud_probability": proba,
            "threshold": threshold,
            "predicted_at": predicted_at.isoformat(),
            "ai_available": False,
            "ai_explanation": None,
            "ai_explanation_at": None,
            "status": "ok",
        }

    def get_record(self, prediction_id: str) -> dict[str, Any] | None:
        from api.database import get_prediction_record

        return get_prediction_record(prediction_id)

    def list_records(self, *, filter_params: dict | None = None, limit: int = 50, offset: int = 0):
        from api.database import list_prediction_records
        from api.models import PredictionsFilter

        f = None
        if filter_params:
            f = PredictionsFilter(**filter_params)
        return list_prediction_records(filter=f, limit=limit, offset=offset)
