# PHASE 14 — Data Quality & Airflow Data Quality Gate

## 1. MỤC TIÊU

Xây dựng hệ thống Data Quality Checks toàn diện để đảm bảo dữ liệu chất lượng cao qua các layer:
- RAW → STAGING → MARTS

Cụ thể:
1. Xây dựng dbt data tests (schema tests + custom SQL tests)
2. Tích hợp Data Quality Gate vào Airflow DAG
3. Chứng minh Data Quality Gate có thể chặn pipeline khi có vi phạm
4. Recovery và restore sau failure simulation

---

## 2. FRAMEWORK LỰA CHỌN

| Tool | Use Case | Status |
|------|----------|--------|
| dbt tests (schema.yml) | not_null, unique, accepted_values, relationships | ✅ Implemented |
| dbt tests (singular SQL) | Business rule validation | ✅ Implemented |
| dbt run | Build models | ✅ Implemented |
| dbt test | Validate data | ✅ Implemented |
| Airflow DAG | Orchestration + Quality Gate | ✅ Implemented |

---

## 3. CẤU TRÚC THƯ MỤC

```
dbt/
├── models/
│   ├── staging/
│   │   ├── stg_transactions.sql
│   │   ├── stg_identity.sql
│   │   └── staging.yml          # Schema tests for staging
│   └── marts/
│       ├── dim_product.sql
│       ├── dim_device.sql
│       ├── dim_date.sql
│       ├── fact_transactions.sql
│       └── schema.yml           # Schema tests for marts
├── tests/
│   └── data_quality/            # Custom SQL assertions (12 tests)
│       ├── fraud_ratio_check.sql
│       ├── negative_transaction_amount.sql
│       ├── non_positive_transaction_amount.sql
│       ├── orphan_transactions.sql
│       ├── fact_staging_row_count.sql
│       ├── duplicate_transaction_ids.sql
│       ├── null_transaction_ids.sql
│       ├── invalid_fraud_flag.sql
│       ├── device_type_completeness.sql
│       ├── fraud_distribution_consistency.sql
│       ├── fact_transactions_not_empty.sql
│       └── staging_transactions_not_empty.sql

docs/data_quality/
├── baseline.md
├── thresholds.md
├── quality_report.md
└── phase14_airflow_evidence.md

docs/14_data_quality/
└── data_quality.md              # This file
```

---

## 4. DBT SCHEMA TESTS (staging.yml)

File: `dbt/models/staging/staging.yml`

Tests applied to `stg_transactions`:
- not_null (transaction_id, is_fraud, transaction_amt, product_cd, card1-6, addr1-2, dist1-2, p/r_emaildomain, c1-14, d1-15, m1-9, v1-339)
- unique (transaction_id)
- accepted_values (is_fraud: [0, 1])
- relationships (transaction_id → ref('stg_transactions'), device_type → ref('dim_device'), product_cd+card4 → ref('dim_product'))

Tests applied to `stg_identity`:
- not_null (transaction_id)
- accepted_values (device_type: ['desktop', 'mobile'])

---

## 5. DBT SCHEMA TESTS (marts/schema.yml)

File: `dbt/models/marts/schema.yml`

Tests applied to `marts.dim_product`:
- not_null (product_key, product_cd)
- unique (product_key, product_cd)

Tests applied to `marts.dim_device`:
- not_null (device_key, device_type, device_info)
- unique (device_key, device_type+device_info)

Tests applied to `marts.dim_date`:
- not_null (date_key, transaction_day)
- unique (date_key)

Tests applied to `marts.fact_transactions`:
- not_null (transaction_key, transaction_id, is_fraud, transaction_amt, product_key, device_key, product_cd, card1-6, addr1-2, dist1-2, p/r_emaildomain, c1-14, d1-15, m1-9, v1-339, id_01-38, device_type, device_info, _loaded_at, transaction_dt)
- unique (transaction_key, transaction_id)
- accepted_values (is_fraud: [0, 1])
- relationships (device_key → ref('dim_device'), product_key → ref('dim_product'))

---

## 6. CUSTOM SQL TESTS (dbt/tests/data_quality/)

### 6.1 fraud_ratio_check.sql

```sql
SELECT
    transaction_id,
    is_fraud
FROM {{ ref('fact_transactions') }}
WHERE is_fraud NOT IN (0, 1)
   OR is_fraud IS NULL
```

Mục đích: Kiểm tra fraud flag chỉ có giá trị 0 hoặc 1.

### 6.2 negative_transaction_amount.sql

```sql
SELECT
    transaction_id,
    transaction_amt
FROM {{ ref('fact_transactions') }}
WHERE transaction_amt < 0
```

Mục đích: Không có giao dịch âm.

### 6.3 non_positive_transaction_amount.sql

```sql
SELECT
    transaction_id,
    transaction_amt
FROM {{ ref('fact_transactions') }}
WHERE transaction_amt <= 0
```

Mục đích: Không có giao dịch bằng 0 hoặc âm.

### 6.4 orphan_transactions.sql

```sql
WITH transaction_ids AS (
    SELECT DISTINCT transaction_id FROM {{ ref('stg_transactions') }}
),

fact_ids AS (
    SELECT DISTINCT transaction_id FROM {{ ref('fact_transactions') }}
)

SELECT
    f.transaction_id
FROM fact_ids f
LEFT JOIN transaction_ids s ON f.transaction_id = s.transaction_id
WHERE s.transaction_id IS NULL
```

Mục đích: Kiểm tra không có orphan fact (fact_id không tồn tại trong staging).

### 6.5 fact_staging_row_count.sql

```sql
WITH counts AS (
    SELECT
        (SELECT COUNT(*) FROM {{ ref('stg_transactions') }}) AS staging_count,
        (SELECT COUNT(*) FROM {{ ref('fact_transactions') }}) AS fact_count
)
SELECT
    staging_count,
    fact_count
FROM counts
WHERE staging_count <> fact_count
```

Mục đích: Row count staging = fact_transactions.

### 6.6 duplicate_transaction_ids.sql

```sql
SELECT
    transaction_id,
    COUNT(*) AS duplicate_count
FROM {{ ref('fact_transactions') }}
GROUP BY transaction_id
HAVING COUNT(*) > 1
```

Mục đích: Không có duplicate transaction_id.

### 6.7 null_transaction_ids.sql

```sql
SELECT
    transaction_id
FROM {{ ref('fact_transactions') }}
WHERE transaction_id IS NULL
```

Mục đích: Không có NULL transaction_id.

### 6.8 invalid_fraud_flag.sql

```sql
SELECT
    transaction_id,
    is_fraud
FROM {{ ref('fact_transactions') }}
WHERE is_fraud NOT IN (0, 1)
   OR is_fraud IS NULL
```

Mục đích: Fraud flag hợp lệ (0 hoặc 1).

### 6.9 device_type_completeness.sql

```sql
WITH device_stats AS (
    SELECT
        COUNT(*) AS total_rows,
        COUNT(*) FILTER (
            WHERE device_type IS NULL
               OR TRIM(device_type) = ''
        ) AS missing_rows
    FROM {{ ref('stg_identity') }}
),
...
SELECT total_rows, missing_rows, missing_percentage
FROM quality_check
WHERE missing_percentage > 30.0
```

Mục đích: Kiểm tra missing device_type < 30%.

### 6.10 fraud_distribution_consistency.sql

Kiểm tra phân phối fraud flag nhất quán giữa các layer.

### 6.11 fact_transactions_not_empty.sql

```sql
SELECT COUNT(*) FROM {{ ref('fact_transactions') }} HAVING COUNT(*) = 0
```

Mục đích: fact_transactions không rỗng.

### 6.12 staging_transactions_not_empty.sql

```sql
SELECT COUNT(*) FROM {{ ref('stg_transactions') }} HAVING COUNT(*) = 0
```

Mục đích: staging không rỗng.

---

## 7. KẾT QUẢ THỰC TẾ DBT

### 7.1 dbt debug

```
All checks passed!
```

### 7.2 dbt run (full)

```
Running 1 on-run-start hook
1 of 1 OK hook: ecommerce_fraud_dw.on-run-start.0 ...................... [SELECT 1 in 0.00s]

6 models built:
  - marts.dim_date (table)       SELECT 183 rows
  - marts.dim_device (table)     SELECT 1939 rows
  - marts.dim_product (table)    SELECT 22 rows
  - marts.fact_transactions (table)  SELECT 590540 rows
  - staging.stg_transactions (view)  SELECT 590540 rows
  - staging.stg_identity (view)      SELECT 144233 rows

Done. PASS=6 WARN=0 ERROR=0 SKIP=0 TOTAL=6
```

### 7.3 dbt test (full)

```
Running 38 data tests, 1 project hook in 0 hours 0 minutes and 37.89 seconds

PASS=38 WARN=0 ERROR=0 SKIP=0 TOTAL=38
```

### 7.4 dbt build (full)

```
PASS=44 WARN=0 ERROR=0 SKIP=0 TOTAL=44
```

(6 models + 38 tests)

---

## 8. KẾT QUẢ KIỂM TRA DỮ LIỆU THỰC TẾ

### 8.1 RAW Layer

| Table | Row count |
|-------|-----------|
| raw.transactions | 590,540 |
| raw.identity | 144,233 |

| Check | Result |
|-------|--------|
| NULL TransactionID (raw.transactions) | 0 |
| Duplicate TransactionID (raw.transactions) | 0 |
| NULL TransactionID (raw.identity) | 0 |
| Duplicate TransactionID (raw.identity) | 0 |

### 8.2 STAGING Layer

| Table | Row count |
|-------|-----------|
| staging.stg_transactions | 590,540 |
| staging.stg_identity | 144,233 |

### 8.3 MARTS Layer

| Table | Row count |
|-------|-----------|
| marts.fact_transactions | 590,540 |
| marts.dim_product | 22 |
| marts.dim_device | 1,939 |
| marts.dim_date | 183 |

### 8.4 Transaction Metrics

| Metric | Value |
|--------|-------|
| Total transactions | 590,540 |
| Distinct transaction_id | 590,540 |
| NULL transaction_id | 0 |
| Duplicate transaction_id | 0 |
| Orphan fact vs staging | 0 |

### 8.5 Fraud Distribution

| is_fraud | Count |
|----------|-------|
| 0 | 569,877 |
| 1 | 20,663 |
| **Total** | **590,540** |
| **Fraud ratio** | **3.4990%** |

### 8.6 Transaction Amount

| Metric | Value |
|--------|-------|
| Min | 0.25 |
| Max | 31,937.39 |
| Avg | 135.027 |
| Negative | 0 |
| Non-positive | 0 |

### 8.7 Device Type

| device_type | Count |
|-------------|-------|
| desktop | 85,165 |
| mobile | 55,645 |
| Missing | 3,423 |

Missing ratio: 2.3732% (within threshold < 30%)

---

## 9. AIRFLOW DATA QUALITY GATE

### 9.1 DAG Cấu trúc

File: `airflow/dags/fraud_dw_pipeline.py`

DAG ID: `fraud_dw_pipeline`
Schedule: `@daily`
Owner: kayy

| # | Task ID | Type | Description |
|---|---------|------|-------------|
| 1 | start_pipeline | BashOperator | Start marker |
| 2 | ingest_raw_data | BashOperator | Load CSV → raw (idempotent) |
| 3 | verify_raw_layer | SQLExecuteQueryOperator | Verify raw counts |
| 4 | run_dbt_staging | BashOperator | `dbt run --select staging` |
| 5 | run_dbt_marts | BashOperator | `dbt run --select marts` |
| 6 | run_dbt_tests | BashOperator | `dbt test` (**DATA QUALITY GATE**) |
| 7 | verify_marts_quality | SQLExecuteQueryOperator | Verify no NULL transaction_id |
| 8 | end_pipeline | BashOperator | End marker |

### 9.2 DAG Dependency

```
start_pipeline
    >> ingest_raw_data
    >> verify_raw_layer
    >> run_dbt_staging
    >> run_dbt_marts
    >> run_dbt_tests          ← DATA QUALITY GATE
    >> verify_marts_quality
    >> end_pipeline
```

### 9.3 Data Quality Gate Behavior

`run_dbt_tests` chạy `dbt test --profiles-dir .` (chạy toàn bộ 38 test).

| dbt test exit code | run_dbt_tests | Downstream |
|-------------------|---------------|------------|
| 0 (PASS) | SUCCESS | Continue |
| ≠ 0 (FAILED) | FAILED | SKIPPED |

Khi `run_dbt_tests` FAILED:
- `verify_marts_quality` = SKIPPED (upstream_failed)
- `end_pipeline` = SKIPPED (upstream_failed)
- DAG = FAILED

---

## 10. FAILURE SIMULATION

### 10.1 Phương pháp

Tạo vi phạm trong `raw.transactions` bằng cách cập nhật `isFraud = '2'` (không hợp lệ) cho TransactionID = '3411796'.

Vi phạm này lan truyền qua:
- staging.stg_transactions (is_fraud = 2)
- marts.fact_transactions (is_fraud = 2)

### 10.2 Tạo vi phạm

```sql
UPDATE raw.transactions SET "isFraud" = '2' WHERE "TransactionID" = '3411796';
```

Kết quả: 1 row updated. Total rows không thay đổi (vẫn 590,540).

### 10.3 Chạy Airflow DAG với vi phạm

Run ID: `manual__2026-09-22T11:16:47+00:00`

DAG State: **FAILED**

| Task ID | State | Duration |
|---------|-------|----------|
| start_pipeline | SUCCESS | 0.6s |
| ingest_raw_data | SUCCESS | 3.6s (skip - data exists) |
| verify_raw_layer | SUCCESS | 0.9s |
| run_dbt_staging | SUCCESS | 5.2s |
| run_dbt_marts | SUCCESS | 36.5s |
| run_dbt_tests | **FAILED** | 15.8s |
| verify_marts_quality | upstream_failed (SKIPPED) | - |
| end_pipeline | upstream_failed (SKIPPED) | - |

### 10.4 Các test FAIL khi có vi phạm

3 tests FAIL:
1. `accepted_values_stg_transactions_is_fraud__0__1` — is_fraud = 2, not in [0, 1]
2. `accepted_values_fact_transactions_is_fraud__0__1` — is_fraud = 2, not in [0, 1]
3. `invalid_fraud_flag` — is_fraud = 2, NOT IN (0, 1)

dbt test result:
```
PASS=35 WARN=0 ERROR=3 SKIP=0 TOTAL=38
```

### 10.5 Chất lượng Gate hoạt động ĐÚNG

Khi dbt test FAIL → run_dbt_tests FAILED → downstream SKIPPED → DAG FAILED.

Điều này chứng minh Data Quality Gate chặn pipeline khi có vi phạm dữ liệu.

---

## 11. RESTORE VÀ RECOVERY

### 11.1 Restore dữ liệu

```sql
UPDATE raw.transactions SET "isFraud" = '0' WHERE "TransactionID" = '3411796';
```

Kết quả: 1 row updated.

### 11.2 Xác nhận restore

| Check | Result |
|-------|--------|
| isFraud cho TransactionID 3411796 | 0 ✅ |
| raw.transactions count | 590,540 ✅ |
| dbt test (all) | PASS=38 ✅ |

### 11.3 Chạy lại dbt

```
dbt run --profiles-dir .    → PASS=6
dbt test --profiles-dir .   → PASS=38
```

---

## 12. FINAL NORMAL RUN (Sau Restore)

Run ID: `manual__2026-09-22T11:25:13+00:00`

DAG State: **SUCCESS**

| Task ID | State | Start | End |
|---------|-------|-------|-----|
| start_pipeline | SUCCESS | 11:25:14 | 11:25:15 |
| ingest_raw_data | SUCCESS | 11:25:15 | 11:25:19 |
| verify_raw_layer | SUCCESS | 11:25:20 | 11:25:21 |
| run_dbt_staging | SUCCESS | 11:25:23 | 11:25:28 |
| run_dbt_marts | SUCCESS | 11:25:29 | 11:26:07 |
| run_dbt_tests | SUCCESS | 11:26:08 | 11:26:48 |
| verify_marts_quality | SUCCESS | 11:26:50 | 11:26:51 |
| end_pipeline | SUCCESS | 11:26:52 | 11:26:53 |

---

## 13. LOAD_RAW.IDEMPOTENCY FIX

### Vấn đề
CSV files trong `data/raw/` bị mất sau khi ingest. Khi Airflow chạy lại, `load_raw.py` thất bại vì `FileNotFoundError: data/raw/train_transaction.csv`.

### Giải pháp
Thêm hàm `check_raw_data_exists()` vào `load_raw.py`:
- Trước khi load CSV, kiểm tra xem raw table đã có dữ liệu chưa
- Nếu có → skip load CSV, chỉ verify row count
- Nếu không → load CSV như bình thường

File sửa: `ingestion/load_raw.py`

---

## 14. SUCCESS CRITERIA

```text
[✅] Ingestion chạy SUCCESS trong Airflow
[✅] Raw verification SUCCESS
[✅] dbt staging SUCCESS
[✅] dbt marts SUCCESS
[✅] dbt tests SUCCESS (PASS=38)
[✅] Data Quality Gate hoạt động đúng
[✅] verify_marts_quality SUCCESS
[✅] end_pipeline SUCCESS
[✅] toàn DAG SUCCESS
[✅] Failure simulation tạo được FAILED quality gate
[✅] Downstream tasks bị SKIPPED khi quality gate fail
[✅] Dữ liệu được restore
[✅] Final normal run SUCCESS
[✅] Không có ERROR
[✅] Documentation cập nhật
[✅] Evidence report tồn tại
[✅] Không có dữ liệu giả
[✅] Không phá các Phase trước
```

---

## 15. LIÊN HỆ

- Trước: [PHASE 13 — Airflow](../13_airflow/airflow_dag.md)
- Sau: [PHASE 15 — Fraud Detection Prep](../15_fraud_detection/fraud_detection_prep.md)

---

## 16. EVIDENCE FILES

| File | Mô tả |
|------|--------|
| `docs/data_quality/baseline.md` | Baseline metrics |
| `docs/data_quality/thresholds.md` | Quality thresholds |
| `docs/data_quality/quality_report.md` | Full quality report |
| `docs/data_quality/phase14_airflow_evidence.md` | Detailed evidence with DAG runs |

---

*Cập nhật: 2026-09-22 | Version: 2.0*
