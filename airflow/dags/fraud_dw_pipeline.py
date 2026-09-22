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
