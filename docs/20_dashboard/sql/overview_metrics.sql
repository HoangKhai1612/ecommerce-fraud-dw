-- Phase 20 — Overview KPI metrics (4 scalar cards)
-- Source: marts.fact_transactions (590,540 rows, grain = 1 transaction)
-- Verified against PostgreSQL 18.3 (Windows instance, localhost:5432)
-- and through Metabase's own connection (HTTP 202, card query API).

-- KPI 1: Tổng số giao dịch
SELECT COUNT(*) AS total_transactions
FROM marts.fact_transactions;

-- KPI 2: Tổng số giao dịch gian lận (nhãn thực tế is_fraud = 1)
SELECT COUNT(*) AS total_fraud_transactions
FROM marts.fact_transactions
WHERE is_fraud = 1;

-- KPI 3: Tỷ lệ giao dịch gian lận (%)
-- Chia cho NULLIF để tránh lỗi chia cho 0.
SELECT ROUND(
           100.0 * COUNT(*) FILTER (WHERE is_fraud = 1)
           / NULLIF(COUNT(*), 0),
           2
       ) AS fraud_rate_pct
FROM marts.fact_transactions;

-- KPI 4: Tổng giá trị giao dịch (tổng cột transaction_amt)
SELECT SUM(transaction_amt) AS total_amount
FROM marts.fact_transactions;

-- Kết quả thực tế (2026-10-09):
--   total_transactions       = 590,540
--   total_fraud_transactions = 20,663
--   fraud_rate_pct           = 3.50  (3.4990% trước khi làm tròn)
--   total_amount             = 79,738,980.37
