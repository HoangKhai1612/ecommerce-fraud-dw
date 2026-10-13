-- Phase 20 — Fraud analysis by device type (bar chart)
-- device_type đã được materialize trong marts.fact_transactions
-- (không cần join dim_device — tránh nhân bản giao dịch).
-- 76% giao dịch có device_type = NULL → gom vào nhóm 'Unknown'
-- bằng COALESCE(NULLIF(...)), không loại bỏ âm thầm.
--
-- Sắp xếp tỷ lệ gian lận giảm dần. Hiển thị kèm tổng số giao
-- dịch để tránh hiểu nhầm nhóm ít giao dịch có tỷ lệ cao.

SELECT COALESCE(NULLIF(device_type, ''), 'Unknown') AS device_type,
       COUNT(*) AS total_transactions,
       COUNT(*) FILTER (WHERE is_fraud = 1) AS fraud_transactions,
       ROUND(
           100.0 * COUNT(*) FILTER (WHERE is_fraud = 1)
           / NULLIF(COUNT(*), 0),
           2
       ) AS fraud_rate_pct
FROM marts.fact_transactions
GROUP BY device_type
ORDER BY fraud_rate_pct DESC;

-- Kết quả thực tế:
--   device_type | total | fraud | rate
--   ------------+-------+-------+------
--   mobile      | 55,645| 5,657 | 10.17%
--   desktop     | 85,165| 5,554 |  6.52%
--   Unknown    |449,730| 9,452 |  2.10%
