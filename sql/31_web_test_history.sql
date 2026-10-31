-- Phase 31: Integrated Fraud Detection Testing Platform
-- Lịch sử kiểm thử giao dịch web (tách biệt với marts.predictions của batch Phase 19).
-- Khởi tạo idempotent: CREATE TABLE IF NOT EXISTS, không ảnh hưởng dữ liệu hiện có.
-- Không ghi vào bảng giao dịch thật (marts.fact_transactions chỉ đọc).

CREATE TABLE IF NOT EXISTS marts.web_test_history (
    prediction_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    transaction_id     BIGINT NULL,                                     -- tham chiếu fact_transactions khi biết (mode ieee-cis)
    model_version      TEXT NOT NULL,
    input_mode         TEXT NOT NULL CHECK (input_mode IN ('ieee-cis', 'ecommerce-sim')),
    input_payload      JSONB NOT NULL,                                  -- dữ liệu nhập của lần kiểm thử (chỉ lịch sử web)
    is_fraud_predicted INTEGER NOT NULL CHECK (is_fraud_predicted IN (0, 1)),
    fraud_probability  DOUBLE PRECISION NOT NULL,
    threshold          DOUBLE PRECISION NOT NULL,
    predicted_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    ai_explanation     TEXT NULL,
    ai_explanation_at  TIMESTAMPTZ NULL,
    ai_available       BOOLEAN NOT NULL DEFAULT FALSE,
    status             TEXT NOT NULL DEFAULT 'ok' CHECK (status IN ('ok', 'error'))
);

CREATE INDEX IF NOT EXISTS idx_web_test_history_predicted_at
    ON marts.web_test_history (predicted_at DESC);

CREATE INDEX IF NOT EXISTS idx_web_test_history_mode
    ON marts.web_test_history (input_mode);

CREATE INDEX IF NOT EXISTS idx_web_test_history_label
    ON marts.web_test_history (is_fraud_predicted);

CREATE INDEX IF NOT EXISTS idx_web_test_history_transaction_id
    ON marts.web_test_history (transaction_id)
    WHERE transaction_id IS NOT NULL;

-- Comment để metadata tự mô tả
COMMENT ON TABLE marts.web_test_history IS 'Lich su kiem thu giao dich web (Phase 31). Chua du doan thuc, khong ghi vao bang giao dịch goc.';
COMMENT ON COLUMN marts.web_test_history.prediction_id IS 'Ma duy nhat cua lan kiem thu (UUID).';
COMMENT ON COLUMN marts.web_test_history.transaction_id IS 'Ma giao dich goc neu co (marts.fact_transactions.transaction_id), NULL neu la phuong thuc mo phong.';
COMMENT ON COLUMN marts.web_test_history.model_version IS 'Phien ban model duoc su dung (xgboost-v1-phase16).';
COMMENT ON COLUMN marts.web_test_history.input_mode IS 'Che do kiem thu: ieee-cis (du lieu IEEE-CIS) hoac ecommerce-sim (mo phong).';
COMMENT ON COLUMN marts.web_test_history.input_payload IS 'Du lieu nhap vao cua lan kiem thu (JSONB, chi luu tru lich su web).';
COMMENT ON COLUMN marts.web_test_history.is_fraud_predicted IS 'Nhan du doan cua XGBoost (0 = khong gian lận, 1 = gian lận, ng buong 0.5).';
COMMENT ON COLUMN marts.web_test_history.fraud_probability IS 'Xac suat gian lận tu predict_proba (class 1).';
COMMENT ON COLUMN marts.web_test_history.threshold IS 'Nguong nhan du doan duoc ap dung.';
COMMENT ON COLUMN marts.web_test_history.predicted_at IS 'Thoi gian thuc hien du doan.';
COMMENT ON COLUMN marts.web_test_history.ai_explanation IS 'Giai thich tu AI Assistant (duoc sinh boi LLM, khong la ket qua model).';
COMMENT ON COLUMN marts.web_test_history.ai_available IS 'Co AI Assistant/Ollama khi giai thich hay khong.';
COMMENT ON COLUMN marts.web_test_history.status IS 'Trang thai xu ly: ok hoac error.';
