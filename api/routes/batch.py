"""EXT-06: synchronous batch fraud prediction with durable result storage."""

import csv
import io
import json
import logging
import os
import uuid
from functools import lru_cache
from pathlib import Path
from typing import Optional

import joblib
import numpy as np
import pandas as pd
from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import StreamingResponse
from starlette.concurrency import run_in_threadpool

from api.inference import MODEL_DIR, MODEL_VERSION, THRESHOLD, get_inference_pipeline

router = APIRouter(prefix="/predictions/batch", tags=["batch-prediction"])
logger = logging.getLogger(__name__)

# Keep batch state across API worker restarts. Override this path in deployments
# that use a mounted persistent volume.
UPLOAD_DIR = Path(
    os.getenv(
        "BATCH_PREDICTION_STORAGE_DIR",
        str(Path(__file__).resolve().parents[2] / "batch_uploads"),
    )
)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

_MODEL_FILES = {
    "xgboost": ("xgboost.pkl", MODEL_VERSION),
    "lightgbm": ("lightgbm.pkl", "lightgbm-v1-phase30"),
    "random_forest": ("random_forest.pkl", "random_forest-artifact"),
    "logistic_regression": ("logistic_regression.pkl", "logistic_regression-artifact"),
}
_MODEL_ALIASES = {
    "xgboost": "xgboost",
    "xgb": "xgboost",
    "lightgbm": "lightgbm",
    "lgbm": "lightgbm",
    "random_forest": "random_forest",
    "random forest": "random_forest",
    "random-forest": "random_forest",
    "logistic_regression": "logistic_regression",
    "logistic regression": "logistic_regression",
    "logistic-regression": "logistic_regression",
}

# CSV header -> raw feature names expected by the trained preprocessing pipeline.
_COL_REMAP = {
    "TransactionID": "transaction_id",
    "TransactionDT": "transaction_dt",
    "TransactionAmt": "transaction_amt",
    "ProductCD": "product_cd",
    "P_emaildomain": "p_emaildomain",
    "R_emaildomain": "r_emaildomain",
    "DeviceType": "device_type",
    "DeviceInfo": "device_info",
    "isFraud": "is_fraud",
    **{f"C{i}": f"c{i}" for i in range(1, 15)},
    **{f"D{i}": f"d{i}" for i in range(1, 16)},
    **{f"V{i}": f"v{i}" for i in range(1, 340)},
    **{f"M{i}": f"m{i}" for i in range(1, 10)},
    **{f"id_{i}": f"id_{i:02d}" for i in range(1, 39)},
    **{f"id-{i:02d}": f"id_{i:02d}" for i in range(1, 39)},
    **{f"card{i}": f"card{i}" for i in range(1, 7)},
    **{f"Card{i}": f"card{i}" for i in range(1, 7)},
    "addr1": "addr1", "Addr1": "addr1",
    "addr2": "addr2", "Addr2": "addr2",
    "dist1": "dist1", "Dist1": "dist1",
    "dist2": "dist2", "Dist2": "dist2",
}


def _normalise_columns(df: pd.DataFrame) -> pd.DataFrame:
    rename_map = {col: _COL_REMAP[col] for col in df.columns if col in _COL_REMAP}
    return df.rename(columns=rename_map) if rename_map else df


def _canonical_model_name(value: str | None) -> str:
    key = (value or "xgboost").strip().lower()
    model_name = _MODEL_ALIASES.get(key)
    if model_name is None:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported model '{value}'. Choose one of: {', '.join(_MODEL_FILES)}",
        )
    return model_name


@lru_cache(maxsize=len(_MODEL_FILES) - 1)
def _load_comparison_model(model_name: str):
    filename, _ = _MODEL_FILES[model_name]
    path = MODEL_DIR / filename
    if not path.is_file():
        raise FileNotFoundError(f"Model artifact not found: {path.name}")
    return joblib.load(path)


@lru_cache(maxsize=1)
def _load_logistic_scaler():
    path = MODEL_DIR / "logistic_scaler.pkl"
    if not path.is_file():
        raise FileNotFoundError("Model artifact not found: logistic_scaler.pkl")
    return joblib.load(path)


def _predict_probabilities(df: pd.DataFrame, model_name: str) -> tuple[np.ndarray, float, str]:
    """Use the trained feature pipeline and the selected Phase 30 model artifact."""
    pipeline = get_inference_pipeline()
    if model_name == "xgboost":
        probabilities = np.asarray(pipeline.predict_proba(df.copy()), dtype=float).reshape(-1)
        return probabilities, float(getattr(pipeline, "threshold", THRESHOLD)), _MODEL_FILES[model_name][1]

    # The comparison estimators were trained on the same engineered feature
    # matrix as XGBoost. Logistic Regression additionally requires its fitted scaler.
    if not pipeline._loaded:
        pipeline.load()
    expected = pipeline._get_expected_raw_columns()
    prepared = df.copy()
    for column in expected:
        if column not in prepared.columns:
            prepared[column] = np.nan
    engineered = pipeline._engineer_features(prepared)
    encoded = pipeline._encode_frequency(engineered)
    features = pipeline._preprocess(encoded)

    model = _load_comparison_model(model_name)
    if model_name == "logistic_regression":
        features = _load_logistic_scaler().transform(features)
    if not hasattr(model, "predict_proba"):
        raise RuntimeError(f"{model_name} artifact does not expose predict_proba")
    class_labels = list(getattr(model, "classes_", [0, 1]))
    if 1 not in class_labels:
        raise RuntimeError(f"{model_name} artifact has no fraud class (label 1)")
    probabilities = np.asarray(model.predict_proba(features)[:, class_labels.index(1)], dtype=float)
    return probabilities.reshape(-1), THRESHOLD, _MODEL_FILES[model_name][1]


def _risk_level(probability: float) -> str:
    if probability >= 0.7:
        return "high"
    if probability >= 0.3:
        return "medium"
    return "low"


def _json_safe(value):
    if value is None or value is pd.NA:
        return None
    if isinstance(value, (np.integer, np.floating, np.bool_)):
        value = value.item()
    if isinstance(value, float) and not np.isfinite(value):
        return None
    if isinstance(value, (pd.Timestamp,)):
        return value.isoformat()
    if pd.isna(value):
        return None
    if isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


def _summary_stats(results: list[dict]) -> dict:
    if not results:
        return {
            "fraud_count": 0, "legit_count": 0,
            "high_risk_count": 0, "medium_risk_count": 0, "low_risk_count": 0,
            "avg_fraud_probability": None, "max_fraud_probability": None,
            "min_fraud_probability": None, "fraud_rate_pct": 0.0,
        }
    probabilities = [r["fraud_probability"] for r in results]
    fraud_count = sum(r["predicted_label"] == 1 for r in results)
    return {
        "fraud_count": fraud_count,
        "legit_count": len(results) - fraud_count,
        "high_risk_count": sum(r["risk_level"] == "high" for r in results),
        "medium_risk_count": sum(r["risk_level"] == "medium" for r in results),
        "low_risk_count": sum(r["risk_level"] == "low" for r in results),
        "avg_fraud_probability": round(float(np.mean(probabilities)), 6),
        "max_fraud_probability": round(float(np.max(probabilities)), 6),
        "min_fraud_probability": round(float(np.min(probabilities)), 6),
        "fraud_rate_pct": round(fraud_count / len(results) * 100, 2),
    }


def _batch_path(batch_id: str) -> Path:
    # Avoid path traversal: only server-generated UUID names are accepted.
    try:
        safe_id = str(uuid.UUID(batch_id))
    except (ValueError, AttributeError) as exc:
        raise HTTPException(status_code=404, detail="Batch not found") from exc
    return UPLOAD_DIR / f"{safe_id}.json"


def _save_batch(batch_id: str, data: dict) -> None:
    path = _batch_path(batch_id)
    temp_path = path.with_suffix(f".{uuid.uuid4().hex}.tmp")
    try:
        temp_path.write_text(json.dumps(data, ensure_ascii=False, allow_nan=False), encoding="utf-8")
        os.replace(temp_path, path)
    finally:
        if temp_path.exists():
            temp_path.unlink()


def _get_batch(batch_id: str) -> dict:
    path = _batch_path(batch_id)
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Batch not found or expired") from exc
    except (OSError, json.JSONDecodeError) as exc:
        logger.exception("Unable to read batch result %s", batch_id)
        raise HTTPException(status_code=500, detail="Stored batch result is unreadable") from exc


@router.post("")
async def create_batch_prediction(
    file: UploadFile = File(...),
    model_name: Optional[str] = Form(default="xgboost"),
):
    """Run inference for each CSV row, persist the result, and return a preview."""
    if not (file.filename or "").lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")
    content = await file.read()
    if len(content) > 50 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large (max 50 MB)")
    try:
        source_df = pd.read_csv(io.BytesIO(content))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid CSV: {exc}") from exc
    if source_df.empty:
        raise HTTPException(status_code=400, detail="CSV file is empty")
    if len(source_df) > 100_000:
        raise HTTPException(status_code=400, detail="Too many rows (max 100 000)")

    selected_model = _canonical_model_name(model_name)
    df = _normalise_columns(source_df.copy())
    if not df.columns.is_unique:
        raise HTTPException(status_code=400, detail="CSV contains duplicate columns after header normalization")
    required = ["transaction_dt", "transaction_amt", "product_cd"]
    missing = [column for column in required if column not in df.columns or df[column].isna().all()]
    if missing:
        raise HTTPException(status_code=400, detail=f"CSV is missing required columns: {', '.join(missing)}")

    tid_col = "transaction_id" if "transaction_id" in df.columns else None
    transaction_ids = df[tid_col].tolist() if tid_col else list(range(1, len(df) + 1))
    batch_id = str(uuid.uuid4())
    filename = Path(file.filename or "batch.csv").name
    model_version = _MODEL_FILES[selected_model][1]

    try:
        probabilities, threshold, model_version = await run_in_threadpool(
            _predict_probabilities, df, selected_model
        )
        if len(probabilities) != len(df):
            raise RuntimeError(f"Expected {len(df)} predictions, received {len(probabilities)}")
        if not np.isfinite(probabilities).all() or (probabilities < 0).any() or (probabilities > 1).any():
            raise RuntimeError("Model returned invalid fraud probabilities")

        results = []
        for index, probability in enumerate(probabilities):
            probability = float(probability)
            label = int(probability >= threshold)
            results.append({
                "row_index": index + 1,
                "transaction_id": _json_safe(transaction_ids[index]),
                "fraud_probability": round(probability, 6),
                "predicted_label": label,
                "prediction": "GIAN_LUAN" if label else "HOP_LE",
                "risk_level": _risk_level(probability),
                "threshold": round(float(threshold), 4),
                "model_name": selected_model,
                "model_version": model_version,
            })

        stats = _summary_stats(results)
        stored = {
            "batch_id": batch_id, "status": "completed", "total_rows": len(df),
            "successful": len(results), "failed": 0, "filename": filename,
            "model_name": selected_model, "model_version": model_version,
            "threshold": round(float(threshold), 4), "statistics": stats,
            "results": results,
        }
        _save_batch(batch_id, stored)
        return {
            "batch_id": batch_id, "status": "completed", "total_rows": len(df),
            "successful": len(results), "failed": 0,
            "fraud_detected": stats["fraud_count"], "legit": stats["legit_count"],
            "filename": filename, "model_name": selected_model,
            "model_version": model_version, "threshold": round(float(threshold), 4),
            "statistics": stats, "results_preview": results[:100],
            "results_total": len(results),
            "message": (
                f"Đã chạy {selected_model} cho {len(df)} bản ghi; "
                f"phát hiện {stats['fraud_count']} giao dịch có nhãn gian lận "
                f"({stats['fraud_rate_pct']}%). Xác suất trung bình: "
                f"{stats['avg_fraud_probability']:.4f}."
            ),
        }
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Batch inference failed for %s", batch_id)
        failed_result = {
            "batch_id": batch_id, "status": "failed", "total_rows": len(df),
            "successful": 0, "failed": len(df), "filename": filename,
            "model_name": selected_model, "model_version": model_version,
            "statistics": _summary_stats([]), "results": [],
            "error_detail": str(exc)[:500],
        }
        try:
            _save_batch(batch_id, failed_result)
        except OSError:
            logger.exception("Unable to persist failed batch %s", batch_id)
        return {
            "batch_id": batch_id, "status": "failed", "total_rows": len(df),
            "successful": 0, "failed": len(df), "fraud_detected": 0,
            "legit": 0, "filename": filename, "model_name": selected_model,
            "model_version": model_version, "error_detail": str(exc)[:500],
            "message": f"Không thể xử lý batch: {str(exc)[:300]}",
        }


@router.get("/{batch_id}")
def get_batch_status(
    batch_id: str,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
):
    """Return persisted batch status and a page of its per-row predictions."""
    stored = _get_batch(batch_id)
    results = stored.get("results", [])
    stats = stored.get("statistics") or _summary_stats(results)
    status_value = stored.get("status", "failed")
    response = {
        "batch_id": stored["batch_id"], "status": status_value,
        "total_rows": stored.get("total_rows", len(results)),
        "successful": stored.get("successful", len(results)),
        "failed": stored.get("failed", 0),
        "fraud_detected": stats.get("fraud_count", 0),
        "legit": stats.get("legit_count", 0),
        "filename": stored.get("filename"), "model_name": stored.get("model_name"),
        "model_version": stored.get("model_version"),
        "threshold": stored.get("threshold"), "statistics": stats,
        # Keep the legacy results property; pagination is additive.
        "results": results[offset:offset + limit],
        "results_total": len(results), "offset": offset, "limit": limit,
        "message": stored.get("error_detail") or (
            f"Hoàn thành {stored.get('successful', len(results))}/"
            f"{stored.get('total_rows', len(results))} bản ghi."
            if status_value == "completed" else "Batch xử lý thất bại."
        ),
    }
    if status_value == "failed":
        response["error_detail"] = stored.get("error_detail")
    return response


@router.get("/{batch_id}/download")
def download_batch_results(batch_id: str):
    """Download every persisted row result as a UTF-8 CSV."""
    stored = _get_batch(batch_id)
    if stored.get("status") != "completed":
        raise HTTPException(status_code=409, detail="Batch has no completed results")
    output = io.StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow([
        "row_index", "transaction_id", "fraud_probability", "predicted_label",
        "prediction", "risk_level", "threshold", "model_name", "model_version",
    ])
    for result in stored.get("results", []):
        writer.writerow([
            result.get("row_index"), result.get("transaction_id"),
            result.get("fraud_probability"), result.get("predicted_label"),
            result.get("prediction"), result.get("risk_level"),
            result.get("threshold"), result.get("model_name"), result.get("model_version"),
        ])
    output.seek(0)
    content = "\ufeff" + output.getvalue()
    return StreamingResponse(
        iter([content]), media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename=batch_{stored['batch_id']}_results.csv"},
    )
