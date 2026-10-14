"""Phase 25 — ML Model Tests.

Tests the ML model artifacts and inference pipeline.
Run from the project root:

    .venv\Scripts\python.exe -m pytest tests/test_ml.py -v

Design:
- Unit tests: verify artifacts exist, can be loaded, and produce valid predictions.
- Uses the real test.parquet data (engineered features) and real model artifacts.
- Does NOT retrain models.
"""

import json
import os
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODELS_DIR = PROJECT_ROOT / "ml" / "models"
DATA_DIR = PROJECT_ROOT / "ml" / "data"

# Expected artifacts from Phase 16/19
REQUIRED_ARTIFACTS = [
    "xgboost.pkl",
    "feature_columns.json",
    "frequency_encoder.pkl",
    "preprocessor.pkl",
    "logistic_regression.pkl",
    "logistic_scaler.pkl",
    "random_forest.pkl",
    "training_results.json",
]

EXPECTED_N_FEATURES = 1014
EXPECTED_MODEL_VERSION = "xgboost-v1-phase16"


# Module-level fixtures shared across all test classes


@pytest.fixture(scope="session")
def inference_pipeline():
    """Load the inference pipeline once per session."""
    from api.inference import InferencePipeline
    pipeline = InferencePipeline()
    pipeline.load()
    return pipeline


@pytest.fixture(scope="session")
def test_data():
    """Load the processed test.parquet (1014 features + is_fraud)."""
    path = DATA_DIR / "test.parquet"
    assert path.exists(), "test.parquet not found"
    df = pd.read_parquet(path)
    assert "is_fraud" in df.columns
    return df


@pytest.fixture(scope="session")
def test_predictions(inference_pipeline, test_data):
    """Generate predictions on test set once per session."""
    proba = inference_pipeline.predict_proba(test_data)
    preds = (proba >= 0.5).astype(int)
    return test_data["is_fraud"].values, preds, proba


class TestMLArtifacts:
    """Verify ML model artifacts exist and are loadable."""

    def test_artifacts_exist(self):
        for artifact in REQUIRED_ARTIFACTS:
            path = MODELS_DIR / artifact
            assert path.exists(), f"Missing artifact: {artifact}"
            assert path.stat().st_size > 0, f"Empty artifact: {artifact}"

    def test_feature_columns_json_valid(self):
        with open(MODELS_DIR / "feature_columns.json", "r") as f:
            cols = json.load(f)
        assert isinstance(cols, list)
        assert len(cols) == EXPECTED_N_FEATURES
        assert all(isinstance(c, str) for c in cols)

    def test_training_results_valid(self):
        with open(MODELS_DIR / "training_results.json", "r") as f:
            results = json.load(f)

        assert results["n_features"] == EXPECTED_N_FEATURES
        assert results["train_rows"] > 0
        assert results["validation_rows"] > 0
        assert len(results["models"]) == 3

        model_names = {m["model"] for m in results["models"]}
        assert model_names == {"Logistic Regression", "Random Forest", "XGBoost"}

        for model in results["models"]:
            for metric in ("roc_auc", "pr_auc", "precision", "recall", "f1"):
                value = model[metric]
                assert 0.0 <= value <= 1.0, (
                    f"{model['model']}.{metric}={value} out of [0,1]"
                )

    def test_xgboost_model_loads(self):
        model = joblib.load(MODELS_DIR / "xgboost.pkl")
        assert model is not None
        assert hasattr(model, "predict_proba")

    def test_preprocessor_loads(self):
        preprocessor = joblib.load(MODELS_DIR / "preprocessor.pkl")
        assert preprocessor is not None
        assert hasattr(preprocessor, "transform")

    def test_frequency_encoder_loads(self):
        encoder = joblib.load(MODELS_DIR / "frequency_encoder.pkl")
        assert encoder is not None
        assert hasattr(encoder, "transform")

    def test_logistic_regression_loads(self):
        model = joblib.load(MODELS_DIR / "logistic_regression.pkl")
        scaler = joblib.load(MODELS_DIR / "logistic_scaler.pkl")
        assert model is not None
        assert scaler is not None
        assert hasattr(model, "predict_proba")
        assert hasattr(scaler, "transform")

    def test_random_forest_loads(self):
        model = joblib.load(MODELS_DIR / "random_forest.pkl")
        assert model is not None
        assert hasattr(model, "predict_proba")


class TestMLInference:
    """Test the full inference pipeline using the FastAPI inference module."""

    def test_feature_count_matches_model(self, inference_pipeline):
        assert len(inference_pipeline.feature_cols) == EXPECTED_N_FEATURES

    def test_predict_proba_shape(self, inference_pipeline, test_data):
        """Run inference on test data and verify output shape."""
        # Use first 10 rows for speed
        sample = test_data.head(10)
        proba = inference_pipeline.predict_proba(sample)
        assert proba.shape == (10,)
        assert np.all((proba >= 0.0) & (proba <= 1.0))

    def test_predict_proba_full_test_set(self, inference_pipeline, test_data):
        """Run inference on full test set (slower, verifies full pipeline)."""
        proba = inference_pipeline.predict_proba(test_data)
        assert proba.shape == (len(test_data),)
        assert np.all((proba >= 0.0) & (proba <= 1.0))

    def test_predict_binary(self, inference_pipeline, test_data):
        """Test binary prediction with default threshold."""
        sample = test_data.head(10)
        preds = inference_pipeline.predict(sample)
        assert preds.shape == (10,)
        assert set(np.unique(preds)).issubset({0, 1})

    def test_missing_columns_handled(self, inference_pipeline):
        """Input missing raw columns should be filled with NaN."""
        # Create minimal raw transaction DataFrame
        df = pd.DataFrame([{
            "transaction_id": 1,
            "transaction_dt": 86400,
            "transaction_amt": 100.0,
            "product_cd": "W",
            "card1": 1001,
            "card4": "visa",
            "device_type": "mobile",
        }])
        proba = inference_pipeline.predict_proba(df)
        assert proba.shape == (1,)
        assert 0.0 <= proba[0] <= 1.0


class TestMLDataIntegrity:
    """Test data integrity of train/val/test splits."""

    def test_train_val_test_files_exist(self):
        for split in ("train.parquet", "val.parquet", "test.parquet"):
            path = DATA_DIR / split
            assert path.exists(), f"Missing {split}"
            assert path.stat().st_size > 0

    def test_split_ratios(self):
        train = pd.read_parquet(DATA_DIR / "train.parquet")
        val = pd.read_parquet(DATA_DIR / "val.parquet")
        test = pd.read_parquet(DATA_DIR / "test.parquet")

        total = len(train) + len(val) + len(test)
        train_ratio = len(train) / total
        val_ratio = len(val) / total
        test_ratio = len(test) / total

        # 70/15/15 split with tolerance
        assert 0.68 <= train_ratio <= 0.72
        assert 0.13 <= val_ratio <= 0.17
        assert 0.13 <= test_ratio <= 0.17

    def test_stratified_splits_fraud_rate(self):
        train = pd.read_parquet(DATA_DIR / "train.parquet")
        val = pd.read_parquet(DATA_DIR / "val.parquet")
        test = pd.read_parquet(DATA_DIR / "test.parquet")

        train_rate = train["is_fraud"].mean()
        val_rate = val["is_fraud"].mean()
        test_rate = test["is_fraud"].mean()

        # Rates should be within 0.5% of each other
        assert abs(train_rate - val_rate) < 0.005
        assert abs(train_rate - test_rate) < 0.005

    def test_no_overlapping_ids(self):
        """Verify train/val/test have no overlapping transaction_ids."""
        train = pd.read_parquet(DATA_DIR / "train.parquet")
        val = pd.read_parquet(DATA_DIR / "val.parquet")
        test = pd.read_parquet(DATA_DIR / "test.parquet")

        # Check if transaction_id column exists in processed data
        if "transaction_id" in train.columns:
            train_ids = set(train["transaction_id"])
            val_ids = set(val["transaction_id"])
            test_ids = set(test["transaction_id"])

            assert train_ids.isdisjoint(val_ids)
            assert train_ids.isdisjoint(test_ids)
            assert val_ids.isdisjoint(test_ids)


class TestMLMetrics:
    """Test metrics on the held-out test set."""

    def test_roc_auc_on_test_set(self, test_predictions):
        from sklearn.metrics import roc_auc_score
        y_true, y_pred, y_proba = test_predictions
        auc = roc_auc_score(y_true, y_proba)
        assert 0.0 <= auc <= 1.0
        # Record the actual AUC for documentation
        print(f"\nTest ROC-AUC: {auc:.6f}")

    def test_pr_auc_on_test_set(self, test_predictions):
        from sklearn.metrics import average_precision_score
        y_true, y_pred, y_proba = test_predictions
        pr_auc = average_precision_score(y_true, y_proba)
        assert 0.0 <= pr_auc <= 1.0
        print(f"\nTest PR-AUC: {pr_auc:.6f}")

    def test_precision_recall_on_test_set(self, test_predictions):
        from sklearn.metrics import precision_score, recall_score, f1_score
        y_true, y_pred, y_proba = test_predictions
        precision = precision_score(y_true, y_pred, zero_division=0)
        recall = recall_score(y_true, y_pred, zero_division=0)
        f1 = f1_score(y_true, y_pred, zero_division=0)
        assert 0.0 <= precision <= 1.0
        assert 0.0 <= recall <= 1.0
        assert 0.0 <= f1 <= 1.0
        print(f"\nTest Precision: {precision:.6f}, Recall: {recall:.6f}, F1: {f1:.6f}")