"""
Phase 30 - EXT-01: LightGBM Model Training
"""
import json
import time
import warnings
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from lightgbm import LGBMClassifier
from sklearn.metrics import (
    average_precision_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)

warnings.filterwarnings("ignore")

RANDOM_STATE = 42
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "ml" / "data"
MODEL_DIR = PROJECT_ROOT / "ml" / "models"

TRAIN_FILE = DATA_DIR / "train.parquet"
VAL_FILE = DATA_DIR / "val.parquet"
MODEL_DIR.mkdir(parents=True, exist_ok=True)


def load_data():
    print("Loading training data...")
    train_df = pd.read_parquet(TRAIN_FILE)
    print("Loading validation data...")
    val_df = pd.read_parquet(VAL_FILE)
    print(f"Train shape: {train_df.shape}")
    print(f"Validation shape: {val_df.shape}")
    return train_df, val_df


def validate_data(train_df, val_df):
    if "is_fraud" not in train_df.columns:
        raise ValueError("Train dataset does not contain 'is_fraud'.")
    if "is_fraud" not in val_df.columns:
        raise ValueError("Validation dataset does not contain 'is_fraud'.")
    if train_df["is_fraud"].isna().any():
        raise ValueError("Train target contains NULL values.")
    if val_df["is_fraud"].isna().any():
        raise ValueError("Validation target contains NULL values.")
    print("\n=== DATA VALIDATION ===")
    print(f"Train rows: {len(train_df):,}")
    print(f"Validation rows: {len(val_df):,}")
    print(f"Train fraud rate: {train_df['is_fraud'].mean():.6f}")
    print(f"Validation fraud rate: {val_df['is_fraud'].mean():.6f}")


def get_feature_columns(train_df):
    excluded = {"is_fraud", "transaction_id"}
    feature_columns = [
        col for col in train_df.columns
        if col not in excluded and pd.api.types.is_numeric_dtype(train_df[col])
    ]
    if not feature_columns:
        raise ValueError("No numeric feature columns found.")
    return feature_columns


def prepare_xy(train_df, val_df, feature_columns):
    X_train = train_df[feature_columns].copy()
    y_train = train_df["is_fraud"].astype(int)
    X_val = val_df[feature_columns].copy()
    y_val = val_df["is_fraud"].astype(int)
    if list(X_train.columns) != list(X_val.columns):
        raise ValueError("Train and validation feature columns are not aligned.")
    train_nulls = int(X_train.isna().sum().sum())
    val_nulls = int(X_val.isna().sum().sum())
    print(f"\nTrain feature NULL count: {train_nulls:,}")
    print(f"Validation feature NULL count: {val_nulls:,}")
    if train_nulls > 0 or val_nulls > 0:
        raise ValueError("Feature matrix contains NULL values.")
    # Clean feature names for LightGBM compatibility
    X_train.columns = [str(c).replace('[', '_').replace(']', '_').replace('<', '_').replace('>', '_').replace(',', '_').replace(':', '_').replace('"', '_').replace('\'', '_').replace(' ', '_') for c in X_train.columns]
    X_val.columns = X_train.columns
    return X_train, y_train, X_val, y_val


def evaluate_model(model, X_val, y_val, name):
    start_pred = time.time()
    if hasattr(model, "predict_proba"):
        y_proba = model.predict_proba(X_val)[:, 1]
    else:
        decision = model.decision_function(X_val)
        y_proba = 1 / (1 + np.exp(-decision))
    pred_time = time.time() - start_pred
    y_pred = (y_proba >= 0.5).astype(int)

    roc_auc = roc_auc_score(y_val, y_proba)
    pr_auc = average_precision_score(y_val, y_proba)
    precision = precision_score(y_val, y_pred, zero_division=0)
    recall = recall_score(y_val, y_pred, zero_division=0)
    f1 = f1_score(y_val, y_pred, zero_division=0)
    cm = confusion_matrix(y_val, y_pred)

    print("\n" + "-" * 70)
    print(f"VALIDATION: {name}")
    print("-" * 70)
    print(f"ROC-AUC   : {roc_auc:.6f}")
    print(f"PR-AUC    : {pr_auc:.6f}")
    print(f"Precision : {precision:.6f}")
    print(f"Recall    : {recall:.6f}")
    print(f"F1        : {f1:.6f}")
    print(f"Pred time : {pred_time:.4f}s")
    print("\nConfusion Matrix:")
    print(cm)

    return {
        "model": name,
        "roc_auc": float(roc_auc),
        "pr_auc": float(pr_auc),
        "precision": float(precision),
        "recall": float(recall),
        "f1": float(f1),
        "threshold": 0.5,
        "confusion_matrix": cm.tolist(),
        "prediction_time_seconds": pred_time,
    }


def main():
    print("=" * 70)
    print("PHASE 30 - EXT-01: LIGHTGBM TRAINING")
    print("=" * 70)

    train_df, val_df = load_data()
    validate_data(train_df, val_df)
    feature_columns = get_feature_columns(train_df)
    print(f"\nNumber of features: {len(feature_columns)}")

    X_train, y_train, X_val, y_val = prepare_xy(train_df, val_df, feature_columns)
    print(f"\nX_train: {X_train.shape}")
    print(f"X_val:   {X_val.shape}")

    print("\n" + "=" * 70)
    print("TRAINING LIGHTGBM")
    print("=" * 70)

    neg = (y_train == 0).sum()
    pos = (y_train == 1).sum()
    scale_pos_weight = neg / pos if pos > 0 else 1.0
    print(f"Class imbalance - neg: {neg}, pos: {pos}, scale_pos_weight: {scale_pos_weight:.2f}")

    start_train = time.time()
    model = LGBMClassifier(
        n_estimators=500,
        max_depth=7,
        learning_rate=0.05,
        num_leaves=127,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=RANDOM_STATE,
        n_jobs=-1,
        scale_pos_weight=scale_pos_weight,
        objective='binary',
        verbosity=-1,
    )
    model.fit(X_train, y_train)
    train_time = time.time() - start_train
    print(f"Training completed in {train_time:.2f}s")

    joblib.dump(model, MODEL_DIR / "lightgbm.pkl")
    print(f"Saved model to {MODEL_DIR / 'lightgbm.pkl'}")

    result = evaluate_model(model, X_val, y_val, "LightGBM")
    result["training_time_seconds"] = train_time

    metadata = {
        "model_name": "lightgbm",
        "model_version": "lightgbm-v1-phase30",
        "random_state": RANDOM_STATE,
        "n_features": len(feature_columns),
        "train_rows": len(train_df),
        "validation_rows": len(val_df),
        "train_fraud_rate": float(train_df["is_fraud"].mean()),
        "val_fraud_rate": float(val_df["is_fraud"].mean()),
        "scale_pos_weight": float(scale_pos_weight),
        "hyperparameters": {
            "n_estimators": 500,
            "max_depth": 7,
            "learning_rate": 0.05,
            "num_leaves": 127,
            "subsample": 0.8,
            "colsample_bytree": 0.8,
        },
        "metrics": result,
        "training_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }

    with open(MODEL_DIR / "lightgbm_metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 70)
    print("LIGHTGBM TRAINING COMPLETED")
    print("=" * 70)
    print(f"ROC-AUC: {result['roc_auc']:.6f}, PR-AUC: {result['pr_auc']:.6f}, F1: {result['f1']:.6f}")


if __name__ == "__main__":
    main()
