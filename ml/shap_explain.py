"""
Phase 18: SHAP / XAI

Explain the selected XGBoost fraud detection model using SHAP.
"""

from pathlib import Path
import json
import warnings

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import shap

warnings.filterwarnings("ignore")

SAMPLE_SIZE = 5000
RANDOM_STATE = 42

BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "data" / "test.parquet"
MODEL_PATH = BASE_DIR / "models" / "xgboost.pkl"
FEATURE_COLS_PATH = BASE_DIR / "models" / "feature_columns.json"
OUTPUT_DIR = BASE_DIR / "models"


def load_data_and_model():
    """Load test data, feature list and trained XGBoost model."""

    print("Loading test data...")

    test_df = pd.read_parquet(DATA_PATH)

    print(f"Test rows: {len(test_df):,}")

    # Load feature columns from JSON
    with open(
        FEATURE_COLS_PATH,
        "r",
        encoding="utf-8",
    ) as f:
        feature_cols = json.load(f)

    missing_features = [
        col for col in feature_cols
        if col not in test_df.columns
    ]

    if missing_features:
        raise ValueError(
            f"Missing features in test data: {missing_features[:10]}"
        )

    X_test = test_df[feature_cols].copy()

    # Convert boolean columns to integers.
    bool_cols = X_test.select_dtypes(include=["bool"]).columns

    for col in bool_cols:
        X_test[col] = X_test[col].astype("int8")

    # Keep only numeric features used by the model.
    X_test = X_test.select_dtypes(
        include=["number"]
    )

    # Replace inf values if present.
    X_test = X_test.replace(
        [np.inf, -np.inf],
        np.nan
    )

    # XGBoost model input should not contain NaN unless
    # the trained model explicitly supports the same representation.
    # Preserve NaN here because XGBoost supports missing values.
    
    sample_size = min(
        SAMPLE_SIZE,
        len(X_test)
    )

    X_sample = X_test.sample(
        n=sample_size,
        random_state=RANDOM_STATE
    )

    print(f"SHAP sample size: {len(X_sample):,}")
    print(f"Features: {X_sample.shape[1]:,}")

    print("Loading XGBoost model...")

    model = joblib.load(MODEL_PATH)

    return X_sample, model


def create_shap_explainer(model):
    """Create TreeExplainer for XGBoost."""

    print("Creating SHAP TreeExplainer...")

    return shap.TreeExplainer(model)


def compute_shap_values(explainer, X):
    """Compute SHAP values."""

    print("Computing SHAP values...")

    shap_values = explainer.shap_values(X)

    # Normalize possible SHAP output formats.
    if isinstance(shap_values, list):
        # Binary classification:
        # use positive/fraud class.
        if len(shap_values) == 2:
            shap_values = shap_values[1]
        else:
            shap_values = shap_values[0]

    shap_values = np.asarray(shap_values)

    # Some SHAP versions may return:
    # (n_samples, n_features, n_classes)
    if shap_values.ndim == 3:
        shap_values = shap_values[:, :, 1]

    if shap_values.shape != X.shape:
        raise ValueError(
            f"SHAP shape {shap_values.shape} "
            f"does not match X shape {X.shape}"
        )

    print(
        f"SHAP matrix: "
        f"{shap_values.shape[0]:,} samples × "
        f"{shap_values.shape[1]:,} features"
    )

    return shap_values


def plot_summary(shap_values, X):
    """Generate SHAP beeswarm summary plot."""

    print("Generating SHAP summary plot...")

    plt.figure(figsize=(12, 10))

    shap.summary_plot(
        shap_values,
        X,
        plot_type="dot",
        show=False,
        max_display=20
    )

    plt.title("SHAP Summary — Top 20 Features")
    plt.tight_layout()

    output_path = OUTPUT_DIR / "shap_summary.png"

    plt.savefig(
        output_path,
        dpi=150,
        bbox_inches="tight"
    )

    plt.close()

    print(f"Saved: {output_path}")


def plot_bar(shap_values, X):
    """Generate mean absolute SHAP importance bar chart."""

    print("Generating SHAP bar plot...")

    plt.figure(figsize=(12, 10))

    shap.summary_plot(
        shap_values,
        X,
        plot_type="bar",
        show=False,
        max_display=20
    )

    plt.title("SHAP Feature Importance — Top 20")
    plt.tight_layout()

    output_path = OUTPUT_DIR / "shap_bar.png"

    plt.savefig(
        output_path,
        dpi=150,
        bbox_inches="tight"
    )

    plt.close()

    print(f"Saved: {output_path}")


def plot_individual(explainer, shap_values, X):
    """Generate individual SHAP explanations."""

    print("Generating individual explanations...")

    indices = [0, 100, 500]

    for idx in indices:

        if idx >= len(X):
            continue

        sample = X.iloc[idx]

        base_value = explainer.expected_value

        if isinstance(base_value, np.ndarray):
            if base_value.ndim > 0:
                base_value = base_value[-1]

        sample_shap = shap_values[idx]

        plt.figure(figsize=(16, 6))

        shap.force_plot(
            base_value,
            sample_shap,
            sample,
            matplotlib=True,
            show=False
        )

        plt.title(
            f"SHAP Force Plot — Sample #{idx}"
        )

        plt.tight_layout()

        output_path = (
            OUTPUT_DIR /
            f"shap_individual_{idx}.png"
        )

        plt.savefig(
            output_path,
            dpi=150,
            bbox_inches="tight"
        )

        plt.close()

        print(f"Saved: {output_path}")


def get_top_features(shap_values, X, top_n=20):
    """Calculate mean absolute SHAP feature importance."""

    print("Calculating feature importance...")

    mean_abs_shap = np.abs(
        shap_values
    ).mean(axis=0)

    importance_df = pd.DataFrame({
        "feature": X.columns,
        "mean_abs_shap": mean_abs_shap
    })

    importance_df = importance_df.sort_values(
        "mean_abs_shap",
        ascending=False
    ).reset_index(drop=True)

    top_features = importance_df.head(top_n)

    output_path = OUTPUT_DIR / "top_features.csv"

    top_features.to_csv(
        output_path,
        index=False
    )

    print(f"\nTop {top_n} features:")
    print(top_features.to_string(index=False))

    print(f"\nSaved: {output_path}")

    return top_features


def main():

    print("=" * 70)
    print("PHASE 18 — SHAP / XAI")
    print("=" * 70)

    X_sample, model = load_data_and_model()

    explainer = create_shap_explainer(model)

    shap_values = compute_shap_values(
        explainer,
        X_sample
    )

    plot_summary(
        shap_values,
        X_sample
    )

    plot_bar(
        shap_values,
        X_sample
    )

    plot_individual(
        explainer,
        shap_values,
        X_sample
    )

    top_features = get_top_features(
        shap_values,
        X_sample,
        top_n=20
    )

    print("\n" + "=" * 70)
    print("PHASE 18 — SHAP EXPLANATION COMPLETE")
    print("=" * 70)

    print("\nTop 5 features:")

    print(
        top_features
        .head(5)
        .to_string(index=False)
    )


if __name__ == "__main__":
    main()