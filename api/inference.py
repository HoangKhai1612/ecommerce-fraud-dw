"""
Inference utilities for the FastAPI prediction endpoint.

Loads model artifacts and provides a unified prediction interface.
"""

import json
import warnings
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

MODEL_DIR = Path(__file__).resolve().parent.parent / "ml" / "models"

MODEL_PATH = MODEL_DIR / "xgboost.pkl"
FEATURE_COLS_PATH = MODEL_DIR / "feature_columns.json"
FREQ_ENCODER_PATH = MODEL_DIR / "frequency_encoder.pkl"
PREPROCESSOR_PATH = MODEL_DIR / "preprocessor.pkl"

MODEL_VERSION = "xgboost-v1-phase16"
THRESHOLD = 0.5


class InferencePipeline:
    """
    Encapsulates the full inference pipeline:
    - Feature engineering (time features, missing indicators, amount bins)
    - Frequency encoding (fitted on training data)
    - Preprocessing (ColumnTransformer: impute + scale numeric, impute + one-hot categorical)
    - Model prediction
    """

    def __init__(self):
        self.model = None
        self.feature_cols = None
        self.frequency_encoder = None
        self.preprocessor = None
        self._loaded = False

    def load(self):
        """Load all artifacts."""
        if self._loaded:
            return

        print("Loading model artifacts...")

        # Load model
        self.model = joblib.load(MODEL_PATH)
        print(f"  Model loaded: {type(self.model).__name__}")

        # Load feature columns (final 1014 features after ColumnTransformer)
        with open(FEATURE_COLS_PATH, "r") as f:
            self.feature_cols = json.load(f)
        print(f"  Feature columns: {len(self.feature_cols)}")

        # Load frequency encoder
        self.frequency_encoder = joblib.load(FREQ_ENCODER_PATH)
        print(f"  Frequency encoder loaded")

        # Load preprocessor
        self.preprocessor = joblib.load(PREPROCESSOR_PATH)
        print(f"  Preprocessor loaded")

        self._loaded = True
        print("All artifacts loaded successfully!")

    def _engineer_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply deterministic feature engineering (same as training)."""
        from ml.features.engineering import add_all_engineered_features

        return add_all_engineered_features(df)

    def _encode_frequency(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply frequency encoding."""
        return self.frequency_encoder.transform(df)

    def _preprocess(self, df: pd.DataFrame) -> np.ndarray:
        """Apply the fitted preprocessor (ColumnTransformer) and align to original feature list."""
        # The preprocessor was fitted on columns after feature engineering + frequency encoding
        # We need to prepare the dataframe for sklearn (same as _prepare_df_for_sklearn)
        from ml.features.preprocessing import _prepare_df_for_sklearn

        numeric_features = self.preprocessor.transformers[0][2]
        categorical_features = self.preprocessor.transformers[1][2]

        df_clean = _prepare_df_for_sklearn(df, numeric_features, categorical_features)
        X_processed = self.preprocessor.transform(df_clean)

        # Get feature names from preprocessor
        feature_names = self.preprocessor.get_feature_names_out()

        # Align to original feature_columns.json (model expects exactly these 1014 features in this order)
        # Create a DataFrame with the transformed features
        X_df = pd.DataFrame(X_processed, columns=feature_names, index=df_clean.index)

        # Reindex to match original feature columns (add missing as 0, drop extra)
        X_aligned = X_df.reindex(columns=self.feature_cols, fill_value=0)

        if X_aligned.shape[1] != len(self.feature_cols):
            raise ValueError(
                f"Feature alignment failed: expected {len(self.feature_cols)}, got {X_aligned.shape[1]}"
            )

        return X_aligned.values

    def predict_proba(self, raw_df: pd.DataFrame) -> np.ndarray:
        """
        Run full inference pipeline on raw transaction data.

        Args:
            raw_df: DataFrame with raw transaction columns (same as marts.fact_transactions)

        Returns:
            Array of fraud probabilities (class 1)
        """
        if not self._loaded:
            self.load()

        # Ensure all expected raw columns are present (fill missing with NaN)
        # The feature engineering expects the full raw schema
        expected_raw_columns = self._get_expected_raw_columns()
        for col in expected_raw_columns:
            if col not in raw_df.columns:
                raw_df[col] = np.nan

        # 1. Feature engineering
        df = self._engineer_features(raw_df)

        # 2. Frequency encoding
        df = self._encode_frequency(df)

        # 3. Preprocessing (ColumnTransformer) - this produces the 1014 features
        X_processed = self._preprocess(df)

        # 4. Verify feature count matches
        if X_processed.shape[1] != len(self.feature_cols):
            raise ValueError(
                f"Feature count mismatch after preprocessing: "
                f"expected {len(self.feature_cols)}, got {X_processed.shape[1]}"
            )

        # 5. Model prediction
        if hasattr(self.model, "predict_proba"):
            proba = self.model.predict_proba(X_processed)[:, 1]
        else:
            # For models without predict_proba (e.g., some sklearn models)
            decision = self.model.decision_function(X_processed)
            proba = 1 / (1 + np.exp(-decision))

        return proba

    def _get_expected_raw_columns(self) -> list[str]:
        """Get the list of expected raw transaction columns from the preprocessor's feature names."""
        # The preprocessor was fitted on data after feature engineering + frequency encoding
        # We need to infer the raw columns from the numeric/categorical feature names
        # For simplicity, return a comprehensive list based on the known schema
        # This matches the columns in marts.fact_transactions
        return [
            "transaction_key", "transaction_id", "is_fraud", "transaction_dt",
            "product_key", "device_key", "transaction_amt", "product_cd",
            "card1", "card2", "card3", "card4", "card5", "card6",
            "addr1", "addr2", "dist1", "dist2",
            "p_emaildomain", "r_emaildomain",
            *[f"c{i}" for i in range(1, 15)],
            *[f"d{i}" for i in range(1, 16)],
            *[f"v{i}" for i in range(1, 340)],
            *[f"id_{i:02d}" for i in range(1, 39)],
            *[f"m{i}" for i in range(1, 10)],
            "device_type", "device_info",
        ]

    def predict(self, raw_df: pd.DataFrame) -> np.ndarray:
        """Predict class labels."""
        proba = self.predict_proba(raw_df)
        return (proba >= THRESHOLD).astype(int)


# Global instance for FastAPI lifespan
_inference_pipeline: InferencePipeline | None = None


def get_inference_pipeline() -> InferencePipeline:
    """Get or create the global inference pipeline."""
    global _inference_pipeline
    if _inference_pipeline is None:
        _inference_pipeline = InferencePipeline()
    return _inference_pipeline


def load_inference_pipeline() -> InferencePipeline:
    """Load the inference pipeline (for startup)."""
    pipeline = get_inference_pipeline()
    pipeline.load()
    return pipeline