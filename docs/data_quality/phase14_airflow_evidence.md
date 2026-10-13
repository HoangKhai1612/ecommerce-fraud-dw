# PHASE 14 — Airflow Data Quality Evidence Report

## 1. Environment

| Item | Value |
|---|---|
| Project root | C:\Users\Administrator\Documents\ecommerce-fraud-dw |
| Database | PostgreSQL (host.docker.internal:5432) |
| Database name | ecommerce_fraud_dw |
| User | postgres |
| Airflow container | fraud_dw_airflow |
| Airflow version | 2.10.5 |
| dbt version | 1.8.2 |
| Python | 3.12.9 |
| DAG ID | fraud_dw_pipeline |
| Schedule | @daily |

---

## 2. Airflow DAG Structure

| # | Task ID | Type | Description |
|---|---------|------|-------------|
| 1 | start_pipeline | BashOperator | Start marker |
| 2 | ingest_raw_data | BashOperator | Load CSV to raw layer (idempotent) |
| 3 | verify_raw_layer | SQLExecuteQueryOperator | Verify raw counts |
| 4 | run_dbt_staging | BashOperator | dbt run --select staging |
| 5 | run_dbt_marts | BashOperator | dbt run --select marts |
| 6 | run_dbt_tests | BashOperator | dbt test (Data Quality Gate) |
| 7 | verify_marts_quality | SQLExecuteQueryOperator | Verify no NULL transaction_id |
| 8 | end_pipeline | BashOperator | End marker |

### DAG Dependencies

```
start_pipeline → ingest_raw_data → verify_raw_layer → run_dbt_staging → run_dbt_marts → run_dbt_tests → verify_marts_quality → end_pipeline
```

---

## 3. Raw Layer Verification

| Table | Expected | Actual | Status |
|---|---:|---:|---|
| raw.transactions | 590,540 | 590,540 | PASS |
| raw.identity | 144,233 | 144,233 | PASS |
| NULL TransactionID (raw.transactions) | 0 | 0 | PASS |
| Duplicate TransactionID (raw.transactions) | 0 | 0 | PASS |
| NULL TransactionID (raw.identity) | 0 | 0 | PASS |
| Duplicate TransactionID (raw.identity) | 0 | 0 | PASS |

---

## 4. Staging Layer Verification

| Table | Expected | Actual | Status |
|---|---:|---:|---|
| staging.stg_transactions | 590,540 | 590,540 | PASS |
| staging.stg_identity | 144,233 | 144,233 | PASS |

---

## 5. Marts Layer Verification

| Table | Expected | Actual | Status |
|---|---:|---:|---|
| marts.fact_transactions | 590,540 | 590,540 | PASS |
| marts.dim_product | 22 | 22 | PASS |
| marts.dim_device | 1,939 | 1,939 | PASS |
| marts.dim_date | 183 | 183 | PASS |

---

## 6. Data Quality Tests (dbt test)

| Metric | Value |
|---|---:|
| Total tests | 38 |
| PASS | 38 |
| WARN | 0 |
| ERROR | 0 |
| SKIP | 0 |

---

## 7. Data Quality Gate

**Task: run_dbt_tests**

Command: `cd /opt/airflow/dbt && dbt test --profiles-dir .`

Behavior:
- If `dbt test` exit code = 0 → task SUCCESS → downstream continues
- If `dbt test` exit code ≠ 0 → task FAILED → downstream SKIPPED

This is the official Data Quality Gate for the pipeline.

---

## 8. Normal Pipeline Run (Final)

**Run ID:** `manual__2026-09-22T11:25:13+00:00`

**DAG State:** SUCCESS

| Task ID | State | Start | End |
|---|---|---|---|
| start_pipeline | SUCCESS | 11:25:14 | 11:25:15 |
| ingest_raw_data | SUCCESS | 11:25:15 | 11:25:19 |
| verify_raw_layer | SUCCESS | 11:25:20 | 11:25:21 |
| run_dbt_staging | SUCCESS | 11:25:23 | 11:25:28 |
| run_dbt_marts | SUCCESS | 11:25:29 | 11:26:07 |
| run_dbt_tests | SUCCESS | 11:26:08 | 11:26:48 |
| verify_marts_quality | SUCCESS | 11:26:50 | 11:26:51 |
| end_pipeline | SUCCESS | 11:26:52 | 11:26:53 |

---

## 9. Failure Simulation

### Method

Modified `raw.transactions` by setting `isFraud = '2'` (invalid) for TransactionID = '3411796'.

This created a data quality violation that propagates through:
- staging.stg_transactions (invalid is_fraud)
- marts.fact_transactions (invalid is_fraud)

Violation was detected by:
- `accepted_values_stg_transactions_is_fraud__0__1` (FAIL)
- `accepted_values_fact_transactions_is_fraud__0__1` (FAIL)
- `invalid_fraud_flag` (FAIL)

### Failure Run Results

**Run ID:** `manual__2026-09-22T11:16:47+00:00`

**DAG State:** FAILED

| Task ID | State | Start | End |
|---|---|---|---|
| start_pipeline | SUCCESS | 11:16:48 | 11:16:49 |
| ingest_raw_data | SUCCESS | 11:16:50 | 11:16:53 |
| verify_raw_layer | SUCCESS | 11:16:55 | 11:16:56 |
| run_dbt_staging | SUCCESS | 11:16:57 | 11:17:02 |
| run_dbt_marts | SUCCESS | 11:17:03 | 11:17:39 |
| run_dbt_tests | **FAILED** | 11:20:24 | 11:20:39 |
| verify_marts_quality | upstream_failed | 11:20:40 | 11:20:40 |
| end_pipeline | upstream_failed | 11:20:40 | 11:20:40 |

### Quality Gate Behavior

When `run_dbt_tests` FAILED:
- `verify_marts_quality` = upstream_failed (SKIPPED)
- `end_pipeline` = upstream_failed (SKIPPED)
- DAG = FAILED

This proves the Data Quality Gate correctly blocks downstream processing when quality violations are detected.

---

## 10. Restore

Restored `raw.transactions` by setting `isFraud = '0'` for TransactionID = '3411796'.

Verification:
- isFraud = 0 for TransactionID '3411796' ✓
- raw.transactions count = 590,540 ✓
- All dbt tests = PASS ✓

---

## 11. Final Successful Run (After Restore)

**Run ID:** `manual__2026-09-22T11:25:13+00:00`

**DAG State:** SUCCESS

All 8 tasks = SUCCESS (see Section 8 for details).

---

## 12. Known Warnings

FutureWarning: The `auth_backends` setting in `[api]` has had `airflow.api.auth.backend.session` added in the running config, which is needed by the UI. Please update your config before Apache Airflow 3.0.

This is a compatibility warning for Airflow 3. Does NOT affect pipeline execution.

---

## 13. Final Status

| Criteria | Status |
|---|---|
| Ingestion runs SUCCESS in Airflow | ✅ |
| Raw verification SUCCESS | ✅ |
| dbt staging SUCCESS | ✅ |
| dbt marts SUCCESS | ✅ |
| dbt tests SUCCESS | ✅ |
| Data Quality Gate works correctly | ✅ |
| verify_marts_quality SUCCESS | ✅ |
| end_pipeline SUCCESS | ✅ |
| Full DAG SUCCESS | ✅ |
| Failure simulation creates FAILED gate | ✅ |
| Downstream SKIPPED on quality gate fail | ✅ |
| Data restored | ✅ |
| Final normal run SUCCESS | ✅ |
| No ERROR | ✅ |
| Documentation updated | ✅ |
| Evidence report exists | ✅ |
| No fake data | ✅ |
| No previous phases broken | ✅ |

---

## 14. dbt Test Results

### Normal Run (dbt test)

```
PASS=38
WARN=0
ERROR=0
SKIP=0
TOTAL=38
```

### Failure Run (dbt test with violation)

```
PASS=35
WARN=0
ERROR=3
SKIP=0
TOTAL=38
```

Failed tests:
1. accepted_values_stg_transactions_is_fraud__0__1 (is_fraud = 2, not in [0,1])
2. accepted_values_fact_transactions_is_fraud__0__1 (is_fraud = 2, not in [0,1])
3. invalid_fraud_flag (is_fraud = 2, NOT IN (0, 1))

### Restore Run (dbt test)

```
PASS=38
WARN=0
ERROR=0
SKIP=0
TOTAL=38
```

---

*Report generated: 2026-09-22 | Phase 14 COMPLETED*
