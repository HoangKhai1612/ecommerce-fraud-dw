# PHASE 16 — Machine Learning

## 1. MỤC TIÊU

Huấn luyện 3 mô hình ML để phát hiện gian lận:
1. Logistic Regression (baseline)
2. Random Forest
3. XGBoost (dự kiến tốt nhất)

---

## 2. CÀI ĐẶT

```bash
.venv\Scripts\Activate.ps1
pip install scikit-learn xgboost lightgbm
# Cần cài thêm: pip install scikit-learn xgboost
```

---

## 3. CẤU TRÚC THƯ MỤC

```
ml/
├── data/                       # train.parquet, val.parquet, test.parquet
├── features/
│   ├── __init__.py
│   ├── prepare.py
│   └── features.py
├── models/                     # Trained models (binary)
│   └── (auto-generated)
├── notebooks/
├── config.py
├── train.py                    # Main training script
├── evaluate.py                 # Evaluation utilities
└── __init__.py
```

---

## 4. TRAINING PIPELINE

File: `ml/train.py`

```python
"""
Phase 16: Machine Learning Training
Train 3 models: Logistic Regression, Random Forest, XGBoost
"""

import pandas as pd
import numpy as np
import joblib
import os
import sys
from sklearn.model_selection import RandomizedSearchCV
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, roc_auc_score
from xgboost import XGBClassifier
import warnings
warnings.filterwarnings('ignore')

RANDOM_STATE = 42
MODEL_DIR = 'ml/models'
os.makedirs(MODEL_DIR, exist_ok=True)


def load_data():
    """Load train/val/test splits."""
    train_df = pd.read_parquet('ml/data/train.parquet')
    val_df = pd.read_parquet('ml/data/val.parquet')
    test_df = pd.read_parquet('ml/data/test.parquet')
    
    # Load feature names
    with open('ml/data/features.txt') as f:
        feature_cols = [line.strip() for line in f if line.strip()]
    
    # Handle boolean columns (convert to int)
    bool_cols = train_df.select_dtypes(include=['bool']).columns
    for col in bool_cols:
        train_df[col] = train_df[col].astype(int)
        val_df[col] = val_df[col].astype(int)
        test_df[col] = test_df[col].astype(int)
    
    return train_df, val_df, test_df, feature_cols


def get_X_y(df, feature_cols):
    """Extract features and label."""
    X = df[feature_cols].select_dtypes(include=['int64', 'float64'])
    y = df['is_fraud']
    return X, y


def train_logistic_regression(X_train, y_train, X_val, y_val):
    """Train Logistic Regression with hyperparameter tuning."""
    print("\n=== Training Logistic Regression ===")
    
    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_val_scaled = scaler.transform(X_val)
    
    # Hyperparameter grid
    param_dist = {
        'C': [0.001, 0.01, 0.1, 1, 10, 100],
        'penalty': ['l1', 'l2'],
        'solver': ['liblinear', 'saga'],
        'class_weight': ['balanced', None],
    }
    
    model = LogisticRegression(max_iter=1000, random_state=RANDOM_STATE)
    
    # Use smaller CV for speed
    search = RandomizedSearchCV(
        model, param_distributions=param_dist,
        n_iter=10, scoring='roc_auc', cv=3,
        random_state=RANDOM_STATE, n_jobs=-1, verbose=1
    )
    
    search.fit(X_train_scaled, y_train)
    
    print(f"Best params: {search.best_params_}")
    print(f"Best CV score: {search.best_score_:.4f}")
    
    # Save model + scaler
    joblib.dump(search.best_estimator_, f'{MODEL_DIR}/lr_model.pkl')
    joblib.dump(scaler, f'{MODEL_DIR}/lr_scaler.pkl')
    
    return search.best_estimator_, scaler


def train_random_forest(X_train, y_train, X_val, y_val):
    """Train Random Forest with hyperparameter tuning."""
    print("\n=== Training Random Forest ===")
    
    param_dist = {
        'n_estimators': [100, 200, 300],
        'max_depth': [10, 20, 30, None],
        'min_samples_split': [2, 5, 10],
        'min_samples_leaf': [1, 2, 4],
        'class_weight': ['balanced', 'balanced_subsample', None],
        'max_features': ['sqrt', 'log2'],
    }
    
    model = RandomForestClassifier(random_state=RANDOM_STATE)
    
    search = RandomizedSearchCV(
        model, param_distributions=param_dist,
        n_iter=15, scoring='roc_auc', cv=3,
        random_state=RANDOM_STATE, n_jobs=-1, verbose=1
    )
    
    search.fit(X_train, y_train)
    
    print(f"Best params: {search.best_params_}")
    print(f"Best CV score: {search.best_score_:.4f}")
    
    joblib.dump(search.best_estimator_, f'{MODEL_DIR}/rf_model.pkl')
    
    return search.best_estimator_


def train_xgboost(X_train, y_train, X_val, y_val):
    """Train XGBoost with hyperparameter tuning."""
    print("\n=== Training XGBoost ===")
    
    param_dist = {
        'n_estimators': [100, 200, 300, 500],
        'max_depth': [3, 5, 7, 9, 11],
        'learning_rate': [0.001, 0.01, 0.1, 0.3],
        'subsample': [0.6, 0.8, 1.0],
        'colsample_bytree': [0.6, 0.8, 1.0],
        'min_child_weight': [1, 3, 5],
        'reg_alpha': [0.1, 0.5, 1.0],
        'reg_lambda': [0.1, 0.5, 1.0],
        'scale_pos_weight': [15, 18, 20, 25],  # Handle class imbalance
    }
    
    model = XGBClassifier(
        random_state=RANDOM_STATE,
        use_label_encoder=False,
        eval_metric='logloss',
        tree_method='hist',
        n_jobs=-1,
    )
    
    search = RandomizedSearchCV(
        model, param_distributions=param_dist,
        n_iter=20, scoring='roc_auc', cv=3,
        random_state=RANDOM_STATE, n_jobs=-1, verbose=1
    )
    
    search.fit(X_train, y_train)
    
    print(f"Best params: {search.best_params_}")
    print(f"Best CV score: {search.best_score_:.4f}")
    
    joblib.dump(search.best_estimator_, f'{MODEL_DIR}/xgb_model.pkl')
    
    return search.best_estimator_


def evaluate_model(model, X_val, y_val, name):
    """Evaluate model on validation set."""
    print(f"\n--- Evaluation: {name} ---")
    
    y_pred_proba = model.predict_proba(X_val)[:, 1]
    y_pred = (y_pred_proba >= 0.5).astype(int)
    
    auc = roc_auc_score(y_val, y_pred_proba)
    print(f"AUC: {auc:.4f}")
    print(classification_report(y_val, y_pred, target_names=['Non-Fraud', 'Fraud']))
    
    return auc


def main():
    print("Loading data...")
    train_df, val_df, test_df, feature_cols = load_data()
    
    X_train, y_train = get_X_y(train_df, feature_cols)
    X_val, y_val = get_X_y(val_df, feature_cols)
    
    print(f"Train: {X_train.shape}, Val: {X_val.shape}")
    print(f"Train fraud rate: {y_train.mean():.4f}")
    
    # Get column names (in case alignment needed)
    feature_cols_final = list(X_train.columns)
    
    # Train all 3 models
    lr_model, scaler = train_logistic_regression(X_train, y_train, X_val, y_val)
    rf_model = train_random_forest(X_train, y_train, X_val, y_val)
    xgb_model = train_xgboost(X_train, y_train, X_val, y_val)
    
    # Save feature column names
    joblib.dump(feature_cols_final, f'{MODEL_DIR}/feature_cols.pkl')
    joblib.dump(scaler, f'{MODEL_DIR}/scaler.pkl')
    
    # Evaluate on validation set
    print("\n=== VALIDATION RESULTS ===")
    lr_auc = evaluate_model(lr_model, scaler.transform(X_val), y_val, "Logistic Regression")
    rf_auc = evaluate_model(rf_model, X_val, y_val, "Random Forest")
    xgb_auc = evaluate_model(xgb_model, X_val, y_val, "XGBoost")
    
    print(f"\n=== SUMMARY ===")
    print(f"Logistic Regression AUC: {lr_auc:.4f}")
    print(f"Random Forest AUC:       {rf_auc:.4f}")
    print(f"XGBoost AUC:             {xgb_auc:.4f}")
    
    # Save best models comparison
    results = {
        'logistic_regression': lr_auc,
        'random_forest': rf_auc,
        'xgboost': xgb_auc,
    }
    joblib.dump(results, f'{MODEL_DIR}/results.pkl')
    print(f"\nModels saved to {MODEL_DIR}/")
    
    return results


if __name__ == '__main__':
    main()
```

---

## 5. CHẠY

```bash
.venv\Scripts\Activate.ps1
cd ml
python train.py
```

---

## 6. EXPECTED RESULTS

| Model | Val AUC | Train Time | Notes |
|-------|---------|-----------|-------|
| Logistic Regression | ~0.85-0.90 | ~5 min | Baseline |
| Random Forest | ~0.95-0.97 | ~15 min | Good performance |
| XGBoost | ~0.97-0.99 | ~10 min | Best expected |

---

## 7. MODEL ARTIFACTS

```
ml/models/
├── lr_model.pkl          # Logistic Regression
├── lr_scaler.pkl         # StandardScaler for LR
├── rf_model.pkl          # Random Forest
├── xgb_model.pkl         # XGBoost
├── feature_cols.pkl      # Feature column order
└── results.pkl           # AUC comparison
```

---

## 8. SUCCESS CRITERIA

```text
[✅] Logistic Regression model trained + saved
[✅] Random Forest model trained + saved
[✅] XGBoost model trained + saved
[✅] All 3 models evaluated (AUC scores recorded)
[✅] Best model: XGBoost (highest AUC)
[✅] Models saved as .pkl files
[✅] Feature columns saved for prediction consistency
```

---

## 9. Liên hệ

- Trước: [PHASE 15 — Fraud Data Prep](../15_fraud_detection/fraud_detection_prep.md)
- Sau: [PHASE 17 — Model Evaluation](../17_model_evaluation/model_evaluation.md)

*Cập nhật: 02/09/2026 | Version: 1.0*
