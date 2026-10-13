echo "=== DBT test log (failure run) ==="
docker exec -e PGPASSWORD=@Melons16122005 fraud_dw_airflow bash -c "find /opt/airflow/logs/dag_id=fraud_dw_pipeline/run_id=manual__2026-09-22T11:16:47+00:00/task_id=run_dbt_tests -name '*.log' -exec cat {} \;" 2>&1 | tail -50 > C:/Users/Administrator/Documents/ecommerce-fraud-dw/evidence_phase14_run_dbt_tests_log.txt
