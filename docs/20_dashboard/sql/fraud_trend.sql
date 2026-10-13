-- Phase 20 — Fraud trend by day (line chart)
-- transaction_dt là epoch TƯƠNG ĐỐI (giây tính từ mốc của dataset,
-- convention của bộ dữ liệu Kaggle credit card fraud), KHÔNG phải
-- Unix epoch của lịch thật: to_timestamp(transaction_dt) cho ra
-- 1970-01-02 .. 1970-07-03. Biểu đồ thể hiện trục thời gian tương
-- đối của dataset. marts.dim_date có 183 ngày (date_key 1..183)
-- tương ứng, nhưng fact_transactions không có FK date_key nên trend
-- được nhóm trực tiếp từ transaction_dt.
--
-- Tỷ lệ gian lận được tính từ SỐ LƯỢNG giao dịch từng ngày
-- (COUNT FILTER / COUNT), không phải trung bình các tỷ lệ ngày.

SELECT to_timestamp(transaction_dt)::date AS transaction_date,
       COUNT(*) AS total_transactions,
       COUNT(*) FILTER (WHERE is_fraud = 1) AS fraud_transactions,
       ROUND(
           100.0 * COUNT(*) FILTER (WHERE is_fraud = 1)
           / NULLIF(COUNT(*), 0),
           2
       ) AS fraud_rate_pct
FROM marts.fact_transactions
GROUP BY transaction_date
ORDER BY transaction_date;

-- Kết quả thực tế: 182 ngày có giao dịch
-- (1970-01-02 .. 1970-07-02), mỗi ngày ~2,000-6,800 giao dịch,
-- tỷ lệ gian lận theo ngày dao động ~1.1% .. 6.99%.
-- Không kết luận xu hướng tăng/giảm nếu không phân tích thêm.
