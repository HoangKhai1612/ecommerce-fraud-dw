# Data Quality Report

## Phase 14 — Data Quality Validation

### 1. Overall Status

**PASS**

Data Warehouse đã hoàn thành quá trình kiểm tra Data Quality bằng
dbt và Airflow Data Quality Gate.

Kết quả cuối cùng (dbt test):

```text
PASS=38
WARN=0
ERROR=0
SKIP=0
TOTAL=38

dbt build:

PASS=44
WARN=0
ERROR=0
SKIP=0
TOTAL=44

### 2. Airflow Orchestration

DAG ID: `fraud_dw_pipeline`
Schedule: `@daily`
Owner: kayy

DAG structure:

```
start_pipeline → ingest_raw_data → verify_raw_layer → run_dbt_staging → run_dbt_marts → run_dbt_tests → verify_marts_quality → end_pipeline
```

### 3. Data Quality Gate

Task `run_dbt_tests` là Data Quality Gate chính thức.

Command: `cd /opt/airflow/dbt && dbt test --profiles-dir .`

Behavior:

- `dbt test` exit code = 0 → task SUCCESS → downstream continues
- `dbt test` exit code ≠ 0 → task FAILED → downstream SKIPPED

### 4. Validation Scope

Quá trình kiểm tra bao gồm:

- Staging data validation
- Fact table validation
- Dimension validation
- Referential integrity
- Uniqueness
- Nullability
- Accepted values
- Business rules
- Row count consistency
- Fraud distribution
- Transaction amount validation
- Data completeness

### 5. Main Results

Row Count:

- stg_transactions = 590,540
- fact_transactions = 590,540

Fraud:

- fraud_transactions = 20,663
- fraud_ratio = 3.4990%

Transaction Integrity:

- NULL transaction_id = 0
- duplicate transaction_id = 0
- orphan transactions = 0

Transaction Amount:

- minimum amount = 0.25
- negative amounts = 0
- non-positive amounts = 0

Device Type:

- missing device_type = 3,423
- missing percentage = 2.3732%

### 6. dbt Validation

The dbt project successfully executed:

- 6 models (4 tables + 2 views)
- 2 sources
- 38 data quality tests
- 1 project hook

Final execution:

Completed successfully

PASS=44
WARN=0
ERROR=0
SKIP=0
NO-OP=0
REUSED=0
TOTAL=44

### 7. Quality Gate Decision

The current Data Quality state satisfies all defined quality rules.

Therefore:

DATA QUALITY GATE = PASS

The dataset is allowed to proceed to subsequent processing stages,
including Machine Learning preparation and downstream analytical
workflows.

### 8. Failure Simulation Result

A deliberate violation was introduced (`isFraud = '2'` in raw.transactions)
to verify the Data Quality Gate.

Result:

- run_dbt_tests = FAILED
- verify_marts_quality = SKIPPED (upstream_failed)
- end_pipeline = SKIPPED (upstream_failed)
- DAG = FAILED

This confirms the Data Quality Gate correctly blocks downstream
processing when quality violations are detected.

After restoring the violation, all tests pass and the DAG runs SUCCESS.

### 9. Important Note

The values documented in this report represent the verified state of
the database at the time of Phase 14 validation.

Future pipeline executions must run the Data Quality tests again
rather than assuming that the current baseline remains valid.

---

# Bước 2 — kiểm tra 3 file

Chạy:

```powershell
Get-ChildItem .\docs\data_quality
```

Phải có:

- baseline.md
- quality_report.md
- thresholds.md

---

*Cập nhật: 2026-09-22 | Version: 2.0*