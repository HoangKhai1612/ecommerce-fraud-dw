# PHASE 13 — Airflow DAG

## 1. MỤC TIÊU

Xây dựng Airflow DAG để orchestrate toàn bộ pipeline:
- Ingestion (CSV → PostgreSQL RAW)
- dbt Staging models
- dbt Marts models (Star Schema)
- dbt tests
- Data Quality verification
- Pipeline end

---

## 2. CÀI ĐẶT

```powershell
.venv\Scripts\Activate.ps1
pip install apache-airflow==2.8.0
pip install apache-airflow-providers-postgres
pip install dbt-core dbt-postgres
```

---

## 3. CẤU TRÚC THƯ MỤC

```
airflow/
├── dags/
│   └── fraud_dw_pipeline.py   # Main DAG
├── logs/                        # Auto-generated
├── plugins/                     # Custom operators (optional)
└── config/                      # Airflow config files
```

**Dùng docker-compose.airflow.yml riêng** (không trùng với docker-compose.yml chính):

```
docker-compose.airflow.yml
```

---

## 4. DAG CODE

File: `airflow/dags/fraud_dw_pipeline.py`

```python
"""
Airflow DAG: E-commerce Fraud Detection Pipeline
DAG ID: fraud_dw_pipeline
Orchestrates: Ingestion -> dbt Staging -> dbt Marts -> dbt Tests -> Raw/DW Verification
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.providers.common.sql.operators.sql import SQLExecuteQueryOperator

default_args = {
    'owner': 'kayy',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=2),
}

with DAG(
    dag_id='fraud_dw_pipeline',
    description='E-commerce Fraud Detection Data Warehouse Pipeline',
    default_args=default_args,
    start_date=datetime(2026, 9, 1),
    schedule_interval='@daily',
    catchup=False,
    tags=['ecommerce', 'fraud', 'dw', 'dbt'],
    max_active_runs=1,
) as dag:

    # 1. Start pipeline
    start_pipeline = BashOperator(
        task_id='start_pipeline',
        bash_command='echo "Starting E-commerce Fraud DW Pipeline at $(date)"',
    )

    # 2. Ingest raw CSV data into PostgreSQL RAW layer
    ingest_raw_data = BashOperator(
        task_id='ingest_raw_data',
        bash_command='cd /opt/airflow && python3 /opt/airflow/ingestion/load_raw.py',
    )

    # 3. Verify raw data in PostgreSQL
    verify_raw_layer = SQLExecuteQueryOperator(
        task_id='verify_raw_layer',
        conn_id='postgres_default',
        sql="""
        SELECT 'transactions' AS table_name, COUNT(*) AS row_count FROM raw.transactions
        UNION ALL
        SELECT 'identity' AS table_name, COUNT(*) AS row_count FROM raw.identity;
        """,
    )

    # 4. Run dbt Staging models
    run_dbt_staging = BashOperator(
        task_id='run_dbt_staging',
        bash_command='cd /opt/airflow/dbt && dbt run --select staging --profiles-dir .',
    )

    # 5. Run dbt Marts models
    run_dbt_marts = BashOperator(
        task_id='run_dbt_marts',
        bash_command='cd /opt/airflow/dbt && dbt run --select marts --profiles-dir .',
    )

    # 6. Run dbt data tests
    run_dbt_tests = BashOperator(
        task_id='run_dbt_tests',
        bash_command='cd /opt/airflow/dbt && dbt test --profiles-dir .',
    )

    # 7. Quality check on DW tables
    verify_marts_quality = SQLExecuteQueryOperator(
        task_id='verify_marts_quality',
        conn_id='postgres_default',
        sql="""
        SELECT COUNT(*) FROM marts.fact_transactions WHERE transaction_id IS NULL;
        """,
    )

    # 8. End pipeline
    end_pipeline = BashOperator(
        task_id='end_pipeline',
        bash_command='echo "E-commerce Fraud DW Pipeline completed successfully at $(date)"',
    )

    # Task dependencies
    start_pipeline >> ingest_raw_data >> verify_raw_layer
    verify_raw_layer >> run_dbt_staging >> run_dbt_marts
    run_dbt_marts >> run_dbt_tests >> verify_marts_quality >> end_pipeline
```

---

## 5. CÁC TASK TRONG DAG

| # | Task ID | Loại | Mô tả |
|---|---------|------|--------|
| 1 | `start_pipeline` | BashOperator | Bắt đầu pipeline |
| 2 | `ingest_raw_data` | BashOperator | Chạy `load_raw.py` nạp CSV vào PostgreSQL |
| 3 | `verify_raw_layer` | SQLExecuteQueryOperator | Kiểm tra row count raw.transactions + raw.identity |
| 4 | `run_dbt_staging` | BashOperator | `dbt run --select staging` |
| 5 | `run_dbt_marts` | BashOperator | `dbt run --select marts` |
| 6 | `run_dbt_tests` | BashOperator | `dbt test` |
| 7 | `verify_marts_quality` | SQLExecuteQueryOperator | Kiểm tra NULL transaction_id trong fact_transactions |
| 8 | `end_pipeline` | BashOperator | Kết thúc pipeline |

**Luồng chạy:**
```
start_pipeline → ingest_raw_data → verify_raw_layer → run_dbt_staging → run_dbt_marts → run_dbt_tests → verify_marts_quality → end_pipeline
```

---

## 6. DOCKER COMPOSE CHO AIRFLOW

File: `docker-compose.airflow.yml` (**riêng biệt**, không trùng với `docker-compose.yml` chính)

```yaml
services:

  airflow:
    build:
      context: .
      dockerfile: Dockerfile.airflow

    container_name: fraud_dw_airflow

    restart: unless-stopped

    ports:
      - "8080:8080"

    environment:
      # ==========================================================
      # AIRFLOW
      # ==========================================================
      AIRFLOW__CORE__EXECUTOR: LocalExecutor

      AIRFLOW__DATABASE__SQL_ALCHEMY_CONN: postgresql+psycopg2://postgres:%40Melons16122005@host.docker.internal:5432/airflow_db

      AIRFLOW__CORE__LOAD_EXAMPLES: "false"

      AIRFLOW__API__AUTH_BACKENDS: airflow.api.auth.backend.basic_auth

      AIRFLOW_CONN_POSTGRES_DEFAULT: postgres://postgres:%40Melons16122005@host.docker.internal:5432/ecommerce_fraud_dw

      AIRFLOW__SCHEDULER__ENABLE_HEALTH_CHECK: "true"

      # ==========================================================
      # POSTGRES / DBT
      # ==========================================================
      POSTGRES_HOST: host.docker.internal
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: "@Melons16122005"
      POSTGRES_DB: ecommerce_fraud_dw

      DBT_POSTGRES_HOST: host.docker.internal
      DBT_POSTGRES_USER: postgres
      DBT_POSTGRES_PASSWORD: "@Melons16122005"
      DBT_POSTGRES_DB: ecommerce_fraud_dw

    volumes:
      # ==========================================================
      # AIRFLOW
      # ==========================================================
      - ./airflow/dags:/opt/airflow/dags
      - ./airflow/logs:/opt/airflow/logs
      - ./airflow/plugins:/opt/airflow/plugins
      - ./airflow/config:/opt/airflow/config

      # ==========================================================
      # PROJECT
      # ==========================================================
      - ./ingestion:/opt/airflow/ingestion
      - ./dbt:/opt/airflow/dbt
      - ./data:/opt/airflow/data

    command: >
      bash -c "
        airflow db migrate &&
        airflow users create
          --username admin
          --password admin
          --firstname Admin
          --lastname User
          --role Admin
          --email admin@example.com || true &&
        airflow scheduler &
        exec airflow webserver --port 8080
      "
```

**Lưu ý quan trọng:**
- Kết nối PostgreSQL qua `host.docker.internal:5432` (không phải `postgres:5432`)
- Password `@Melons16122005` được URL-encode thành `%40Melons16122005`
- Airflow và PostgreSQL là **2 Docker Compose riêng biệt**

---

## 7. KẾT NỐI POSTGRESQL CHO AIRFLOW

### Trong Airflow UI:
1. Truy cập `http://localhost:8080`
2. Admin → Connections → "+"
3. Tạo connection:

| Field | Value |
|-------|-------|
| **Conn Id** | `postgres_default` |
| **Conn Type** | Postgres |
| **Host** | `host.docker.internal` |
| **Port** | `5432` |
| **Schema** | `ecommerce_fraud_dw` |
| **Login** | `postgres` |
| **Password** | `@Melons16122005` |

### Hoặc qua biến môi trường (đã có trong docker-compose.airflow.yml):

```yaml
AIRFLOW_CONN_POSTGRES_DEFAULT: postgres://postgres:%40Melons16122005@host.docker.internal:5432/ecommerce_fraud_dw
```

---

## 8. CHẠY AIRFLOW

```powershell
# 1. Chạy Airflow (dùng docker-compose riêng)
docker compose -f docker-compose.airflow.yml up -d

# 2. Đợi Airflow khởi động (khoảng 30s)
docker compose -f docker-compose.airflow.yml logs -f airflow

# 3. Truy cập UI
# http://localhost:8080
# Username: admin
# Password: admin

# 4. Unpause DAG "fraud_dw_pipeline"

# 5. Trigger manually
# Click "Trigger Dag" button

# 6. Monitor
# Xem logs, graph view, tree view trong UI
```

---

## 9. EXPECTED LOGS

```
[2026-09-01 14:00:00] {taskinstance.py:1136} INFO - Task exited as SUCCESS
[2026-09-01 14:00:01] {taskinstance.py:1136} INFO - Task 'start_pipeline' SUCCESS
[2026-09-01 14:00:05] {taskinstance.py:1136} INFO - Task 'ingest_raw_data' SUCCESS
[2026-09-01 14:00:10] {taskinstance.py:1136} INFO - Task 'verify_raw_layer' SUCCESS
[2026-09-01 14:00:30] {taskinstance.py:1136} INFO - Task 'run_dbt_staging' SUCCESS
[2026-09-01 14:01:00] {taskinstance.py:1136} INFO - Task 'run_dbt_marts' SUCCESS
[2026-09-01 14:01:30] {taskinstance.py:1136} INFO - Task 'run_dbt_tests' SUCCESS
[2026-09-01 14:01:35] {taskinstance.py:1136} INFO - Task 'verify_marts_quality' SUCCESS
[2026-09-01 14:01:36] {taskinstance.py:1136} INFO - Task 'end_pipeline' SUCCESS
```

---

## 10. SUCCESS CRITERIA

```text
[✅] Airflow UI accessible (http://localhost:8080)
[✅] DAG "fraud_dw_pipeline" visible
[✅] DAG runs successfully (all 8 tasks PASS)
[✅] RAW layer populated (590,540 + 144,233 rows)
[✅] Staging models built
[✅] dbt tests pass
[✅] Data quality check passes (no NULL transaction_id)
```

---

## 11. LIÊN HỆ

- Trước: [PHASE 12 — dbt Models](../12_dbt_models/dbt_models.md)
- Sau: [PHASE 14 — Data Quality](../14_data_quality/data_quality.md)

*Cập nhật: 09/09/2026 | Version: 2.0*
