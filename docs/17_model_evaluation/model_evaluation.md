# PHASE 17 — Model Evaluation

## 1. MỤC TIÊU

Đánh giá 3 mô hình (Logistic Regression, Random Forest, XGBoost) trên **held-out test set** bằng metrics đầy đủ:
- ROC-AUC, PR-AUC
- Precision, Recall, F1, F1-macro
- Confusion matrix
- Classification report
- ROC curve + Precision-Recall curve plots

---

## 2. CODE EVALUATION

File: `ml/evaluate.py` (đường dẫn tương đối tính từ **root project**)

```python
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
```

---

## 3. CHẠY

```bash
.venv\Scripts\Activate.ps1
python ml\evaluate.py
```

**Lưu ý:** chạy từ **root project**, KHÔNG `cd ml` rồi `python evaluate.py`, vì code dùng đường dẫn tương đối từ root (`ml/data/test.parquet`, `ml/models`).

Phụ thuộc: `matplotlib` (nếu thiếu: `pip install matplotlib`).

---

## 4. KẾT QUẢ THỰC TẾ (ACTUAL RESULTS — test set 88,581 samples)

Test set: **88,581** samples — 3,099 fraud (**3.4985%**, khớp Phase 15).
Threshold mặc định: **0.5**. Features: **1,014**.

### 4.1 Bảng so sánh tổng hợp

| Model | ROC-AUC | PR-AUC | Precision | Recall | F1 | F1-macro |
|-------|---------|--------|-----------|--------|-----|----------|
| XGBoost | **0.917245** | 0.600815 | 0.319582 | **0.709906** | 0.440749 | 0.703677 |
| Random Forest | 0.915310 | **0.650867** | **0.944210** | 0.360439 | **0.521719** | **0.754936** |
| Logistic Regression | 0.872100 | 0.486336 | 0.820728 | 0.283640 | 0.421583 | 0.703820 |

`>>> BEST MODEL BY ROC-AUC: XGBoost (ROC-AUC = 0.917245)`

### 4.2 Confusion matrix (threshold 0.5)

| Model | TN | FP | FN | TP |
|-------|----|----|----|----|
| Logistic Regression | 85,290 | 192 | 2,220 | 879 |
| Random Forest | 85,416 | 66 | 1,982 | 1,117 |
| XGBoost | 80,798 | 4,684 | 899 | 2,200 |

### 4.3 Classification report (verbatim từ output)

**Logistic Regression**
```
              precision    recall  f1-score   support

   Non-Fraud       0.97      1.00      0.99     85482
       Fraud       0.82      0.28      0.42      3099

    accuracy                           0.97     88581
   macro avg       0.90      0.64      0.70     88581
weighted avg       0.97      0.97      0.97     88581
```

**Random Forest**
```
              precision    recall  f1-score   support

   Non-Fraud       0.98      1.00      0.99     85482
       Fraud       0.94      0.36      0.52      3099

    accuracy                           0.98     88581
   macro avg       0.96      0.68      0.75     88581
weighted avg       0.98      0.98      0.97     88581
```

**XGBoost**
```
              precision    recall  f1-score   support

   Non-Fraud       0.99      0.95      0.97     85482
       Fraud       0.32      0.71      0.44      3099

    accuracy                           0.94     88581
   macro avg       0.65      0.83      0.70     88581
weighted avg       0.97      0.94      0.95     88581
```

### 4.4 Phân tích (quan trọng cho luận văn)

- **XGBoost** thắng về **ROC-AUC (0.9172)** và **Recall (0.7099)** — bắt được ~71% gian lận, nhưng **Precision chỉ 0.32** (4,684 FP): ở threshold 0.5 nó flag rất nhiều giao dịch vô hại.
- **Random Forest** thắng về **PR-AUC (0.6509)**, **Precision (0.9442)**, **F1 (0.5217)**, **F1-macro (0.7549)** — gần như mỗi flag là gian lận thật, nhưng **Recall chỉ 0.36** (bỏ sót 1,982 fraud).
- **Không thể kết luận "XGBoost >= tất cả"**: XGBoost chỉ dẫn đầu về ROC-AUC và recall. Trên PR-AUC, Precision, F1, F1-macro, Random Forest tốt hơn rõ rệt.
- Nguyên nhân: threshold 0.5 không tối ưu cho mọi mô hình; XGBoost có phân bố xác suất khác (cần threshold tuning / calibration — có thể xem xét ở Phase 18+).
- Kết quả thực tế **thấp hơn khoảng kỳ vọng tham khảo** ban đầu (XGBoost ROC-AUC 0.917 vs kỳ vọng 0.97–0.99). Đây là số liệu thực nghiệm trên test set, lấy từ `evaluation_summary.csv` / `evaluation_results.pkl`.

### 4.5 Bảng kỳ vọng tham khảo (KHÔNG dùng làm kết quả luận văn)

| Model | ROC-AUC | PR-AUC | Precision | Recall | F1 |
|-------|---------|--------|-----------|--------|-----|
| Logistic Regression | 0.85–0.90 | 0.15–0.25 | 0.70+ | 0.60+ | 0.65+ |
| Random Forest | 0.95–0.97 | 0.30–0.45 | 0.80+ | 0.70+ | 0.75+ |
| XGBoost | 0.97–0.99 | 0.45–0.65 | 0.85+ | 0.75+ | 0.80+ |

Chỉ LR nằm trong khoảng kỳ vọng. RF và XGBoost thấp hơn — ghi đúng số thực tế vào báo cáo.

---

## 5. EVIDENCE FILES

```
ml/models/
├── logistic_regression_eval.png   # ROC + PR curve (LR)
├── random_forest_eval.png         # ROC + PR curve (RF)
├── xgboost_eval.png               # ROC + PR curve (XGBoost)
├── evaluation_results.pkl         # Full results (dict list, có curve data)
├── evaluation_summary.csv         # Bảng so sánh metrics
└── [saved models từ Phase 16]

evidence/phase_17/
└── execution_log.txt              # Log chạy evaluate.py
```

Tên file plot: `model_name.lower().replace(" ", "_") + "_eval.png"` →
`logistic_regression_eval.png`, `random_forest_eval.png`, `xgboost_eval.png`
(**không phải** lr_eval.png / rf_eval.png / xgb_eval.png).

---

## 6. SUCCESS CRITERIA (kiểm tra thực tế 08/10/2026)

```text
[✅] Test set = 88,581 samples
[✅] Fraud rate test = 3.4985% (3,099 fraud) — khớp Phase 15
[✅] Logistic Regression evaluated (ROC-AUC 0.872100)
[✅] Random Forest evaluated (ROC-AUC 0.915310)
[✅] XGBoost evaluated (ROC-AUC 0.917245)
[✅] ROC-AUC + PR-AUC + Precision + Recall + F1 + F1-macro đầy đủ
[✅] Confusion matrix + classification report đầy đủ
[✅] 3 ROC/PR plots được tạo (logistic_regression_eval.png, random_forest_eval.png, xgboost_eval.png)
[✅] evaluation_results.pkl được tạo (~4.9 MB)
[✅] evaluation_summary.csv được tạo
[⚠️] "XGBoost >= all other models" — CHỈ ĐÚNG trên ROC-AUC và Recall.
     Trên PR-AUC, Precision, F1, F1-macro: Random Forest thắng.
     → Luận văn ghi: XGBoost best về ranking (ROC-AUC)/recall,
       Random Forest best về precision/F1 ở threshold 0.5.
```

---

## 7. Liên hệ

- Trước: [PHASE 16 — Machine Learning](../16_machine_learning/machine_learning.md)
- Sau: [PHASE 18 — SHAP/XAI](../18_shap/shap_explanation.md)

*Cập nhật: 08/10/2026 | Version: 2.1 (kết quả thực nghiệm)*
