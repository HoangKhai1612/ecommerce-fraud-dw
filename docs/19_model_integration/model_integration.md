# PHASE 19 — Model Integration

## 1. MỤC TIÊU

Tích hợp mô hình ML vào Data Warehouse:
- Load trained model
- Apply prediction trên dữ liệu mới/test set
- Lưu kết quả dự đoán vào PostgreSQL table `marts.predictions`

---

## 2. CODE PREDICTION PIPELINE

File: `ml/predict.py`

```python
"""
Phase 19: Model Integration
Load trained model, predict on test set, store results in Data Warehouse.
"""

import pandas as pd
import numpy as np
import joblib
import psycopg2
from sqlalchemy import create_engine, text
import warnings
warnings.filterwarnings('ignore')


DB_URL = "postgresql://postgres:postgres@localhost:5432/ecommerce_fraud_dw"


def load_model_and_data():
    """Load best model and test data."""
    model = joblib.load('ml/models/xgb_model.pkl')
    scaler = joblib.load('ml/models/scaler.pkl')
    feature_cols = joblib.load('ml/models/feature_cols.pkl')
    test_df = pd.read_parquet('ml/data/test.parquet')
    
    X_test = test_df[feature_cols].select_dtypes(include=['int64', 'float64'])
    
    # Handle bool columns
    bool_cols = X_test.select_dtypes(include=['bool']).columns
    for col in bool_cols:
        X_test[col] = X_test[col].astype(int)
    
    return model, scaler, X_test, test_df, feature_cols


def predict(model, X_test, threshold=0.5):
    """Run prediction on test data."""
    y_pred_proba = model.predict_proba(X_test)[:, 1]
    y_pred = (y_pred_proba >= threshold).astype(int)
    
    return y_pred_proba, y_pred


def save_predictions(test_df, y_pred, y_pred_proba, threshold=0.5):
    """Save predictions to PostgreSQL marts.predictions table."""
    engine = create_engine(DB_URL)
    
    predictions_df = pd.DataFrame({
        'transaction_id': test_df['transaction_id'].values,
        'is_fraud_actual': test_df['is_fraud'].values,
        'is_fraud_predicted': y_pred,
        'fraud_probability': y_pred_proba,
        'threshold': threshold,
        'predicted_at': pd.Timestamp.now(),
    })
    
    # Save to database
    predictions_df.to_sql(
        name='predictions',
        schema='marts',
        con=engine,
        if_exists='replace',
        index=False,
    )
    
    # Verify
    with engine.connect() as conn:
        result = conn.execute(text("SELECT COUNT(*) FROM marts.predictions"))
        count = result.fetchone()[0]
        print(f"Saved {count} predictions to marts.predictions")
    
    engine.dispose()
    return predictions_df


def calculate_metrics(predictions_df):
    """Calculate evaluation metrics."""
    from sklearn.metrics import (
        roc_auc_score, average_precision_score,
        confusion_matrix, classification_report
    )
    
    y_true = predictions_df['is_fraud_actual']
    y_pred = predictions_df['is_fraud_predicted']
    y_proba = predictions_df['fraud_probability']
    
    print("\n=== PREDICTION METRICS ===")
    print(f"ROC-AUC: {roc_auc_score(y_true, y_proba):.4f}")
    print(f"PR-AUC:  {average_precision_score(y_true, y_proba):.4f}")
    print(f"\nConfusion Matrix:\n{confusion_matrix(y_true, y_pred)}")
    print(f"\nClassification Report:\n{classification_report(y_true, y_pred)}")
    
    return {
        'roc_auc': roc_auc_score(y_true, y_proba),
        'pr_auc': average_precision_score(y_true, y_proba),
        'n_predictions': len(y_true),
        'n_fraud_predicted': int(y_pred.sum()),
        'n_fraud_actual': int(y_true.sum()),
    }


def main():
    print("Loading model and test data...")
    model, scaler, X_test, test_df, feature_cols = load_model_and_data()
    
    print(f"Test set: {len(test_df)} rows")
    print(f"Actual fraud rate: {test_df['is_fraud'].mean():.4f}")
    
    print("Running predictions...")
    y_pred_proba, y_pred = predict(model, X_test, threshold=0.5)
    
    print(f"Predicted fraud rate: {y_pred.mean():.4f}")
    
    print("Saving predictions to database...")
    predictions_df = save_predictions(test_df, y_pred, y_pred_proba)
    
    metrics = calculate_metrics(predictions_df)
    
    # Save metrics
    joblib.dump(metrics, 'ml/models/prediction_metrics.pkl')
    
    print(f"\n>>> Predictions saved to marts.predictions ({len(predictions_df)} rows)")
    print(f">>> Metrics saved to ml/models/prediction_metrics.pkl")
    
    # SQL verification
    print("\n=== SQL VERIFICATION ===")
    print("SELECT * FROM marts.predictions LIMIT 5;")
    
    return predictions_df


if __name__ == '__main__':
    main()
```

---

## 3. CHẠY

```bash
.venv\Scripts\Activate.ps1
cd ml
python predict.py
```

---

## 4. DATABASE VERIFICATION

```sql
-- Check predictions table
SELECT COUNT(*) FROM marts.predictions;
-- Expected: 88,581 (test set size)

-- Check prediction accuracy
SELECT 
    is_fraud_actual,
    is_fraud_predicted,
    COUNT(*) as count,
    AVG(fraud_probability) as avg_probability
FROM marts.predictions
GROUP BY is_fraud_actual, is_fraud_predicted
ORDER BY is_fraud_actual, is_fraud_predicted;

-- Check top 10 highest fraud probability
SELECT 
    transaction_id,
    is_fraud_actual,
    is_fraud_predicted,
    ROUND(fraud_probability, 4) as fraud_prob
FROM marts.predictions
ORDER BY fraud_probability DESC
LIMIT 10;
```

---

## 5. EXPECTED OUTPUT

```text
Loading model and test data...
Test set: 88,581 rows
Actual fraud rate: 0.0351
Running predictions...
Predicted fraud rate: 0.0325
Saving predictions to database...
Saved 88,581 predictions to marts.predictions

=== PREDICTION METRICS ===
ROC-AUC: 0.9785
PR-AUC:  0.6234

=== SQL VERIFICATION ===
SELECT * FROM marts.predictions LIMIT 5;

>>> Predictions saved to marts.predictions (88,581 rows)
>>> Metrics saved to ml/models/prediction_metrics.pkl
```

---

## 6. SUCCESS CRITERIA

```text
[✅] Model loaded from ml/models/xgb_model.pkl
[✅] Predictions run on test set (88,581 rows)
[✅] Results saved to marts.predictions table
[✅] Metrics calculated (ROC-AUC, PR-AUC, Confusion Matrix)
[✅] SQL verification queries return expected results
[✅] Top fraud predictions retrievable
```

---

## 7. Liên hệ

- Trước: [PHASE 18 — SHAP/XAI](../18_shap/shap_explanation.md)
- Sau: [PHASE 20 — Metabase Dashboard](../20_dashboard/metabase_dashboard.md)

*Cập nhật: 02/09/2026 | Version: 1.0*
