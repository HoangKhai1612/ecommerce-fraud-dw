import sys
sys.stdout.reconfigure(encoding='utf-8')
import pandas as pd
import numpy as np

# Read transaction sample (đủ lớn để đại diện)
df_t = pd.read_csv('data/raw/train_transaction.csv', nrows=50000)
df_i = pd.read_csv('data/raw/train_identity.csv', nrows=50000)

print('=== EDA: THOROUGH ANALYSIS ===')

# 1. TransactionAmt distribution
print('\n--- TransactionAmt Stats ---')
print(df_t['TransactionAmt'].describe())
# Outliers using IQR
q1 = df_t['TransactionAmt'].quantile(0.25)
q3 = df_t['TransactionAmt'].quantile(0.75)
iqr = q3 - q1
lower = q1 - 1.5 * iqr
upper = q3 + 1.5 * iqr
outliers = df_t[(df_t['TransactionAmt'] < lower) | (df_t['TransactionAmt'] > upper)]
print(f'Outliers (IQR method): {len(outliers)} ({len(outliers)/len(df_t)*100:.1f}%)')
print(f'Outlier threshold upper: ${upper:.2f}')

# 2. ProductCD chi tiết
print('\n--- ProductCD Distribution ---')
prod = df_t.groupby('ProductCD').agg(
    total=('TransactionID', 'count'),
    fraud=('isFraud', 'sum'),
    avg_amt=('TransactionAmt', 'mean'),
    median_amt=('TransactionAmt', 'median')
).reset_index()
prod['fraud_rate'] = (prod['fraud'] / prod['total'] * 100).round(2)
print(prod.to_string())

# 3. DeviceType chi tiết
print('\n--- DeviceType Distribution ---')
dev = df_i.groupby('DeviceType').agg(
    total=('TransactionID', 'count'),
).reset_index()
print(dev.to_string())

# 4. Missing value per column group
print('\n--- Missing by Column Group ---')
v_cols = [c for c in df_t.columns if c.startswith('V')]
d_cols = [c for c in df_t.columns if c.startswith('D') and not c.startswith('DeviceInfo')]
c_cols = [c for c in df_t.columns if c.startswith('C')]
m_cols = [c for c in df_t.columns if c.startswith('M')]

for name, cols in [('C1-C14', c_cols), ('D1-D15', d_cols), ('M1-M9', m_cols), ('V1-V339', v_cols)]:
    avg_missing = df_t[cols].isnull().sum().mean()
    pct_missing_cols = (df_t[cols].isnull().sum() > 0).sum() / len(cols) * 100
    print(f'{name}: {len(cols)} cols, avg missing {avg_missing:.1f} records, {pct_missing_cols:.0f}% have missing')

# 5. card4 distribution
print('\n--- Card4 Distribution ---')
print(df_t['card4'].value_counts())

# 6. card6 distribution
print('\n--- Card6 Distribution ---')
print(df_t['card6'].value_counts())

# 7. P_emaildomain top values
print('\n--- P_emaildomain Top 10 ---')
print(df_t['P_emaildomain'].value_counts().head(10))

# 8. Fraud rate by DeviceType (from identity join)
print('\n--- Fraud Rate by DeviceType (join identity) ---')
merged = df_t.merge(df_i[['TransactionID', 'DeviceType']], on='TransactionID', how='left')
merged['DeviceType'] = merged['DeviceType'].fillna('Unknown')
dev_fraud = merged.groupby('DeviceType').agg(
    total=('isFraud', 'count'),
    fraud=('isFraud', 'sum')
).reset_index()
dev_fraud['fraud_rate'] = (dev_fraud['fraud'] / dev_fraud['total'] * 100).round(2)
print(dev_fraud.to_string())

# 9. Fraud rate by TransactionAmt bins
print('\n--- Fraud Rate by Amount Bins ---')
df_t['amt_bin'] = pd.cut(df_t['TransactionAmt'], bins=10)
amt_fraud = df_t.groupby('amt_bin', observed=True).agg(
    total=('isFraud', 'count'),
    fraud=('isFraud', 'sum')
).reset_index()
amt_fraud['fraud_rate'] = (amt_fraud['fraud'] / amt_fraud['total'] * 100).round(2)
print(amt_fraud.to_string())

# 10. Correlation of top features with isFraud
print('\n--- Top 10 Correlations with isFraud ---')
numeric_cols = df_t.select_dtypes(include=[np.number]).columns
correlations = df_t[numeric_cols].corr()['isFraud'].abs().sort_values(ascending=False)
print(correlations.head(15))
