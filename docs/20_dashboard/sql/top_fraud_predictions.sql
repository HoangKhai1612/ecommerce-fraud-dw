-- Phase 20 — Top 50 fraud predictions (table card)
-- Đọc kết quả dự đoán thật từ marts.predictions (Phase 19 ghi,
-- model_version='xgboost-v1-phase16', 88,581 rows).
--
-- Lưu ý quan trọng:
-- * fraud_probability được lưu ở thang 0..1 (đã verify trong
--   Phase 19: min 0.004984, max 0.998232) → nhân 100 để hiển
--   thị phần trăm. CAST ::numeric vì PostgreSQL không có
--   round(double precision, integer).
-- * JOIN marts.fact_transactions theo transaction_id (1:1, đã
--   verify 88,581/88,581 khớp) chỉ để lấy transaction_amt.
-- * Sắp xếp theo XÁC SUẤT giảm dần, KHÔNG theo nhãn thực tế.
-- * Đây là DỰ ĐOÁN CỦA MÔ HÌNH, không phải kết luận điều tra.
-- * UNIQUE (transaction_id, model_version) đảm bảo 1 dự đoán/
--   giao dịch cho version này — không có bản ghi trùng để lọc.

SELECT p.transaction_id,
       p.is_fraud_actual,
       p.is_fraud_predicted,
       ROUND((p.fraud_probability * 100)::numeric, 2) AS fraud_probability_pct,
       f.transaction_amt
FROM marts.predictions p
JOIN marts.fact_transactions f ON f.transaction_id = p.transaction_id
WHERE p.model_version = 'xgboost-v1-phase16'
ORDER BY p.fraud_probability DESC
LIMIT 50;

-- Kết quả thực tế: 50 rows, xác suất 99.82% .. 99.47%,
-- top 10 khớp kết quả SQL verification của Phase 19:
--   3122167 (99.82), 3127114 (99.71), 3524493/3224515/3360008
--   (99.68), 3516426/3231532/3231534 (99.67), 3085461/3395166
--   (99.66).
