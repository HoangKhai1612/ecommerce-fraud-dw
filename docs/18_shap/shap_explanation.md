# PHASE 18 — SHAP / XAI

## 1. MỤC TIÊU

Sử dụng SHAP (SHapley Additive exPlanations) để giải thích quyết định của mô hình XGBoost:
- Hiểu tại sao mỗi giao dịch bị đánh dấu là gian lận
- Visualize top features quan trọng nhất

---

## 2. CÀI ĐẶT

```bash
pip install shap matplotlib
```

---

## 3. CODE SHAP EXPLANATION

File: `ml/shap_explain.py`

```python
"""
Phase 18: SHAP Explanation
Explain XGBoost model predictions using SHAP values.
"""

import pandas as pd
import numpy as np
import joblib
import shap
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')

# Limit to 5000 samples for performance
SAMPLE_SIZE = 5000
RANDOM_STATE = 42


def load_data_and_model():
    """Load test data and best model."""
    test_df = pd.read_parquet('ml/data/test.parquet')
    feature_cols = joblib.load('ml/models/feature_cols.pkl')
    
    X_test = test_df[feature_cols].select_dtypes(include=['int64', 'float64'])
    
    # Handle bool columns
    bool_cols = X_test.select_dtypes(include=['bool']).columns
    for col in bool_cols:
        X_test[col] = X_test[col].astype(int)
    
    # Sample for SHAP
    X_sample = X_test.sample(n=min(SAMPLE_SIZE, len(X_test)), random_state=RANDOM_STATE)
    
    model = joblib.load('ml/models/xgb_model.pkl')
    
    return X_sample, model


def create_shap_explainer(model):
    """Create SHAP explainer for XGBoost model."""
    # For XGBoost, use TreeExplainer (fast)
    explainer = shap.TreeExplainer(model)
    return explainer


def compute_shap_values(explainer, X):
    """Compute SHAP values for the dataset."""
    shap_values = explainer.shap_values(X)
    return shap_values


def plot_summary(shap_values, X):
    """Plot SHAP summary (beeswarm plot)."""
    # Determine if binary or multiclass
    if isinstance(shap_values, list):
        # Binary: take fraud class (index 1)
        sv = shap_values[1]
    else:
        sv = shap_values
    
    shap.summary_plot(sv, X, plot_type="dot", show=False)
    plt.title("SHAP Summary — Feature Importance")
    plt.tight_layout()
    plt.savefig('ml/models/shap_summary.png', dpi=150, bbox_inches='tight')
    plt.close()


def plot_bar(shap_values, X):
    """Plot SHAP bar chart."""
    if isinstance(shap_values, list):
        sv = shap_values[1]
    else:
        sv = shap_values
    
    shap.summary_plot(sv, X, plot_type="bar", show=False)
    plt.title("SHAP Feature Importance (Bar)")
    plt.tight_layout()
    plt.savefig('ml/models/shap_bar.png', dpi=150, bbox_inches='tight')
    plt.close()


def plot_individual(explainer, X, model, indices=[0, 100, 500]):
    """Explain individual predictions."""
    for idx in indices:
        shap.force_plot(
            explainer.expected_value,
            explainer.shap_values(X.iloc[idx:idx+1])[0],  # for binary
            X.iloc[idx],
            matplotlib=True,
            show=False
        )
        plt.title(f"SHAP Force Plot — Sample #{idx}")
        plt.tight_layout()
        plt.savefig(f'ml/models/shap_individual_{idx}.png', dpi=150, bbox_inches='tight')
        plt.close()


def get_top_features(shap_values, X, top_n=20):
    """Get top N most important features."""
    if isinstance(shap_values, list):
        sv = shap_values[1]
    else:
        sv = shap_values
    
    mean_abs_shap = np.abs(sv).mean(axis=0)
    feature_names = X.columns.tolist()
    
    importance_df = pd.DataFrame({
        'feature': feature_names,
        'mean_abs_shap': mean_abs_shap
    }).sort_values('mean_abs_shap', ascending=False)
    
    top_features = importance_df.head(top_n)
    print(f"\nTop {top_n} features:")
    print(top_features.to_string(index=False))
    
    # Save
    top_features.to_csv(f'ml/models/top_features.csv', index=False)
    return top_features


def main():
    print("Loading data and best model...")
    X_sample, model = load_data_and_model()
    print(f"Sample size: {len(X_sample)}")
    
    print("Creating SHAP explainer...")
    explainer = create_shap_explainer(model)
    
    print("Computing SHAP values...")
    shap_values = compute_shap_values(explainer, X_sample)
    
    print("Generating plots...")
    plot_summary(shap_values, X_sample)
    plot_bar(shap_values, X_sample)
    plot_individual(explainer, X_sample, model)
    
    top_features = get_top_features(shap_values, X_sample, top_n=20)
    
    print("\n=== SHAP EXPLANATION COMPLETE ===")
    print(f"Top 5 features:")
    print(top_features.head(5).to_string(index=False))
    print(f"\nSaved: ml/models/shap_summary.png, ml/models/shap_bar.png, ml/models/top_features.csv")


if __name__ == '__main__':
    main()
```

---

## 4. CHẠY

```bash
.venv\Scripts\Activate.ps1
cd ml
python shap_explain.py
```

---

## 5. EXPECTED OUTPUT

File: `ml/models/top_features.csv`

| Feature | Mean |SHAP| Value |
|---------|--------|-------------|
| V317 | 0.45 | ... |
| V316 | 0.38 | ... |
| id_02 | 0.32 | ... |
| V287 | 0.28 | ... |
| V207 | 0.25 | ... |
| ... | ... | ... |

---

## 6. EVIDENCE FILES

```
ml/models/
├── shap_summary.png          # Beeswarm plot
├── shap_bar.png              # Bar chart
├── shap_individual_0.png     # Force plot sample 0
├── shap_individual_100.png   # Force plot sample 100
├── shap_individual_500.png   # Force plot sample 500
└── top_features.csv          # Top 20 features
```

---

## 7. SUCCESS CRITERIA

```text
[✅] SHAP explainer created for XGBoost
[✅] SHAP values computed (5,000 samples)
[✅] Summary beeswarm plot saved
[✅] Bar chart of feature importance saved
[✅] Individual force plots saved (3 samples)
[✅] Top 20 features exported to CSV
[✅] Top features align with business understanding (Vesta features, id features)
```

---

## 8. Liên hệ

- Trước: [PHASE 17 — Model Evaluation](../17_model_evaluation/model_evaluation.md)
- Sau: [PHASE 19 — Model Integration](../19_model_integration/model_integration.md)

*Cập nhật: 02/09/2026 | Version: 1.0*
