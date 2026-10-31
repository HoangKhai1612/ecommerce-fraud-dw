"""Model comparison and metadata endpoints."""
from fastapi import APIRouter
from typing import Any
import json
from pathlib import Path

router = APIRouter(prefix="/models", tags=["Models"])

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
MODEL_DIR = PROJECT_ROOT / "ml" / "models"


@router.get("/comparison")
def get_model_comparison() -> Any:
    try:
        comparison_path = MODEL_DIR / "model_comparison_phase30.json"
        if comparison_path.exists():
            with open(comparison_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data
    except Exception:
        pass
    
    # Fallback to training results + lightgbm metadata
    models = []
    try:
        training_path = MODEL_DIR / "training_results.json"
        if training_path.exists():
            with open(training_path, "r", encoding="utf-8") as f:
                tr = json.load(f)
            for m in tr.get("models", []):
                models.append({
                    "name": m["model"],
                    "roc_auc": m["roc_auc"],
                    "pr_auc": m["pr_auc"],
                    "precision": m["precision"],
                    "recall": m["recall"],
                    "f1": m["f1"],
                })
    except Exception:
        pass
    
    try:
        lgb_path = MODEL_DIR / "lightgbm_metadata.json"
        if lgb_path.exists():
            with open(lgb_path, "r", encoding="utf-8") as f:
                lm = json.load(f)
            met = lm.get("metrics", {})
            models.append({
                "name": "LightGBM",
                "roc_auc": met.get("roc_auc"),
                "pr_auc": met.get("pr_auc"),
                "precision": met.get("precision"),
                "recall": met.get("recall"),
                "f1": met.get("f1"),
                "training_time_seconds": met.get("training_time_seconds"),
                "prediction_time_seconds": met.get("prediction_time_seconds"),
            })
    except Exception:
        pass
    
    return {"models": models}
