#!/bin/bash
PGPASSWORD='@Melons16122005' psql -h host.docker.internal -U postgres -d ecommerce_fraud_dw -c "SELECT transaction_id FROM marts.fact_transactions LIMIT 3;"
PGPASSWORD='@Melons16122005' psql -h host.docker.internal -U postgres -d ecommerce_fraud_dw -c "SELECT COUNT(*) FROM marts.fact_transactions;"
PGPASSWORD='@Melons16122005' psql -h host.docker.internal -U postgres -d ecommerce_fraud_dw -c "SELECT COUNT(*) FROM marts.fact_transactions WHERE transaction_amt < 0;"
