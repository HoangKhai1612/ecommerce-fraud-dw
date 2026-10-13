#!/bin/bash
echo "=== BACKUP ==="
docker exec fraud_dw_airflow bash -c "PGPASSWORD='@Melons16122005' psql -h host.docker.internal -U postgres -d ecommerce_fraud_dw -c \"SELECT 'fact_transactions' as tbl, COUNT(*) FROM marts.fact_transactions UNION ALL SELECT 'raw.transactions', COUNT(*) FROM raw.transactions UNION ALL SELECT 'raw.identity', COUNT(*) FROM raw.identity UNION ALL SELECT 'stg.transactions', COUNT(*) FROM staging.stg_transactions UNION ALL SELECT 'stg.identity', COUNT(*) FROM staging.stg_identity;\""

echo "=== Insert violation ==="
docker exec fraud_dw_airflow bash -c "PGPASSWORD='@Melons16122005' psql -h host.docker.internal -U postgres -d ecommerce_fraud_dw -c \"INSERT INTO marts.fact_transactions (transaction_key, transaction_id, is_fraud, transaction_amt, product_key, device_key) VALUES (999999999, 'VIOLATION_TEST_001', 0, -100.00, 1, 1);\""

echo "=== Verify violation exists ==="
docker exec fraud_dw_airflow bash -c "PGPASSWORD='@Melons16122005' psql -h host.docker.internal -U postgres -d ecommerce_fraud_dw -c \"SELECT COUNT(*) as negative_count FROM marts.fact_transactions WHERE transaction_amt < 0;\""
docker exec fraud_dw_airflow bash -c "PGPASSWORD='@Melons16122005' psql -h host.docker.internal -U postgres -d ecommerce_fraud_dw -c \"SELECT COUNT(*) as violation_count FROM marts.fact_transactions WHERE transaction_id = 'VIOLATION_TEST_001';\""

echo "=== Run dbt test (expect FAIL) ==="
docker exec fraud_dw_airflow bash -c "cd /opt/airflow/dbt && dbt test --select negative_transaction_amount --profiles-dir . 2>&1; echo TEST_EXIT: $?"

echo "=== Restore ==="
docker exec fraud_dw_airflow bash -c "PGPASSWORD='@Melons16122005' psql -h host.docker.internal -U postgres -d ecommerce_fraud_dw -c \"DELETE FROM marts.fact_transactions WHERE transaction_id = 'VIOLATION_TEST_001';\""

echo "=== Verify restore ==="
docker exec fraud_dw_airflow bash -c "PGPASSWORD='@Melons16122005' psql -h host.docker.internal -U postgres -d ecommerce_fraud_dw -c \"SELECT COUNT(*) FROM marts.fact_transactions;\""
docker exec fraud_dw_airflow bash -c "PGPASSWORD='@Melons16122005' psql -h host.docker.internal -U postgres -d ecommerce_fraud_dw -c \"SELECT COUNT(*) FROM marts.fact_transactions WHERE transaction_id = 'VIOLATION_TEST_001';\""
