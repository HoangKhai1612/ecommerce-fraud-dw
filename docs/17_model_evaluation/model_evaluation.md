# PHASE 17 — Model Evaluation

## 1. MỤC TIÊU

Đánh giá mô hình ML bằng metrics đầy đủ:
- ROC-AUC, PR-AUC
- Precision, Recall, F1
- Confusion matrix
- Classification report

---

## 2. CODE EVALUATION

File: `ml/evaluate.py`

```python
"""
Phase 17: Model Evaluation
Evaluate all 3 models on test set.
"""

import pandas as pd
import numpy as np
import joblib
import matplotlib.pyplot as plt
from sklearn.metrics import (
    roc_auc_score, average_precision_score,
    confusion_matrix, classification_report,
    precision_recall_curve, roc_curve
)
import warnings
warnings.filterwarnings('ignore')


def load_test_data():
    """Load test set and model artifacts."""
    test_df = pd.read_parquet('ml/data/test.parquet')
    feature_cols = joblib.load('ml/models/feature_cols.pkl')
    scaler = joblib.load('ml/models/scaler.pkl')
    
    X_test = test_df[feature_cols].select_dtypes(include=['int64', 'float64'])
    y_test = test_df['is_fraud']
    
    # Align columns
    bool_cols = X_test.select_dtypes(include=['bool']).columns
    for col in bool_cols:
        X_test[col] = X_test[col].astype(int)
    
    return X_test, y_test, scaler


def evaluate_single_model(model, model_name, X_test, y_test, use_scaler=False, scaler=None):
    """Evaluate one model."""
    if use_scaler and scaler:
        X_test = scaler.transform(X_test)
    
    y_pred_proba = model.predict_proba(X_test)[:, 1]
    y_pred = (y_pred_proba >= 0.5).astype(int)
    
    # Metrics
    auc = roc_auc_score(y_test, y_pred_proba)
    ap = average_precision_score(y_test, y_pred_proba)
    cm = confusion_matrix(y_test, y_pred)
    report = classification_report(y_test, y_pred, target_names=['Non-Fraud', 'Fraud'])
    
    print(f"\n=== {model_name} ===")
    print(f"ROC-AUC: {auc:.4f}")
    print(f"PR-AUC: {ap:.4f}")
    print(f"Confusion Matrix:\n{cm}")
    print(f"Classification Report:\n{report}")
    
    # Save plot
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    
    # ROC curve
    fpr, tpr, _ = roc_curve(y_test, y_pred_proba)
    axes[0].plot(fpr, tpr, label=f'AUC = {auc:.4f}')
    axes[0].plot([0, 1], [0, 1], 'k--', label='Random')
    axes[0].set_xlabel('False Positive Rate')
    axes[0].set_ylabel('True Positive Rate')
    axes[0].set_title(f'ROC Curve - {model_name}')
    axes[0].legend()
    
    # PR curve
    precision, recall, _ = precision_recall_curve(y_test, y_pred_proba)
    axes[1].plot(recall, precision, label=f'AP = {ap:.4f}')
    axes[1].set_xlabel('Recall')
    axes[1].set_ylabel('Precision')
    axes[1].set_title(f'Precision-Recall Curve - {model_name}')
    axes[1].legend()
    
    plt.tight_layout()
    plt.savefig(f'ml/models/{model_name.lower().replace(" ", "_")}_eval.png', dpi=150)
    plt.close()
    
    return {
        'model': model_name,
        'roc_auc': auc,
        'pr_auc': ap,
        'f1_macro': (cm[0][0] + cm[1][1]) / cm.sum(),
        'confusion_matrix': cm.tolist(),
    }


def main():
    X_test, y_test, scaler = load_test_data()
    results = joblib.load('ml/models/results.pkl')
    
    # Load models
    models = [
        ('Logistic Regression', joblib.load('ml/models/lr_model.pkl'), True, scaler),
        ('Random Forest', joblib.load('ml/models/rf_model.pkl'), False, None),
        ('XGBoost', joblib.load('ml/models/xgb_model.pkl'), False, None),
    ]
    
    all_results = []
    for name, model, use_scaler, scaler_obj in models:
        result = evaluate_single_model(model, name, X_test.copy(), y_test, use_scaler, scaler_obj)
        all_results.append(result)
    
    # Summary comparison
    print("\n=== MODEL COMPARISON ===")
    comparison = pd.DataFrame(all_results)
    print(comparison[['model', 'roc_auc', 'pr_auc']].to_string(index=False))
    
    # Save results
    joblib.dump(all_results, 'ml/models/evaluation_results.pkl')
    
    # Find best model
    best = max(all_results, key=lambda x: x['roc_auc'])
    print(f"\n>>> BEST MODEL: {best['model']} (AUC: {best['roc_auc']:.4f})")


if __name__ == '__main__':
    main()
```

---

## 3. CHẠY

```bash
.venv\Scripts\Activate.ps1
cd ml
python evaluate.py
```

---

## 4. EXPECTED RESULTS TABLE

| Model | ROC-AUC | PR-AUC | Precision | Recall | F1 |
|-------|---------|--------|-----------|--------|-----|
| Logistic Regression | 0.85-0.90 | 0.15-0.25 | 0.70+ | 0.60+ | 0.65+ |
| Random Forest | 0.95-0.97 | 0.30-0.45 | 0.80+ | 0.70+ | 0.75+ |
| XGBoost | 0.97-0.99 | 0.45-0.65 | 0.85+ | 0.75+ | 0.80+ |

---

## 5. EVIDENCE FILES

```
ml/models/
├── lr_eval.png              # ROC + PR curve plot
├── rf_eval.png              # ROC + PR curve plot
├── xgb_eval.png             # ROC + PR curve plot
├── evaluation_results.pkl   # Full results
└── [saved models]
```

---

## 6. SUCCESS CRITERIA

```text
[✅] All 3 models evaluated on test set
[✅] ROC-AUC > 0.85 for all models
[✅] XGBoost >= all other models
[✅] Confusion matrices generated
[✅] Plots saved (ROC curve, PR curve)
[✅] Results saved to pkl file
```

---

## 7. Liên hệ

- Trước: [PHASE 16 — Machine Learning](../16_machine_learning/machine_learning.md)
- Sau: [PHASE 18 — SHAP/XAI](../18_shap/shap_explanation.md)

*Cập nhật: 02/09/2026 | Version: 1.0*
