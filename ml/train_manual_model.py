"""
Phase 31 Manual-Input XGBoost Model Training

Trains a separate XGBoost model for Mode B (manual transaction testing)
using only user-providable features from IEEE-CIS dataset.

Usage:
    python ml/train_manual_model.py
"""
import json
import os
import pickle
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    confusion_matrix,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from xgboost import XGBClassifier

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from api.database import get_engine

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODELS_DIR = PROJECT_ROOT / "ml" / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)

# User-providable features (subset of IEEE-CIS raw columns)
NUMERIC_FEATURES = [
    "transaction_amt",
    "transaction_hour",
    "transaction_dayofweek",
    "is_weekend",
    "card1",
    "addr1",
    "addr2",
    "dist1",
    "dist2",
    "c1", "c2", "c3", "c4", "c5", "c6", "c7", "c8", "c9", "c10",
    "c11", "c12", "c13", "c14",
    "d1", "d2", "d3", "d4", "d5",
]

CATEGORICAL_FEATURES = [
    "product_cd",
    "card4",
    "card6",
    "p_emaildomain",
    "r_emaildomain",
    "device_type",
    "m1", "m2", "m3", "m4", "m5", "m6",
]

ALL_FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES

RANDOM_STATE = 42
TEST_SIZE = 0.15
VAL_SIZE = 0.15


def load_raw_data():
    """Load raw transaction data from PostgreSQL."""
    engine = get_engine()
    cols = ["transaction_id", "is_fraud", "transaction_dt", "transaction_amt",
            "product_cd", "card1", "card2", "card3", "card4", "card5", "card6",
            "addr1", "addr2", "dist1", "dist2", "p_emaildomain", "r_emaildomain",
            "device_type", "device_info",
            "c1", "c2", "c3", "c4", "c5", "c6", "c7", "c8", "c9", "c10",
            "c11", "c12", "c13", "c14",
            "d1", "d2", "d3", "d4", "d5",
            "m1", "m2", "m3", "m4", "m5", "m6", "m7", "m8", "m9"]
    col_str = ", ".join(cols)
    query = f"SELECT {col_str} FROM marts.fact_transactions"
    print("Loading data from PostgreSQL...")
    df = pd.read_sql(query, engine)
    print(f"Loaded {len(df)} rows, {len(df.columns)} columns")
    return df


def engineer_features(df):
    """Engineer time features from transaction_dt."""
    df = df.copy()
    df["transaction_hour"] = (df["transaction_dt"] % 86400 // 3600).astype("float64")
    df["transaction_dayofweek"] = ((df["transaction_dt"] // 86400) % 7).astype("float64")
    df["is_weekend"] = (df["transaction_dayofweek"].isin([5, 6])).astype("float64")
    return df


def build_preprocessor():
    """Build a ColumnTransformer for numeric + categorical features."""
    numeric_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
    ])
    categorical_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="constant", fill_value="missing")),
        ("encoder", OneHotEncoder(
            handle_unknown="ignore",
            sparse_output=False,
            dtype=np.float32,
            max_categories=30,
        )),
    ])
    return ColumnTransformer(
        transformers=[
            ("num", numeric_pipeline, NUMERIC_FEATURES),
            ("cat", categorical_pipeline, CATEGORICAL_FEATURES),
        ],
        remainder="drop",
        sparse_threshold=0,
    )


def evaluate_model(model, X, y, label=""):
    """Compute and print evaluation metrics."""
    proba = model.predict_proba(X)[:, 1]
    pred = (proba >= 0.5).astype(int)
    auc = roc_auc_score(y, proba)
    pr_auc = None
    try:
        precision, recall, _ = precision_recall_curve(y, proba)
        pr_auc = (precision * (recall[1:] - recall[:-1])).sum() if len(precision) > 1 else 0
    except Exception:
        pass
    prec = precision_score(y, pred, zero_division=0)
    rec = recall_score(y, pred, zero_division=0)
    f1 = f1_score(y, pred, zero_division=0)
    cm = confusion_matrix(y, pred)
    print(f"\n{label} Metrics:")
    print(f"  ROC-AUC:   {auc:.4f}")
    print(f"  PR-AUC:    {pr_auc:.4f}" if pr_auc is not None else "  PR-AUC:    N/A")
    print(f"  Precision: {prec:.4f}")
    print(f"  Recall:    {rec:.4f}")
    print(f"  F1:        {f1:.4f}")
    print(f"  Confusion Matrix: TN={cm[0,0]}, FP={cm[0,1]}, FN={cm[1,0]}, TP={cm[1,1]}")
    print(f"  Fraud rate: {y.mean()*100:.2f}%")
    return {"roc_auc": auc, "pr_auc": pr_auc, "precision": prec, "recall": rec, "f1": f1,
            "confusion_matrix": cm.tolist()}


def find_best_threshold(y_val, proba_val):
    """Find threshold that maximizes F1 on validation set."""
    precisions, recalls, thresholds = precision_recall_curve(y_val, proba_val)
    f1s = 2 * (precisions * recalls) / (precisions + recalls + 1e-10)
    best_idx = f1s.argmax()
    best_threshold = thresholds[best_idx] if best_idx < len(thresholds) else 0.5
    print(f"\nBest threshold (max F1 on val): {best_threshold:.4f} (F1={f1s[best_idx]:.4f})")
    return float(best_threshold)


def main():
    # Load data
    df = load_raw_data()

    # Engineer features
    df = engineer_features(df)

    # Split
    X = df[ALL_FEATURES].copy()
    y = df["is_fraud"].astype(int)

    X_train, X_temp, y_train, y_temp = train_test_split(
        X, y, test_size=TEST_SIZE + VAL_SIZE, random_state=RANDOM_STATE, stratify=y
    )
    val_ratio = VAL_SIZE / (TEST_SIZE + VAL_SIZE)
    X_val, X_test, y_val, y_test = train_test_split(
        X_temp, y_temp, test_size=1 - val_ratio, random_state=RANDOM_STATE, stratify=y_temp
    )

    print(f"Train: {len(X_train)}, Val: {len(X_val)}, Test: {len(X_test)}")

    # Build and fit preprocessor
    print("\nBuilding preprocessor...")
    preprocessor = build_preprocessor()
    X_train_proc = preprocessor.fit_transform(X_train)
    X_val_proc = preprocessor.transform(X_val)
    X_test_proc = preprocessor.transform(X_test)

    feature_names = [f"f_{i}" for i in range(X_train_proc.shape[1])]
    # Use actual feature names from ColumnTransformer
    try:
        feature_names = preprocessor.get_feature_names_out().tolist()
    except Exception:
        pass

    print(f"Processed features: {X_train_proc.shape[1]}")

    # Train XGBoost
    print("\nTraining XGBoost...")
    scale_pos_weight = (y_train == 0).sum() / (y_train == 1).sum()
    model = XGBClassifier(
        n_estimators=300,
        max_depth=6,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        scale_pos_weight=scale_pos_weight,
        eval_metric="auc",
        use_label_encoder=False,
        random_state=RANDOM_STATE,
        n_jobs=-1,
    )
    model.fit(
        X_train_proc, y_train,
        eval_set=[(X_val_proc, y_val)],
        verbose=50,
    )

    # Evaluate
    val_metrics = evaluate_model(model, X_val_proc, y_val, "Validation")
    test_metrics = evaluate_model(model, X_test_proc, y_test, "Test")

    # Find best threshold on validation
    val_proba = model.predict_proba(X_val_proc)[:, 1]
    best_threshold = find_best_threshold(y_val.values, val_proba)

    # Evaluate at best threshold on test
    test_proba = model.predict_proba(X_test_proc)[:, 1]
    test_pred = (test_proba >= best_threshold).astype(int)
    print(f"\nTest metrics at threshold={best_threshold:.4f}:")
    print(f"  Precision: {precision_score(y_test, test_pred, zero_division=0):.4f}")
    print(f"  Recall:    {recall_score(y_test, test_pred, zero_division=0):.4f}")
    print(f"  F1:        {f1_score(y_test, test_pred, zero_division=0):.4f}")
    cm = confusion_matrix(y_test, test_pred)
    print(f"  Confusion Matrix: TN={cm[0,0]}, FP={cm[0,1]}, FN={cm[1,0]}, TP={cm[1,1]}")

    # Save artifacts
    print("\nSaving artifacts...")
    joblib.dump(model, MODELS_DIR / "xgboost_manual.pkl")
    joblib.dump(preprocessor, MODELS_DIR / "preprocessor_manual.pkl")

    with open(MODELS_DIR / "feature_columns_manual.json", "w") as f:
        json.dump(ALL_FEATURES, f, indent=2)

    with open(MODELS_DIR / "feature_names_processed_manual.json", "w") as f:
        json.dump(feature_names, f, indent=2)

    metadata = {
        "model_version": "xgboost-manual-v1",
        "model_type": "XGBoost",
        "training_mode": "manual-input",
        "threshold": best_threshold,
        "default_threshold": 0.5,
        "features": ALL_FEATURES,
        "num_features": len(NUMERIC_FEATURES),
        "cat_features": len(CATEGORICAL_FEATURES),
        "total_features_raw": len(ALL_FEATURES),
        "total_features_processed": len(feature_names),
        "train_size": len(X_train),
        "val_size": len(X_val),
        "test_size": len(X_test),
        "fraud_rate_train": float(y_train.mean()),
        "fraud_rate_val": float(y_val.mean()),
        "fraud_rate_test": float(y_test.mean()),
        "val_metrics": val_metrics,
        "test_metrics": test_metrics,
        "scale_pos_weight": float(scale_pos_weight),
        "random_state": RANDOM_STATE,
    }
    with open(MODELS_DIR / "model_metadata_manual.json", "w") as f:
        json.dump(metadata, f, indent=2, default=str)

    # Save threshold separately for easy loading
    with open(MODELS_DIR / "threshold_manual.json", "w") as f:
        json.dump({"threshold": best_threshold}, f)

    # Verify: load and predict
    print("\nVerifying artifacts (load + predict)...")
    loaded_model = joblib.load(MODELS_DIR / "xgboost_manual.pkl")
    loaded_prep = joblib.load(MODELS_DIR / "preprocessor_manual.pkl")
    test_pred_proba = loaded_model.predict_proba(loaded_prep.transform(X_test.head(5)))[:, 1]
    print(f"  Sample predictions: {test_pred_proba.tolist()}")
    print("  Verification PASSED")

    print("\n=== TRAINING COMPLETE ===")
    print(f"  Model: {MODELS_DIR / 'xgboost_manual.pkl'}")
    print(f"  Preprocessor: {MODELS_DIR / 'preprocessor_manual.pkl'}")
    print(f"  Features: {MODELS_DIR / 'feature_columns_manual.json'}")
    print(f"  Threshold: {best_threshold:.4f}")
    print(f"  Test ROC-AUC: {test_metrics['roc_auc']:.4f}")
    print(f"  Test PR-AUC: {test_metrics['pr_auc']:.4f}" if test_metrics['pr_auc'] is not None else "  Test PR-AUC: N/A")
    print(f"  Test F1: {test_metrics['f1']:.4f}")


if __name__ == "__main__":
    main()
