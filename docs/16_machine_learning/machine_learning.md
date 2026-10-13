# PHASE 16 — Machine Learning

## 1. MỤC TIÊU

Huấn luyện 3 mô hình ML để phát hiện gian lận:
1. Logistic Regression (baseline)
2. Random Forest
3. XGBoost (best model)

So sánh dựa trên **ROC-AUC** trên validation set.

---

## 2. CÀI ĐẶT

```bash
.venv\Scripts\Activate.ps1
pip install scikit-learn xgboost joblib
```

---

## 3. CẤU TRÚC THƯ MỤC THỰC TẾ

```
ml/
├── config.py                      # Configuration
├── features/
│   ├── engineering.py
│   ├── preprocessing.py
│   ├── prepare.py
│   └── __init__.py
├── models/                         # Trained artifacts (auto-generated)
│   ├── logistic_regression.pkl
│   ├── logistic_scaler.pkl
│   ├── random_forest.pkl
│   ├── xgboost.pkl
│   ├── feature_columns.json
│   └── training_results.json
├── data/
│   ├── train.parquet
│   ├── val.parquet
│   ├── test.parquet
│   └── feature_metadata.json
├── train.py                        # Main training script
├── evaluate.py
└── __init__.py
```

---

## 4. TRAINING PIPELINE (ml/train.py)

### 4.1 Data Loading & Validation
```python
train_df = pd.read_parquet('ml/data/train.parquet')  # 413,378 × 1015
val_df = pd.read_parquet('ml/data/val.parquet')      # 88,581 × 1015

# Target: is_fraud (int8), Features: 1014 numeric (float32)
```

### 4.2 Hyperparameter Tuning Strategy
- **Subset tuning**: 50,000 samples (memory efficient)
- **RandomizedSearchCV**: n_iter reduced, cv=2 (fast)
- **Refit on full training data** after best params found
- **n_jobs=1** for CV to limit memory

---

## 5. KẾT QUẢ THỰC TẾ (ACTUAL RESULTS)

### 5.1 Logistic Regression
| Metric | Value |
|--------|-------|
| Best CV ROC-AUC | 0.844992 |
| Best params | `{'C': 0.01, 'penalty': 'l2', 'solver': 'lbfgs', 'class_weight': None}` |
| **Val ROC-AUC** | **0.869964** |
| **Val PR-AUC** | **0.485851** |
| **Val F1 (0.5)** | **0.422111** |
| Precision (0.5) | 0.817424 |
| Recall (0.5) | 0.284516 |

**Confusion Matrix (val, threshold=0.5):**
```
[[85284   197]   ← Non-Fraud: 85,481 total
 [ 2218   882]]  ← Fraud: 3,100 total
```

### 5.2 Random Forest
| Metric | Value |
|--------|-------|
| Best CV ROC-AUC | 0.876630 |
| Best params | `{'n_estimators': 200, 'max_depth': 20, 'min_samples_split': 2, 'min_samples_leaf': 2, 'class_weight': None, 'max_features': 'sqrt'}` |
| **Val ROC-AUC** | **0.912991** |
| **Val PR-AUC** | **0.645182** |
| **Val F1 (0.5)** | **0.521094** |
| Precision (0.5) | 0.925865 |
| Recall (0.5) | 0.362581 |

**Confusion Matrix (val, threshold=0.5):**
```
[[85391    90]
 [ 1976  1124]]
```

### 5.3 XGBoost
| Metric | Value |
|--------|-------|
| Best CV ROC-AUC | 0.891390 |
| Best params | `{'n_estimators': 200, 'max_depth': 5, 'learning_rate': 0.05, 'subsample': 0.8, 'colsample_bytree': 1.0, 'min_child_weight': 3, 'reg_alpha': 0.1, 'reg_lambda': 0.5, 'scale_pos_weight': 15}` |
| **Val ROC-AUC** | **0.916026** |
| **Val PR-AUC** | **0.591256** |
| **Val F1 (0.5)** | **0.438063** |
| Precision (0.5) | 0.316045 |
| Recall (0.5) | 0.713548 |

**Confusion Matrix (val, threshold=0.5):**
```
[[80694  4787]
 [  888  2212]]
```

---

## 6. MODEL COMPARISON (Validation Set)

| Model | ROC-AUC | PR-AUC | F1@0.5 | Precision@0.5 | Recall@0.5 | Best CV ROC-AUC |
|-------|---------|--------|--------|---------------|------------|-----------------|
| **XGBoost** | **0.916026** | 0.591256 | 0.438063 | 0.316045 | **0.713548** | 0.891390 |
| Random Forest | 0.912991 | **0.645182** | **0.521094** | **0.925865** | 0.362581 | 0.876630 |
| Logistic Regression | 0.869964 | 0.485851 | 0.422111 | 0.817424 | 0.284516 | 0.844992 |

**Best Model by ROC-AUC: XGBoost** ✅

---

## 7. KEY INSIGHTS

| Aspect | Finding |
|--------|---------|
| **Best ROC-AUC** | XGBoost (0.916) — marginally better than RF (0.913) |
| **Best PR-AUC** | Random Forest (0.645) — better for imbalanced fraud detection |
| **Best F1@0.5** | Random Forest (0.521) — best balance at default threshold |
| **Best Recall@0.5** | XGBoost (0.714) — catches more fraud cases |
| **Best Precision@0.5** | Random Forest (0.926) — fewer false alarms |

> **Note**: Threshold=0.5 is arbitrary. For production, optimize threshold per business cost matrix (Phase 17).

---

## 8. MODEL ARTIFACTS (ml/models/)

| File | Size | Description |
|------|------|-------------|
| `logistic_regression.pkl` | 4.9 KB | LR model |
| `logistic_scaler.pkl` | 43.8 KB | StandardScaler for LR |
| `random_forest.pkl` | 92.4 MB | RF model (200 trees) |
| `xgboost.pkl` | 562 KB | XGBoost model |
| `feature_columns.json` | 22.7 KB | 1,014 feature names |
| `training_results.json` | 1.4 KB | Full metrics + best_model |

---

## 9. CHẠY PIPELINE

```powershell
.venv\Scripts\Activate.ps1
python -m ml.train
```

**Output thực tế:**
```
======================================================================
PHASE 16 - MACHINE LEARNING
======================================================================
Loading training data...
Train shape: (413378, 1015)
Validation shape: (88581, 1015)

=== DATA VALIDATION ===
Train fraud rate: 0.034990
Validation fraud rate: 0.034996
Number of features: 1014
X_train: (413378, 1014)
X_val:   (88581, 1014)

======================================================================
TRAINING LOGISTIC REGRESSION
======================================================================
Best CV ROC-AUC: 0.844992
======================================================================
TRAINING RANDOM FOREST
======================================================================
Best CV ROC-AUC: 0.876630
======================================================================
TRAINING XGBOOST
======================================================================
Best CV ROC-AUC: 0.891390

======================================================================
VALIDATION MODEL COMPARISON
======================================================================
XGBoost                   ROC-AUC=0.916026 PR-AUC=0.591256 F1=0.438063
Random Forest             ROC-AUC=0.912991 PR-AUC=0.645182 F1=0.521094
Logistic Regression       ROC-AUC=0.869964 PR-AUC=0.485851 F1=0.422111

Best model: XGBoost
Artifacts saved to: C:\Users\Administrator\Documents\ecommerce-fraud-dw\ml\models
Phase 16 training completed.
```

---

## 10. SUCCESS CRITERIA

| Tiêu chí | Trạng thái | Chi tiết |
|----------|------------|----------|
| [✅] Logistic Regression trained | PASS | ROC-AUC=0.870, model + scaler saved |
| [✅] Random Forest trained | PASS | ROC-AUC=0.913, model saved |
| [✅] XGBoost trained | PASS | ROC-AUC=0.916 (best), model saved |
| [✅] All evaluated on validation | PASS | Full metrics recorded |
| [✅] Best model selected | PASS | XGBoost (highest ROC-AUC) |
| [✅] Artifacts saved | PASS | 6 files in ml/models/ |
| [✅] Feature columns saved | PASS | 1,014 features in JSON |

---

## 11. LIÊN HỆ

- Trước: [PHASE 15 — Fraud Data Prep](../15_fraud_detection/fraud_detection_prep.md)
- Sau: [PHASE 17 — Model Evaluation](../17_model_evaluation/model_evaluation.md)

---

## 12. EVIDENCE

| File | Mô tả |
|------|-------|
| `ml/train.py` | Training script (subset tuning, refit full) |
| `ml/models/training_results.json` | Complete metrics for all 3 models |
| `ml/models/feature_columns.json` | 1,014 feature names for serving |
| `ml/models/*.pkl` | Serialized models |

---

*Cập nhật: 2026-10-08 | Version: 2.0 | Status: PASSED ✅*