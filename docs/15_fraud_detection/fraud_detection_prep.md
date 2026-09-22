# PHASE 15 — Fraud Detection Data Preparation

## 1. MỤC TIÊU

Chuẩn bị dữ liệu cho ML:
- Join transactions + identity
- Feature engineering
- Handle missing values
- Encode categorical features
- Train/test split (stratified, 70/15/15)

---

## 2. CẤU TRÚC THƯ MỤC

```
ml/
├── data/                     # Generated features
├── features/
│   ├── __init__.py
│   ├── prepare.py           # Main data prep
│   └── features.py          # Feature engineering functions
├── __init__.py
├── config.py                # Configuration
└── notebooks/
    └── eda.ipynb            # EDA exploration
```

---

## 3. FEATURE ENGINEERING

### 3.1 Các features mới đề xuất

1. **Transaction count per device** — số giao dịch trên mỗi thiết bị
2. **Email domain frequency** — tần suất email domain
3. **Card frequency** — tần suất card1-card6
4. **Transaction amount bin** — phân loại transaction_amt thành bins
5. **Time-based features** — hour, day_of_week, is_weekend
6. **Missing indicator** — đánh dấu cột có missing values

### 3.2 Code feature engineering

File: `ml/features/features.py`

```python
"""
Feature engineering functions for fraud detection.
Phase 15: Data Preparation & Feature Engineering
"""

import pandas as pd
import numpy as np

def add_time_features(df):
    """Thêm features thời gian từ TransactionDT."""
    # TransactionDT is seconds since 1970-01-01
    df['transaction_dt'] = pd.to_datetime(df['transaction_dt'], unit='s')
    df['transaction_hour'] = df['transaction_dt'].dt.hour
    df['transaction_dayofweek'] = df['transaction_dt'].dt.dayofweek
    df['is_weekend'] = df['transaction_dayofweek'].isin([5, 6]).astype(int)
    return df

def add_missing_indicators(df):
    """Thêm indicator cho missing values."""
    # Columns with high missing rates
    id_cols = [c for c in df.columns if c.startswith('id_')]
    for col in id_cols:
        if df[col].isna().any():
            df[f'{col}_missing'] = df[col].isna().astype(int)
    
    # Device info missing
    df['device_info_missing'] = (df['device_info'].isna() | (df['device_info'] == '')).astype(int)
    return df

def add_frequency_features(df):
    """Thêm features tần suất xuất hiện."""
    # Device type frequency
    device_counts = df['device_type'].value_counts(normalize=True)
    df['device_type_freq'] = df['device_type'].map(device_counts)
    
    # Product CD frequency
    product_counts = df['product_cd'].value_counts(normalize=True)
    df['product_cd_freq'] = df['product_cd'].map(product_counts)
    
    # Email domain frequency
    email_counts = df['p_emaildomain'].value_counts(normalize=True)
    df['p_emaildomain_freq'] = df['p_emaildomain'].map(email_counts).fillna(0)
    
    return df

def add_binned_amount(df):
    """Thêm binned transaction amount."""
    bins = [0, 50, 100, 200, 500, 1000, 5000, 10000, np.inf]
    labels = ['0-50', '50-100', '100-200', '200-500', '500-1K', '1K-5K', '5K-10K', '10K+']
    df['transaction_amt_bin'] = pd.cut(df['transaction_amt'], bins=bins, labels=labels)
    return df

def encode_categoricals(df):
    """Encode categorical features."""
    # One-hot encoding cho categorical
    cat_cols = ['product_cd', 'card4', 'card6', 'transaction_amt_bin']
    df = pd.get_dummies(df, columns=cat_cols, prefix=cat_cols)
    return df

def fill_missing_values(df):
    """Fill missing values."""
    # Numeric columns: fill với median
    numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns
    for col in numeric_cols:
        if df[col].isna().any():
            df[col] = df[col].fillna(df[col].median())
    
    # Categorical columns: fill với mode hoặc 'Unknown'
    cat_cols = df.select_dtypes(include=['object']).columns
    for col in cat_cols:
        if df[col].isna().any():
            df[col] = df[col].fillna('Unknown')
    
    return df

def prepare_features(df):
    """Main function: apply all feature engineering steps."""
    df = add_time_features(df)
    df = add_missing_indicators(df)
    df = add_frequency_features(df)
    df = add_binned_amount(df)
    df = encode_categoricals(df)
    df = fill_missing_values(df)
    return df
```

---

## 4. TRAIN/TEST SPLIT

File: `ml/features/prepare.py`

```python
"""
Data preparation: load data, engineer features, split.
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sqlalchemy import create_engine, text
import sys
import os

sys.path.append(os.path.dirname(__file__))
from features import prepare_features

DB_URL = "postgresql://postgres:postgres@localhost:5432/ecommerce_fraud_dw"
RANDOM_STATE = 42

def load_data():
    """Load data from staging layer."""
    engine = create_engine(DB_URL)
    
    query = """
    SELECT t.*, i.device_type, i.device_info,
           i.id_01, i.id_02, i.id_03, i.id_04, i.id_05, i.id_06,
           i.id_07, i.id_08, i.id_09, i.id_10, i.id_11,
           i.id_12, i.id_13, i.id_14, i.id_15, i.id_16, i.id_17,
           i.id_18, i.id_19, i.id_20, i.id_21, i.id_22, i.id_23,
           i.id_24, i.id_25, i.id_26, i.id_27, i.id_28, i.id_29,
           i.id_30, i.id_31, i.id_32, i.id_33, i.id_34, i.id_35,
           i.id_36, i.id_37, i.id_38
    FROM marts.fact_transactions t
    LEFT JOIN marts.dim_device d ON t.device_type = d.device_type
    """
    
    df = pd.read_sql(query, engine)
    engine.dispose()
    return df


def split_data(df, test_size=0.15, val_size=0.15):
    """
    Stratified split: 70% train, 15% validation, 15% test.
    """
    # First split: train vs (val + test)
    train_df, temp_df = train_test_split(
        df, test_size=(val_size + test_size), 
        stratify=df['is_fraud'], random_state=RANDOM_STATE
    )
    
    # Second split: val vs test
    val_df, test_df = train_test_split(
        temp_df, test_size=test_size / (val_size + test_size),
        stratify=temp_df['is_fraud'], random_state=RANDOM_STATE
    )
    
    return train_df, val_df, test_df


def main():
    print("Loading data from staging layer...")
    df = load_data()
    print(f"Total rows: {len(df)}")
    print(f"Columns: {len(df.columns)}")
    
    print("Engineering features...")
    df = prepare_features(df)
    
    print("Splitting data (70/15/15 stratified)...")
    train_df, val_df, test_df = split_data(df)
    
    print(f"Train: {len(train_df)} ({train_df['is_fraud'].mean()*100:.2f}% fraud)")
    print(f"Val:   {len(val_df)} ({val_df['is_fraud'].mean()*100:.2f}% fraud)")
    print(f"Test:  {len(test_df)} ({test_df['is_fraud'].mean()*100:.2f}% fraud)")
    
    # Save splits
    os.makedirs('ml/data', exist_ok=True)
    train_df.to_parquet('ml/data/train.parquet', index=False)
    val_df.to_parquet('ml/data/val.parquet', index=False)
    test_df.to_parquet('ml/data/test.parquet', index=False)
    
    # Save feature list
    feature_cols = [c for c in df.columns if c not in ['is_fraud', 'transaction_id', 'transaction_dt']]
    with open('ml/data/features.txt', 'w') as f:
        for col in feature_cols:
            f.write(col + '\n')
    
    print(f"Features: {len(feature_cols)}")
    print("Data saved to ml/data/")
    return train_df, val_df, test_df


if __name__ == '__main__':
    main()
```

---

## 5. CHẠY

```bash
.venv\Scripts\Activate.ps1
cd ml
python features/prepare.py
```

---

## 6. EXPECTED OUTPUT

```text
Loading data from staging layer...
Total rows: 590,540
Columns: 415
Engineering features...
Splitting data (70/15/15 stratified)...
Train: 413,378 (3.49% fraud)
Val:   88,581  (3.50% fraud)
Test:  88,581  (3.51% fraud)
Features: 412
Data saved to ml/data/
```

---

## 7. Liên hệ

- Trước: [PHASE 14 — Data Quality](../14_data_quality/data_quality.md)
- Sau: [PHASE 16 — Machine Learning](../16_machine_learning/machine_learning.md)

*Cập nhật: 02/09/2026 | Version: 1.0*
