"""
Phase 16 - Machine Learning

Train and compare:
1. Logistic Regression
2. Random Forest
3. XGBoost

Training protocol:
- Train: model fitting + hyperparameter tuning
- Validation: model comparison
- Test: NOT USED in Phase 16
"""

from pathlib import Path
import json
import warnings

import joblib
import numpy as np
import pandas as pd

from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    classification_report,
    confusion_matrix,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
)
from sklearn.model_selection import RandomizedSearchCV
from sklearn.preprocessing import StandardScaler

from xgboost import XGBClassifier


warnings.filterwarnings("ignore")

RANDOM_STATE = 42

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_DIR = PROJECT_ROOT / "ml" / "data"
MODEL_DIR = PROJECT_ROOT / "ml" / "models"

TRAIN_FILE = DATA_DIR / "train.parquet"
VAL_FILE = DATA_DIR / "val.parquet"
FEATURE_METADATA_FILE = DATA_DIR / "feature_metadata.json"

MODEL_DIR.mkdir(parents=True, exist_ok=True)


def load_data():
    """Load training and validation data only."""

    print("Loading training data...")
    train_df = pd.read_parquet(TRAIN_FILE)

    print("Loading validation data...")
    val_df = pd.read_parquet(VAL_FILE)

    print(f"Train shape: {train_df.shape}")
    print(f"Validation shape: {val_df.shape}")

    return train_df, val_df


def validate_data(train_df, val_df):
    """Validate dataset structure before training."""

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
    """
    Determine feature columns.

    Excludes target and transaction identifier.
    Keeps numeric features only.
    """

    excluded = {
        "is_fraud",
        "transaction_id",
    }

    feature_columns = [
        col
        for col in train_df.columns
        if col not in excluded
        and pd.api.types.is_numeric_dtype(train_df[col])
    ]

    if not feature_columns:
        raise ValueError("No numeric feature columns found.")

    return feature_columns


def prepare_xy(train_df, val_df, feature_columns):

    X_train = train_df[feature_columns].copy()
    y_train = train_df["is_fraud"].astype(int)

    X_val = val_df[feature_columns].copy()
    y_val = val_df["is_fraud"].astype(int)

    # Check column alignment
    if list(X_train.columns) != list(X_val.columns):
        raise ValueError("Train and validation feature columns are not aligned.")

    # Check missing values
    train_nulls = int(X_train.isna().sum().sum())
    val_nulls = int(X_val.isna().sum().sum())

    print(f"\nTrain feature NULL count: {train_nulls:,}")
    print(f"Validation feature NULL count: {val_nulls:,}")

    if train_nulls > 0 or val_nulls > 0:
        raise ValueError(
            "Feature matrix contains NULL values. "
            "Resolve preprocessing in Phase 15 before training."
        )

    return X_train, y_train, X_val, y_val


def train_logistic_regression(X_train, y_train):

    print("\n" + "=" * 70)
    print("TRAINING LOGISTIC REGRESSION")
    print("=" * 70)

    scaler = StandardScaler()

    X_train_scaled = scaler.fit_transform(X_train)

    # Use small subset for fast tuning
    tune_size = min(50000, len(X_train_scaled))
    tune_idx = np.random.RandomState(RANDOM_STATE).choice(
        len(X_train_scaled), tune_size, replace=False
    )
    X_tune = X_train_scaled[tune_idx]
    y_tune = y_train.iloc[tune_idx]

    param_dist = {
        "C": [0.01, 0.1, 1, 10],
        "penalty": ["l2"],
        "solver": ["lbfgs"],
        "class_weight": ["balanced", None],
    }

    model = LogisticRegression(
        max_iter=1000,
        random_state=RANDOM_STATE,
    )

    search = RandomizedSearchCV(
        estimator=model,
        param_distributions=param_dist,
        n_iter=4,
        scoring="roc_auc",
        cv=2,
        random_state=RANDOM_STATE,
        n_jobs=1,
        verbose=1,
    )

    search.fit(X_tune, y_tune)

    print("Best parameters:")
    print(search.best_params_)

    print(f"Best CV ROC-AUC: {search.best_score_:.6f}")

    # Refit best model on full training data
    best_model = search.best_estimator_
    best_model.fit(X_train_scaled, y_train)

    joblib.dump(
        best_model,
        MODEL_DIR / "logistic_regression.pkl",
    )

    joblib.dump(
        scaler,
        MODEL_DIR / "logistic_scaler.pkl",
    )

    return best_model, scaler


def train_random_forest(X_train, y_train):

    print("\n" + "=" * 70)
    print("TRAINING RANDOM FOREST")
    print("=" * 70)

    # Use subset for hyperparameter tuning
    tune_size = min(50000, len(X_train))
    tune_idx = np.random.RandomState(RANDOM_STATE).choice(
        len(X_train), tune_size, replace=False
    )
    X_tune = X_train.iloc[tune_idx]
    y_tune = y_train.iloc[tune_idx]

    param_dist = {
        "n_estimators": [100, 200],
        "max_depth": [10, 20, None],
        "min_samples_split": [2, 5],
        "min_samples_leaf": [1, 2],
        "class_weight": ["balanced", None],
        "max_features": ["sqrt"],
    }

    model = RandomForestClassifier(
        random_state=RANDOM_STATE,
        n_jobs=2,
    )

    search = RandomizedSearchCV(
        estimator=model,
        param_distributions=param_dist,
        n_iter=6,
        scoring="roc_auc",
        cv=2,
        random_state=RANDOM_STATE,
        n_jobs=1,
        verbose=1,
    )

    search.fit(X_tune, y_tune)

    print("Best parameters:")
    print(search.best_params_)

    print(f"Best CV ROC-AUC: {search.best_score_:.6f}")

    # Refit best model on full training data
    best_model = search.best_estimator_
    best_model.fit(X_train, y_train)

    joblib.dump(
        best_model,
        MODEL_DIR / "random_forest.pkl",
    )

    return best_model


def train_xgboost(X_train, y_train):

    print("\n" + "=" * 70)
    print("TRAINING XGBOOST")
    print("=" * 70)

    # Use subset for hyperparameter tuning
    tune_size = min(50000, len(X_train))
    tune_idx = np.random.RandomState(RANDOM_STATE).choice(
        len(X_train), tune_size, replace=False
    )
    X_tune = X_train.iloc[tune_idx]
    y_tune = y_train.iloc[tune_idx]

    param_dist = {
        "n_estimators": [100, 200],
        "max_depth": [3, 5, 7],
        "learning_rate": [0.05, 0.1, 0.2],
        "subsample": [0.8, 1.0],
        "colsample_bytree": [0.8, 1.0],
        "min_child_weight": [1, 3],
        "reg_alpha": [0, 0.1],
        "reg_lambda": [0.5, 1.0],
        "scale_pos_weight": [15, 17, 20],
    }

    model = XGBClassifier(
        random_state=RANDOM_STATE,
        eval_metric="logloss",
        tree_method="hist",
        n_jobs=2,
    )

    search = RandomizedSearchCV(
        estimator=model,
        param_distributions=param_dist,
        n_iter=8,
        scoring="roc_auc",
        cv=2,
        random_state=RANDOM_STATE,
        n_jobs=1,
        verbose=1,
    )

    search.fit(X_tune, y_tune)

    print("Best parameters:")
    print(search.best_params_)

    print(f"Best CV ROC-AUC: {search.best_score_:.6f}")

    # Refit best model on full training data
    best_model = search.best_estimator_
    best_model.fit(X_train, y_train)

    joblib.dump(
        best_model,
        MODEL_DIR / "xgboost.pkl",
    )

    return best_model


def evaluate_model(model, X_val, y_val, name):

    y_proba = model.predict_proba(X_val)[:, 1]

    # 0.5 is kept as the initial comparison threshold.
    y_pred = (y_proba >= 0.5).astype(int)

    roc_auc = roc_auc_score(y_val, y_proba)
    pr_auc = average_precision_score(y_val, y_proba)

    precision = precision_score(
        y_val,
        y_pred,
        zero_division=0,
    )

    recall = recall_score(
        y_val,
        y_pred,
        zero_division=0,
    )

    f1 = f1_score(
        y_val,
        y_pred,
        zero_division=0,
    )

    cm = confusion_matrix(y_val, y_pred)

    print("\n" + "-" * 70)
    print(f"VALIDATION: {name}")
    print("-" * 70)

    print(f"ROC-AUC : {roc_auc:.6f}")
    print(f"PR-AUC  : {pr_auc:.6f}")
    print(f"Precision: {precision:.6f}")
    print(f"Recall   : {recall:.6f}")
    print(f"F1       : {f1:.6f}")

    print("\nConfusion Matrix:")
    print(cm)

    print("\nClassification Report:")
    print(
        classification_report(
            y_val,
            y_pred,
            target_names=["Non-Fraud", "Fraud"],
            zero_division=0,
        )
    )

    return {
        "model": name,
        "roc_auc": float(roc_auc),
        "pr_auc": float(pr_auc),
        "precision": float(precision),
        "recall": float(recall),
        "f1": float(f1),
        "threshold": 0.5,
        "confusion_matrix": cm.tolist(),
    }


def main():

    print("=" * 70)
    print("PHASE 16 - MACHINE LEARNING")
    print("=" * 70)

    train_df, val_df = load_data()

    validate_data(train_df, val_df)

    feature_columns = get_feature_columns(train_df)

    print(f"\nNumber of features: {len(feature_columns)}")

    X_train, y_train, X_val, y_val = prepare_xy(
        train_df,
        val_df,
        feature_columns,
    )

    print(f"\nX_train: {X_train.shape}")
    print(f"X_val:   {X_val.shape}")

    # --------------------------------------------------
    # 1. Logistic Regression
    # --------------------------------------------------

    lr_model, lr_scaler = train_logistic_regression(
        X_train,
        y_train,
    )

    X_val_scaled = lr_scaler.transform(X_val)

    # --------------------------------------------------
    # 2. Random Forest
    # --------------------------------------------------

    rf_model = train_random_forest(
        X_train,
        y_train,
    )

    # --------------------------------------------------
    # 3. XGBoost
    # --------------------------------------------------

    xgb_model = train_xgboost(
        X_train,
        y_train,
    )

    # --------------------------------------------------
    # Validation
    # --------------------------------------------------

    print("\n\n")
    print("=" * 70)
    print("VALIDATION MODEL COMPARISON")
    print("=" * 70)

    results = []

    results.append(
        evaluate_model(
            lr_model,
            X_val_scaled,
            y_val,
            "Logistic Regression",
        )
    )

    results.append(
        evaluate_model(
            rf_model,
            X_val,
            y_val,
            "Random Forest",
        )
    )

    results.append(
        evaluate_model(
            xgb_model,
            X_val,
            y_val,
            "XGBoost",
        )
    )

    # --------------------------------------------------
    # Select best model by ROC-AUC
    # --------------------------------------------------

    best_result = max(
        results,
        key=lambda x: x["roc_auc"],
    )

    print("\n" + "=" * 70)
    print("FINAL MODEL COMPARISON")
    print("=" * 70)

    for result in results:
        print(
            f"{result['model']:25s} "
            f"ROC-AUC={result['roc_auc']:.6f} "
            f"PR-AUC={result['pr_auc']:.6f} "
            f"F1={result['f1']:.6f}"
        )

    print("\nBest model:")
    print(best_result["model"])

    # --------------------------------------------------
    # Save feature metadata
    # --------------------------------------------------

    with open(
        MODEL_DIR / "feature_columns.json",
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(
            feature_columns,
            f,
            ensure_ascii=False,
            indent=2,
        )

    with open(
        MODEL_DIR / "training_results.json",
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(
            {
                "random_state": RANDOM_STATE,
                "n_features": len(feature_columns),
                "train_rows": len(train_df),
                "validation_rows": len(val_df),
                "models": results,
                "best_model": best_result["model"],
            },
            f,
            ensure_ascii=False,
            indent=2,
        )

    print("\nArtifacts saved to:")
    print(MODEL_DIR)

    print("\nPhase 16 training completed.")


if __name__ == "__main__":
    main()