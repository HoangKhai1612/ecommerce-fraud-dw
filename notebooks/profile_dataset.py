import sys
sys.stdout.reconfigure(encoding='utf-8')
import pandas as pd

# Read train_transaction
df_t = pd.read_csv('data/raw/train_transaction.csv', nrows=10000)
print('=== TRAIN_TRANSACTION (first 10K rows) ===')
print(f'Shape: {df_t.shape}')
print(f'Columns: {len(df_t.columns)}')
print(f'Dtypes value counts:')
print(df_t.dtypes.value_counts())

# Read train_identity
df_i = pd.read_csv('data/raw/train_identity.csv', nrows=10000)
print()
print('=== TRAIN_IDENTITY (first 10K rows) ===')
print(f'Shape: {df_i.shape}')
print(f'Columns: {len(df_i.columns)}')

# Read full to count
df_full = pd.read_csv('data/raw/train_transaction.csv', usecols=['isFraud'])
print()
print('=== FULL TRANSACTION STATS ===')
print(f'Total rows: {len(df_full)}')
fraud_count = df_full['isFraud'].sum()
non_fraud_count = len(df_full) - fraud_count
print(f'Fraud count: {fraud_count}')
print(f'Non-Fraud count: {non_fraud_count}')
print(f'Fraud ratio: {df_full["isFraud"].mean() * 100:.2f}%')

# Identity count
df_id_full = pd.read_csv('data/raw/train_identity.csv')
print(f'Identity rows: {len(df_id_full)}')

# Check missing values in transaction (sample)
print()
print('=== MISSING VALUES (train_transaction, 10K sample) ===')
missing = df_t.isnull().sum()
missing_pct = (missing / len(df_t) * 100).round(2)
missing_df = pd.DataFrame({'count': missing, 'pct': missing_pct})
missing_df = missing_df[missing_df['count'] > 0].sort_values('count', ascending=False)
print(f'Total columns with missing: {len(missing_df)}')
print(f'Top 10 columns with most missing:')
print(missing_df.head(10))

# Check missing values in identity
print()
print('=== MISSING VALUES (train_identity, 10K sample) ===')
missing_i = df_i.isnull().sum()
missing_i_pct = (missing_i / len(df_i) * 100).round(2)
missing_i_df = pd.DataFrame({'count': missing_i, 'pct': missing_i_pct})
missing_i_df = missing_i_df[missing_i_df['count'] > 0].sort_values('count', ascending=False)
print(f'Total columns with missing: {len(missing_i_df)}')
print(f'Top 10:')
print(missing_i_df.head(10))

# ProductCD distribution
print()
print('=== PRODUCTCD DISTRIBUTION ===')
prod_dist = df_t.groupby('ProductCD').agg(
    total=('isFraud', 'count'),
    fraud=('isFraud', 'sum')
).reset_index()
prod_dist['fraud_rate'] = (prod_dist['fraud'] / prod_dist['total'] * 100).round(2)
print(prod_dist)

# DeviceType from identity
print()
print('=== DEVICETYPE DISTRIBUTION (identity) ===')
dev_dist = df_i.groupby('DeviceType').agg(
    total=('TransactionID', 'count'),
).reset_index()
print(dev_dist)

# TransactionAmt stats
print()
print('=== TRANSACTION AMT STATS ===')
print(df_t['TransactionAmt'].describe())

# Test files
import os
print()
print('=== TEST FILES ===')
for f in ['test_transaction.csv', 'test_identity.csv', 'sample_submission.csv']:
    path = f'data/raw/{f}'
    if os.path.exists(path):
        size_mb = os.path.getsize(path) / 1024 / 1024
        print(f'{f}: {size_mb:.1f} MB')
        if 'transaction' in f:
            df_test = pd.read_csv(path, nrows=5)
            print(f'  Columns: {len(df_test.columns)}')
    else:
        print(f'{f}: NOT FOUND')

# List all columns in transaction
print()
print('=== TRANSACTION COLUMNS (first 20 + last 10) ===')
cols = list(df_t.columns)
for c in cols[:20]:
    print(f'  {c}: {df_t[c].dtype}')
print('  ...')
for c in cols[-10:]:
    print(f'  {c}: {df_t[c].dtype}')
