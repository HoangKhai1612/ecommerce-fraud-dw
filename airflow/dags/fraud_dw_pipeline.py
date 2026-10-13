"""
Airflow DAG: E-commerce Fraud Detection Pipeline

DAG ID:
    fraud_dw_pipeline

Pipeline:
    Ingestion
        -> Raw Verification
        -> dbt Staging
        -> dbt Marts
        -> Data Quality Gate
        -> DW Quality Verification
        -> End

Data Quality Gate:
    The task `run_dbt_tests` is the mandatory gate before
    downstream warehouse verification.

If dbt tests fail:
    - run_dbt_tests becomes FAILED
    - downstream tasks are not executed
    - the pipeline stops before downstream processing
"""

from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.providers.common.sql.operators.sql import SQLExecuteQueryOperator


# ============================================================
# DEFAULT ARGUMENTS
# ============================================================

default_args = {
    "owner": "kayy",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=2),
}


# ============================================================
# DAG DEFINITION
# ============================================================

with DAG(
    dag_id="fraud_dw_pipeline",
    description=(
        "E-commerce Fraud Detection Data Warehouse Pipeline "
        "with dbt Data Quality Gate"
    ),
    default_args=default_args,
    start_date=datetime(2026, 9, 1),
    schedule="@daily",
    catchup=False,
    tags=["ecommerce", "fraud", "dw", "dbt", "data-quality"],
    max_active_runs=1,
) as dag:

    # ========================================================
    # 1. START PIPELINE
    # ========================================================

    start_pipeline = BashOperator(
        task_id="start_pipeline",
        bash_command="""
        echo "=================================================="
        echo "Starting E-commerce Fraud DW Pipeline"
        echo "Execution time: $(date)"
        echo "=================================================="
        """,
    )

    # ========================================================
    # 2. INGEST RAW DATA
    # ========================================================

    ingest_raw_data = BashOperator(
        task_id="ingest_raw_data",
        bash_command="""
        set -e

        echo "Starting raw data ingestion..."

        cd /opt/airflow
        python3 /opt/airflow/ingestion/load_raw.py

        echo "Raw data ingestion completed successfully."
        """,
    )

    # ========================================================
    # 3. VERIFY RAW LAYER
    # ========================================================

    verify_raw_layer = SQLExecuteQueryOperator(
        task_id="verify_raw_layer",
        conn_id="postgres_default",
        sql="""
        SELECT
            'transactions' AS table_name,
            COUNT(*) AS row_count
        FROM raw.transactions

        UNION ALL

        SELECT
            'identity' AS table_name,
            COUNT(*) AS row_count
        FROM raw.identity;
        """,
    )

    # ========================================================
    # 4. DBT STAGING
    # ========================================================

    run_dbt_staging = BashOperator(
        task_id="run_dbt_staging",
        bash_command="""
        set -e

        echo "Running dbt staging models..."

        cd /opt/airflow/dbt

        dbt run \
            --select staging \
            --profiles-dir .

        echo "dbt staging completed successfully."
        """,
    )

    # ========================================================
    # 5. DBT MARTS
    # ========================================================

    run_dbt_marts = BashOperator(
        task_id="run_dbt_marts",
        bash_command="""
        set -e

        echo "Running dbt marts models..."

        cd /opt/airflow/dbt

        dbt run \
            --select marts \
            --profiles-dir .

        echo "dbt marts completed successfully."
        """,
    )

    # ========================================================
    # 6. DATA QUALITY GATE
    # ========================================================

    run_dbt_tests = BashOperator(
        task_id="run_dbt_tests",
        bash_command="""
        set -e

        echo "=================================================="
        echo "DATA QUALITY GATE"
        echo "Running dbt data quality tests..."
        echo "=================================================="

        cd /opt/airflow/dbt

        dbt test \
            --profiles-dir .

        echo "=================================================="
        echo "DATA QUALITY GATE PASSED"
        echo "All dbt data quality tests passed."
        echo "Downstream tasks may continue."
        echo "=================================================="
        """,
    )

    # ========================================================
    # 7. VERIFY MARTS QUALITY
    # ========================================================

    verify_marts_quality = SQLExecuteQueryOperator(
        task_id="verify_marts_quality",
        conn_id="postgres_default",
        sql="""
        SELECT
            COUNT(*) AS null_transaction_id_count
        FROM marts.fact_transactions
        WHERE transaction_id IS NULL;
        """,
    )

    # ========================================================
    # 8. END PIPELINE
    # ========================================================

    end_pipeline = BashOperator(
        task_id="end_pipeline",
        bash_command="""
        echo "=================================================="
        echo "E-commerce Fraud DW Pipeline completed successfully"
        echo "Completion time: $(date)"
        echo "=================================================="
        """,
    )

    # ========================================================
    # TASK DEPENDENCIES
    # ========================================================

    start_pipeline >> ingest_raw_data

    ingest_raw_data >> verify_raw_layer

    verify_raw_layer >> run_dbt_staging

    run_dbt_staging >> run_dbt_marts

    run_dbt_marts >> run_dbt_tests

    # --------------------------------------------------------
    # DATA QUALITY GATE
    #
    # If run_dbt_tests fails:
    #     verify_marts_quality will NOT run.
    #
    # If run_dbt_tests succeeds:
    #     verify_marts_quality continues.
    # --------------------------------------------------------

    run_dbt_tests >> verify_marts_quality

    verify_marts_quality >> end_pipeline