# PHASE 15 — Fraud Detection Data Preparation

## 1. MỤC TIÊU

Chuẩn bị dữ liệu cho Machine Learning từ Data Warehouse:
- Load dữ liệu từ `marts.fact_transactions` (đã có identity join từ Phase 12)
- Feature engineering xác định (deterministic)
- Handle missing values & encode categorical features
- Train/Validation/Test split stratified 70/15/15
- Lưu Parquet + metadata JSON

---

## 2. CẤU TRÚC THƯ MỤC THỰC TẾ

```
ml/
├── config.py                      # Config (DB URL, split ratios, paths)
├── features/
│   ├── __init__.py
│   ├── engineering.py             # Deterministic feature engineering
│   ├── preprocessing.py           # Preprocessing pipeline (fit on TRAIN only)
│   ├── prepare.py                 # Main pipeline orchestrator
│   └── encoding.py                # (reserved)
├── data/
│   ├── train.parquet              # 413,378 × 1,015 (1014 features + target)
│   ├── val.parquet                # 88,581 × 1,015
│   ├── test.parquet               # 88,581 × 1,015
│   └── feature_metadata.json      # Auto-generated metadata
├── __init__.py
└── notebooks/
    └── eda.ipynb                  # EDA exploration
```

---

## 3. THUẬT TOÁN & PIPELINE

### 3.1 Load Data (`prepare.py:load_data()`)

```python
# Query đơn giản từ marts.fact_transactions
# (các cột identity đã được join ở Phase 12 dbt fact_transactions.sql)
SELECT * FROM marts.fact_transactions
```

- 590,540 rows, 438 columns (bao gồm sẵn device_type, device_info, id_01..id_38)
- Grain: 1 row = 1 transaction (transaction_id unique)

### 3.2 Feature Engineering (`features/engineering.py`)

| Function | Mô tả | Output features |
|----------|-------|-----------------|
| `add_time_features` | Từ `transaction_dt` (seconds) → hour, day_index, dayofweek, is_weekend | `transaction_hour`, `transaction_day_index`, `transaction_dayofweek`, `is_weekend` |
| `add_missing_indicators` | Tạo cột `_missing` cho id_01..id_38, device_info, p_emaildomain, r_emaildomain | 41 `_missing` columns (int8) |
| `add_amount_bin` | Bin `transaction_amt` theo 9 bins | `transaction_amt_bin` (category) |
| `add_all_engineered_features` | Orchestrator | +46 features |

**Quan trọng:** Frequency encoding (`device_type_freq`, `product_cd_freq`, `card*_freq`) được tách sang `preprocessing.py` để fit chỉ trên TRAIN.

### 3.3 Preprocessing Pipeline (`features/preprocessing.py`)

```python
# ColumnTransformer với 3 nhánh:
1. Numeric:  SimpleImputer(median) → StandardScaler
2. Categorical: SimpleImputer(most_frequent) → OneHotEncoder(handle_unknown='ignore')
3. Identity (id_01..id_38): SimpleImputer(constant=0) → StandardScaler
```

**Key principle:** `fit_transform_datasets(train_X, val_X, test_X)` — **FIT chỉ trên TRAIN**, TRANSFORM cả 3 tập.

### 3.4 Split (`prepare.py:split_data()`)

```python
# Stratified 70/15/15
train_df, temp_df = train_test_split(df, test_size=0.30, stratify=df['is_fraud'], random_state=42)
val_df, test_df = train_test_split(temp_df, test_size=0.5, stratify=temp_df['is_fraud'], random_state=42)
```

---

## 4. KẾT QUẢ THỰC TẾ (ACTUAL RESULTS)

### 4.1 Load & Validation
```
Loaded rows: 590,540
Loaded columns: 438
Base dataset validation:
  Rows: 590,540
  Distinct IDs: 590,540
  Null IDs: 0
  Duplicate IDs: 0
```

### 4.2 Split Verification
| Split | Rows | % Total | Fraud Count | Fraud Rate |
|-------|------|---------|-------------|------------|
| Train | 413,378 | 70.00% | 14,464 | 3.4990% |
| Val | 88,581 | 15.00% | 3,100 | 3.4996% |
| Test | 88,581 | 15.00% | 3,099 | 3.4985% |
| **Total** | **590,540** | **100%** | **20,663** | **3.4990%** |

**Baseline Phase 14:** 20,663 / 590,540 = 3.4990% ✅

### 4.3 Overlap Check (từ code validation)
```
TRAIN ∩ VAL = 0 ✅
TRAIN ∩ TEST = 0 ✅
VAL ∩ TEST = 0 ✅
Total unique IDs = 590,540 ✅
```

### 4.4 Feature Matrix
| Metric | Train | Val | Test |
|--------|-------|-----|------|
| Rows | 413,378 | 88,581 | 88,581 |
| Features | 1,014 | 1,014 | 1,014 |
| Target (is_fraud) | 1 | 1 | 1 |
| Total columns | 1,015 | 1,015 | 1,015 |
| NaN | 0 | 0 | 0 |
| Dtypes | float32(1014) + int8(1) | same | same |

**Feature breakdown (từ feature_metadata.json):**
- `num__` (numeric): 390+ raw + 9 freq + 46 engineered + 38 id missing = ~480
- `cat__` (one-hot): card4(5), card6(5), device_info(28+), m1-m9(18+), id_12..id_38(100+), p/r_emaildomain(40+), product_cd(5), transaction_amt_bin(8), device_type(3) = ~534
- **Total: 1,014 features**

---

## 5. FILES ĐẦU RA

### 5.1 Parquet Files
```
ml/data/train.parquet    (413,378 × 1,015)
ml/data/val.parquet      (88,581 × 1,015)
ml/data/test.parquet     (88,581 × 1,015)
```
Tất cả: `float32` features + `int8` target, **NaN = 0**

### 5.2 Metadata (auto-generated: `feature_metadata.json`)
```json
{
  "phase": 15,
  "target": "is_fraud",
  "id_column": "transaction_id",
  "random_state": 42,
  "split": {"train": 0.7, "validation": 0.15, "test": 0.15},
  "rows": {"train": 413378, "validation": 88581, "test": 88581},
  "features": {
    "count": 1014,
    "names": ["num__addr1", "num__addr2", ..., "cat__transaction_amt_bin_5K-10K"]
  }
}
```

---

## 6. CHẠY PIPELINE

```powershell
.venv\Scripts\Activate.ps1
python -m ml.features.prepare
```

**Output thực tế:**
```
======================================================================
PHASE 15 - FRAUD DETECTION DATA PREPARATION
======================================================================

[1/7] Loading data...
Loaded rows: 590,540
Loaded columns: 438

[2/7] Validating base dataset...
Base dataset validation
-----------------------
Rows:              590,540
Distinct IDs:      590,540
Null IDs:          0
Duplicate IDs:     0

[3/7] Splitting data...
Split validation
----------------
Train: 413,378 (70.00%) fraud=3.4990%
Val:   88,581 (15.00%) fraud=3.4996%
Test:  88,581 (15.00%) fraud=3.4985%

[4/7] Engineering features...

[5/7] Separating features and target...
Raw ML features before preprocessing: 491

[6/7] Fitting preprocessing on TRAIN only...
Processed feature count: 1,014

[7/7] Saving processed datasets...

======================================================================
PHASE 15 COMPLETED
======================================================================
Train: 413,378
Validation: 88,581
Test: 88,581
Features: 1,014
Saved to: ml\data
```

---

## 7. CHECKLIST PHASE 15

| Tiêu chí | Trạng thái | Chi tiết |
|----------|------------|----------|
| **A. Grain đúng** | ✅ | 590,540 rows = 590,540 distinct transaction_id |
| **B. Split đúng** | ✅ | 413,378 / 88,581 / 88,581 (70/15/15) |
| **C. Fraud rate giữ** | ✅ | 3.4990% baseline → Train 3.4990%, Val 3.4996%, Test 3.4985% |
| **D. Không overlap** | ✅ | Code validation: TRAIN∩VAL=0, TRAIN∩TEST=0, VAL∩TEST=0 |
| **E. NaN = 0** | ✅ | Preprocessing impute + validation: 0 NaN all splits |
| **F. Không object/string** | ✅ | Tất cả features float32, target int8 |
| **G. Cùng feature count** | ✅ | 1,014 features train/val/test |
| **H. Preprocessor fit TRAIN only** | ✅ | `fit_transform_datasets()` fit trên train_X, transform val_X/test_X |

---

## 8. SAI LẪM PHỔ BIỂN ĐÃ TRÁNH

| Sai lầm | Cách xử lý đúng |
|---------|-----------------|
| Frequency encoding fit trên toàn bộ data | ❌ Fit trên TRAIN → transform TRAIN/VAL/TEST |
| OneHotEncoder không handle unknown | ❌ `handle_unknown='ignore'` |
| Join identity tạo duplicate columns | ❌ marts.fact_transactions đã có identity từ Phase 12 |
| Fill missing trước split | ❌ Imputer fit trên TRAIN only |
| transaction_id giữ làm feature | ❌ Drop trước preprocessing |

---

## 9. LIÊN HỆ

- Trước: [PHASE 14 — Data Quality](../14_data_quality/data_quality.md)
- Sau: [PHASE 16 — Machine Learning](../16_machine_learning/machine_learning.md)

---

## 10. EVIDENCE

| File | Mô tả |
|------|-------|
| `ml/features/prepare.py` | Main orchestrator |
| `ml/features/engineering.py` | Deterministic features |
| `ml/features/preprocessing.py` | ColumnTransformer pipeline |
| `ml/config.py` | Configuration |
| `ml/data/train.parquet` | Train split |
| `ml/data/val.parquet` | Validation split |
| `ml/data/test.parquet` | Test split |
| `ml/data/feature_metadata.json` | Feature metadata |

---

*Cập nhật: 2026-10-08 | Version: 2.0 | Status: PASSED ✅*