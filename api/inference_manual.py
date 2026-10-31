"""
Phase 31: Manual-input XGBoost inference pipeline.

Uses the separately trained xgboost_manual.pkl model which accepts only
user-providable features (no Vesta-engineered v-features or id-features).

This model is used for Mode B (Manual Transaction Testing) where the user
enters a few basic transaction fields. The model is weaker than the full
IEEE-CIS model because it has fewer features, but it can inference on
arbitrary user input without requiring a database lookup.
"""
from pathlib import Path
from typing import Any

import joblib
import json
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODELS_DIR = PROJECT_ROOT / "ml" / "models"

MANUAL_MODEL_VERSION = "xgboost-manual-v1"
MANUAL_THRESHOLD_DEFAULT = 0.5


class ManualInferencePipeline:
    """Load and run the manual-input XGBoost model."""

    def __init__(self):
        self.model = None
        self.preprocessor = None
        self.feature_columns = None  # raw feature columns
        self.processed_feature_names = None
        self.threshold = MANUAL_THRESHOLD_DEFAULT
        self._loaded = False
        self.metadata = None

    def load(self):
        """Load all artifacts from ml/models/."""
        self.model = joblib.load(MODELS_DIR / "xgboost_manual.pkl")
        self.preprocessor = joblib.load(MODELS_DIR / "preprocessor_manual.pkl")

        with open(MODELS_DIR / "feature_columns_manual.json") as f:
            self.feature_columns = json.load(f)

        with open(MODELS_DIR / "feature_names_processed_manual.json") as f:
            self.processed_feature_names = json.load(f)

        with open(MODELS_DIR / "threshold_manual.json") as f:
            self.threshold = json.load(f)["threshold"]

        with open(MODELS_DIR / "model_metadata_manual.json") as f:
            self.metadata = json.load(f)

        self._loaded = True

    def _ensure_loaded(self):
        if not self._loaded:
            self.load()

    def _prepare_input(self, transaction: dict[str, Any]) -> pd.DataFrame:
        """Build a DataFrame with all required raw features, filling missing."""
        row = {}
        for col in self.feature_columns:
            if col in transaction:
                row[col] = transaction[col]
            else:
                row[col] = None
        # Keep transaction_dt for time feature engineering
        if "transaction_dt" in transaction:
            row["_transaction_dt"] = transaction["transaction_dt"]
        df = pd.DataFrame([row])
        # Engineer time features
        if "_transaction_dt" in df.columns:
            dt = df["_transaction_dt"]
            df["transaction_hour"] = (dt % 86400 // 3600).astype("float64")
            df["transaction_dayofweek"] = ((dt // 86400) % 7).astype("float64")
            df["is_weekend"] = df["transaction_dayofweek"].isin([5, 6]).astype("float64")
            df = df.drop(columns=["_transaction_dt"])
        else:
            # Default time features if no transaction_dt provided
            df["transaction_hour"] = 12.0
            df["transaction_dayofweek"] = 0.0
            df["is_weekend"] = 0.0
        return df

    def predict_proba(self, transaction: dict[str, Any]) -> float:
        """Run inference and return fraud probability."""
        self._ensure_loaded()
        df = self._prepare_input(transaction)
        # Ensure all feature columns present
        for col in self.feature_columns:
            if col not in df.columns:
                df[col] = None
        df = df[self.feature_columns]
        X_proc = self.preprocessor.transform(df)
        proba = float(self.model.predict_proba(X_proc)[:, 1][0])
        return proba

    def predict(self, transaction: dict[str, Any]) -> dict[str, Any]:
        """Run inference and return full result dict."""
        self._ensure_loaded()
        proba = self.predict_proba(transaction)
        is_fraud = int(proba >= self.threshold)
        if proba >= 0.7:
            risk_level = "high"
        elif proba >= 0.3:
            risk_level = "medium"
        else:
            risk_level = "low"
        return {
            "fraud_probability": proba,
            "is_fraud_predicted": is_fraud,
            "threshold": self.threshold,
            "risk_level": risk_level,
            "model_version": MANUAL_MODEL_VERSION,
        }


# Global instance
_manual_pipeline = None


def get_manual_pipeline() -> ManualInferencePipeline:
    global _manual_pipeline
    if _manual_pipeline is None:
        _manual_pipeline = ManualInferencePipeline()
    return _manual_pipeline


def load_manual_pipeline() -> ManualInferencePipeline:
    pipeline = get_manual_pipeline()
    pipeline.load()
    return pipeline
