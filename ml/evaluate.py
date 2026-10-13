"""
Phase 17: Model Evaluation

Evaluate Logistic Regression, Random Forest and XGBoost
on the held-out test set.
"""

import json
import os
import warnings

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from sklearn.metrics import (
    average_precision_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)

warnings.filterwarnings("ignore")


TEST_PATH = "ml/data/test.parquet"
MODELS_DIR = "ml/models"


def load_test_data():
    """Load the held-out test set and preprocessing artifacts."""

    test_df = pd.read_parquet(TEST_PATH)

    # Load feature columns from JSON
    with open(
        os.path.join(MODELS_DIR, "feature_columns.json"),
        "r",
        encoding="utf-8",
    ) as f:
        feature_cols = json.load(f)

    # Load scaler (only for Logistic Regression)
    scaler_path = os.path.join(MODELS_DIR, "logistic_scaler.pkl")
    scaler = None
    if os.path.exists(scaler_path):
        scaler = joblib.load(scaler_path)

    X_test = test_df[feature_cols].copy()

    # Convert boolean features to integer if present.
    bool_cols = X_test.select_dtypes(include=["bool"]).columns

    for col in bool_cols:
        X_test[col] = X_test[col].astype(int)

    # Keep numeric features only.
    X_test = X_test.select_dtypes(
        include=["int64", "int32", "float64", "float32"]
    )

    y_test = test_df["is_fraud"].astype(int)

    return X_test, y_test, scaler


def evaluate_single_model(
    model,
    model_name,
    X_test,
    y_test,
    use_scaler=False,
    scaler=None,
):
    """Evaluate one model on the test set."""

    X_eval = X_test.copy()

    if use_scaler:
        if scaler is None:
            raise ValueError(
                f"Scaler is required for {model_name}."
            )

        X_eval = scaler.transform(X_eval)

    # Probability of fraud class.
    y_pred_proba = model.predict_proba(X_eval)[:, 1]

    # Default classification threshold.
    threshold = 0.5

    y_pred = (
        y_pred_proba >= threshold
    ).astype(int)

    # Main ranking metrics.
    roc_auc = roc_auc_score(
        y_test,
        y_pred_proba,
    )

    pr_auc = average_precision_score(
        y_test,
        y_pred_proba,
    )

    # Classification metrics.
    precision = precision_score(
        y_test,
        y_pred,
        zero_division=0,
    )

    recall = recall_score(
        y_test,
        y_pred,
        zero_division=0,
    )

    f1 = f1_score(
        y_test,
        y_pred,
        zero_division=0,
    )

    f1_macro = f1_score(
        y_test,
        y_pred,
        average="macro",
        zero_division=0,
    )

    # Confusion matrix.
    cm = confusion_matrix(
        y_test,
        y_pred,
    )

    tn, fp, fn, tp = cm.ravel()

    # Classification report.
    report = classification_report(
        y_test,
        y_pred,
        target_names=["Non-Fraud", "Fraud"],
        zero_division=0,
    )

    print()
    print("=" * 60)
    print(model_name)
    print("=" * 60)

    print(f"ROC-AUC : {roc_auc:.6f}")
    print(f"PR-AUC  : {pr_auc:.6f}")
    print(f"Precision: {precision:.6f}")
    print(f"Recall   : {recall:.6f}")
    print(f"F1       : {f1:.6f}")
    print(f"F1 Macro : {f1_macro:.6f}")

    print("\nConfusion Matrix:")
    print(cm)

    print("\nClassification Report:")
    print(report)

    # ---------------------------------------------------------
    # Plot ROC and Precision-Recall curves.
    # ---------------------------------------------------------

    fpr, tpr, _ = roc_curve(
        y_test,
        y_pred_proba,
    )

    precision_curve, recall_curve, _ = (
        precision_recall_curve(
            y_test,
            y_pred_proba,
        )
    )

    fig, axes = plt.subplots(
        1,
        2,
        figsize=(12, 5),
    )

    # ROC.
    axes[0].plot(
        fpr,
        tpr,
        label=f"ROC-AUC = {roc_auc:.4f}",
    )

    axes[0].plot(
        [0, 1],
        [0, 1],
        linestyle="--",
        label="Random",
    )

    axes[0].set_xlabel(
        "False Positive Rate"
    )

    axes[0].set_ylabel(
        "True Positive Rate"
    )

    axes[0].set_title(
        f"ROC Curve - {model_name}"
    )

    axes[0].legend()

    # Precision-Recall.
    axes[1].plot(
        recall_curve,
        precision_curve,
        label=f"PR-AUC = {pr_auc:.4f}",
    )

    axes[1].set_xlabel(
        "Recall"
    )

    axes[1].set_ylabel(
        "Precision"
    )

    axes[1].set_title(
        f"Precision-Recall Curve - {model_name}"
    )

    axes[1].legend()

    plt.tight_layout()

    filename = (
        model_name.lower()
        .replace(" ", "_")
        + "_eval.png"
    )

    output_path = os.path.join(
        MODELS_DIR,
        filename,
    )

    plt.savefig(
        output_path,
        dpi=150,
        bbox_inches="tight",
    )

    plt.close()

    return {
        "model": model_name,
        "threshold": threshold,
        "roc_auc": roc_auc,
        "pr_auc": pr_auc,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "f1_macro": f1_macro,
        "tn": int(tn),
        "fp": int(fp),
        "fn": int(fn),
        "tp": int(tp),
        "confusion_matrix": cm.tolist(),
        "classification_report": report,
        "roc_curve": {
            "fpr": fpr.tolist(),
            "tpr": tpr.tolist(),
        },
        "pr_curve": {
            "precision": precision_curve.tolist(),
            "recall": recall_curve.tolist(),
        },
        "plot_path": output_path,
    }


def main():

    print("Loading test data...")

    X_test, y_test, scaler = load_test_data()

    print(
        f"Test samples : {len(X_test):,}"
    )

    print(
        f"Features      : {X_test.shape[1]:,}"
    )

    print(
        f"Fraud samples : {int(y_test.sum()):,}"
    )

    print(
        f"Fraud rate    : {y_test.mean():.4%}"
    )

    # ---------------------------------------------------------
    # Load trained models.
    # ---------------------------------------------------------

    models = [
        (
            "Logistic Regression",
            joblib.load(
                os.path.join(
                    MODELS_DIR,
                    "logistic_regression.pkl",
                )
            ),
            True,
            scaler,
        ),
        (
            "Random Forest",
            joblib.load(
                os.path.join(
                    MODELS_DIR,
                    "random_forest.pkl",
                )
            ),
            False,
            None,
        ),
        (
            "XGBoost",
            joblib.load(
                os.path.join(
                    MODELS_DIR,
                    "xgboost.pkl",
                )
            ),
            False,
            None,
        ),
    ]

    # ---------------------------------------------------------
    # Evaluate all models.
    # ---------------------------------------------------------

    all_results = []

    for (
        name,
        model,
        use_scaler,
        scaler_obj,
    ) in models:

        result = evaluate_single_model(
            model=model,
            model_name=name,
            X_test=X_test,
            y_test=y_test,
            use_scaler=use_scaler,
            scaler=scaler_obj,
        )

        all_results.append(result)

    # ---------------------------------------------------------
    # Model comparison.
    # ---------------------------------------------------------

    comparison = pd.DataFrame(
        [
            {
                "model": r["model"],
                "roc_auc": r["roc_auc"],
                "pr_auc": r["pr_auc"],
                "precision": r["precision"],
                "recall": r["recall"],
                "f1": r["f1"],
                "f1_macro": r["f1_macro"],
            }
            for r in all_results
        ]
    )

    comparison = comparison.sort_values(
        "roc_auc",
        ascending=False,
    )

    print()
    print("=" * 80)
    print("MODEL COMPARISON")
    print("=" * 80)

    print(
        comparison.to_string(
            index=False,
            float_format=lambda x: f"{x:.6f}",
        )
    )

    # Save evaluation results.
    evaluation_path = os.path.join(
        MODELS_DIR,
        "evaluation_results.pkl",
    )

    joblib.dump(
        all_results,
        evaluation_path,
    )

    # Save human-readable CSV.
    csv_path = os.path.join(
        MODELS_DIR,
        "evaluation_summary.csv",
    )

    comparison.to_csv(
        csv_path,
        index=False,
    )

    # Best model by ROC-AUC.
    best = max(
        all_results,
        key=lambda x: x["roc_auc"],
    )

    print()
    print(
        f">>> BEST MODEL BY ROC-AUC: "
        f"{best['model']} "
        f"(ROC-AUC = {best['roc_auc']:.6f})"
    )

    print()
    print(
        f"Saved: {evaluation_path}"
    )

    print(
        f"Saved: {csv_path}"
    )


if __name__ == "__main__":
    main()