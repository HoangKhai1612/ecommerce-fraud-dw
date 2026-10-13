-- Phase 20 — Fraud analysis by product code (bar chart)
-- product_cd đã được materialize trong marts.fact_transactions
-- (không cần join dim_product — tránh nhân bản giao dịch).
-- Không đổi tên mã sản phẩm thành tên thương mại (không có bảng
-- ánh xạ đáng tin cậy). Chỉ 5 mã, không có giá trị NULL/empty.
--
-- Sắp xếp tỷ lệ gian lận giảm dần.

SELECT product_cd,
       COUNT(*) AS total_transactions,
       COUNT(*) FILTER (WHERE is_fraud = 1) AS fraud_transactions,
       ROUND(
           100.0 * COUNT(*) FILTER (WHERE is_fraud = 1)
           / NULLIF(COUNT(*), 0),
           2
       ) AS fraud_rate_pct
FROM marts.fact_transactions
GROUP BY product_cd
ORDER BY fraud_rate_pct DESC;

-- Kết quả thực tế:
--   product_cd | total  | fraud | rate
--   -----------+--------+-------+------
--   C          | 68,519 | 8,008 | 11.69%
--   S          | 11,628 |   686 |  5.90%
--   H          | 33,024 | 1,574 |  4.77%
--   R          | 37,699 | 1,426 |  3.78%
--   W          |439,670 | 8,969 |  2.04%
