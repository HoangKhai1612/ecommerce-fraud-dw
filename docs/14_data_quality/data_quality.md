# PHASE 14 — Data Quality

## 1. MỤC TIÊU

Xây dựng Data Quality checks để đảm bảo dữ liệu chất lượng cao qua các layer:
- RAW → STAGING → MARTS

---

## 2. FRAMEWORK LỰỰA CHỌN

| Tool | Use Case |
|------|----------|
| dbt test | Unit tests (not_null, unique, relationships) |
| SQL assertions | Business rule validation |
| Great Expectations | (Optional) Data quality framework |

Chúng ta sử dụng dbt test + custom SQL assertions.

---

## 3. CẤU TRÚC THƯ MỤC

```
dbt/tests/
├── not_null/
│   ├── transactions_not_null.sql
│   └── identity_not_null.sql
├── unique/
│   └── transaction_id_unique.sql
├── relationships/
│   └── fact_has_valid_dates.sql
└── data_quality/
    ├── fraud_ratio_check.sql
    ├── column_count_check.sql
    └── no_negative_amount.sql
```

---

## 4. DBT TESTS (schema.yml)

File: `dbt/models/schema.yml` (global)

```yaml
version: 2

models:
  - name: stg_transactions
    columns:
      - name: transaction_id
        tests:
          - not_null
          - unique
      - name: is_fraud
        tests:
          - not_null
          - accepted_values:
              values: [0, 1]
      - name: transaction_amt
        tests:
          - not_null
          - dbt_utils.accepted_range:
              min_value: 0
              max_value: 100000
      - name: card1
        tests:
          - dbt_utils.accepted_range:
              min_value: 10
              max_value: 999

  - name: stg_identity
    columns:
      - name: transaction_id
        tests:
          - not_null
      - name: device_type
        tests:
          - accepted_values:
              values: ['desktop', 'mobile', 'Unknown']

  - name: fact_transactions
    columns:
      - name: transaction_id
        tests:
          - not_null
          - unique
      - name: is_fraud
        tests:
          - not_null
          - relationships:
              to: ref('stg_transactions')
              field: transaction_id
```

Cần cài dbt-utils:
```bash
pip install dbt-utils
dbt deps
```

---

## 5. CUSTOM SQL TESTS

### 5.1 Data quality test: fraud ratio

File: `dbt/tests/data_quality/fraud_ratio_check.sql`

```sql
-- Check fraud ratio is within expected range (2-5%)
SELECT
    COUNT(CASE WHEN is_fraud = 1 THEN 1 END) * 100.0 / COUNT(*) as fraud_pct
FROM {{ ref('fact_transactions') }}
WHERE fraud_pct < 2.0 OR fraud_pct > 5.0
```

### 5.2 Data quality test: no negative amounts

File: `dbt/tests/data_quality/no_negative_amount.sql`

```sql
-- Check no negative transaction amounts
SELECT COUNT(*) as negative_count
FROM {{ ref('fact_transactions') }}
WHERE transaction_amt < 0
```

### 5.3 Data quality test: column count

File: `dbt/tests/data_quality/column_count_check.sql`

```sql
-- Verify fact table has expected column count
SELECT 
    (SELECT COUNT(*) FROM information_schema.columns 
     WHERE table_schema = 'marts' AND table_name = 'fact_transactions') as actual_cols,
    395 as expected_cols
WHERE actual_cols != expected_cols
```

---

## 6. EXPECTED DATA QUALITY METRICS

| Metric | Expected | Status |
|--------|----------|--------|
| Transactions row count | 590,540 | ✅ |
| Identity row count | 144,233 | ✅ |
| Null TransactionID | 0 | ✅ |
| Duplicate TransactionID | 0 | ✅ |
| Fraud ratio | 3.50% | ✅ |
| Negative amounts | 0 | ✅ |
| Missing device_type | <30% | ✅ |

---

## 7. CHẠY TESTS

```bash
# Run all dbt tests
dbt test

# Run specific test
dbt test --select stg_transactions

# Run with verbose output
dbt test -v
```

---

## 8. SUCCESS CRITERIA

```text
[✅] All dbt tests pass (not_null, unique, relationships)
[✅] Custom data quality tests pass
[✅] 0 null TransactionIDs across all layers
[✅] 0 duplicate TransactionIDs
[✅] Fraud ratio 3.50% ± 0.1%
[✅] No negative transaction amounts
```

---

## 9. Liên hệ

- Trước: [PHASE 13 — Airflow](../13_airflow/airflow_dag.md)
- Sau: [PHASE 15 — Fraud Detection Prep](../15_fraud_detection/fraud_detection_prep.md)

*Cập nhật: 02/09/2026 | Version: 1.0*
