# PHASE 31 — Integrated Fraud Detection Testing Platform
## Implementation Plan

### 1. Mục tiêu
Xây dựng nền tảng web tích hợp: người dùng nhập/tải dữ liệu giao dịch → gửi yêu cầu kiểm thử → XGBoost thực sự dự đoán → lưu lịch sử vào PostgreSQL → AI Assistant giải thích dựa trên kết quả thực → hiển thị trên giao diện. Luồng cốt lõi:

`Web UI → FastAPI → XGBoost inference → Prediction Record (PostgreSQL) → AI Explanation → Web UI`

### 2. Thiết kế mục tiêu (trước → sau)

| Thành phần | Trước Phase 31 | Sau Phase 31 |
|---|---|---|
| FastAPI (`api/`) | `/health`, `/ready`, `/predict` (không lưu, không có prediction ID), `/transactions/*` | Thêm `/predictions` (dự đoán + lưu, trả prediction_id), `/predictions/{id}`, `/predictions` (danh sách+lọc+phân trang), `/predictions/{id}/explain` (AI giải thích), `/transactions/sample` (mẫu kiểm thử), `/system/status` |
| PostgreSQL (marts) | `predictions` (batch Phase 19, 88.5k dòng) | Bảng mới `marts.web_test_history` (lịch sử kiểm thử web, tách biệt, không chạm dữ liệu giao dịch thật) |
| AI Assistant | `/chat` (port 8001, Ollama llama3, read-only SQL) | Gọi lại từ API với context prediction thực; fallback gọi Ollama trực tiếp nếu assistant không khả dụng |
| Giao diện | Chưa có | `web/`: React + TS + Vite, 6 trang: Overview, Transaction Testing, Prediction Detail, AI Assistant, Prediction History, System Status |
| Docker | 5 service | Thêm service `web` (frontend tĩnh qua nginx) |

### 3. File sẽ tạo

- `docs/31_integrated_platform/implementation_plan.md` (này)
- `docs/31_integrated_platform/architecture.md`
- `docs/31_integrated_platform/api_contract.md`
- `docs/31_integrated_platform/data_flow.md`
- `docs/31_integrated_platform/testing.md`
- `docs/31_integrated_platform/security.md`
- `docs/31_integrated_platform/runbook.md`
- `docs/31_integrated_platform/implementation_report.md` (viết cuối)
- `sql/31_web_test_history.sql` (DDL idempotent cho `marts.web_test_history`)
- `api/models.py` (thêm schema)
- `api/config.py` (thêm env: AI_ASSISTANT_BASE_URL, OLLAMA_BASE_URL, ...)
- `api/database.py` (helpers ghi/đọc lịch sử)
- `api/services/prediction_service.py` (inference + persist, tái sử dụng `api.inference.InferencePipeline`)
- `api/services/ai_service.py` (AI explanation: ai-assistant `/chat`, fallback Ollama `/api/chat`)
- `api/routes/predictions.py` (router mới)
- `api/main.py` (include router, khởi tạo bảng lịch sử khi startup)
- `web/` (React + Vite + TypeScript: package.json, vite.config.ts, tsconfig.json, index.html, src/, public/, Dockerfile, .env.example)
- `tests/test_phase31_api.py` (integration API với TestClient, ghi xóa bản ghi test riêng)
- `tests/test_phase31_adapter.py` (unit: mapping feature, preprocessing, output)
- `evidence/phase_31/*` (từ lần chạy thật)

### 4. File sẽ sửa

- `api/main.py` — thêm router predictions, ensure table khi startup.
- `docker-compose.yml` — thêm service `web` (không thay đổi service hiện có).
- `api/requirements.txt` — thêm `httpx` (đã có), `psycopg2-binary` (đã có). Không thêm package lớn khác.

### 5. Endpoint mới / tái sử dụng

| Endpoint | Phương | Mô tả |
|---|---|---|
| `GET /health` | GET | Tái giữ |
| `GET /ready` | GET | Tái giữ |
| `POST /predict` | POST | Tái giữ (dự đoán thô, không lưu) |
| `POST /predictions` | POST | Mới: validation → XGBoost inference → lưu `marts.web_test_history` → trả prediction record |
| `GET /predictions/{prediction_id}` | GET | Mới: chi tiết một bản ghi kiểm thử |
| `GET /predictions` | GET | Mới: danh sách, lọc (label, min/max prob, mode, thời gian), phân trang |
| `POST /predictions/{prediction_id}/explain` | POST | Mới: AI giải thích dựa trên prediction thực, lưu vào bản ghi |
| `GET /transactions/sample` | GET | Mới: lấy mẫu giao dịch từ `marts.fact_transactions` (read-only) cho chế độ A |
| `GET /system/status` | GET | Mới: trạng thái API, model, DB, Ollama/ai-assistant |

### 6. Database changes

Bảng `marts.web_test_history`:
- `prediction_id` UUID PK (gen_random_uuid)
- `transaction_id` BIGINT NULL (tham chiếu `marts.fact_transactions.transaction_id` khi có)
- `model_version` TEXT
- `input_mode` TEXT ('ieee-cis' | 'ecommerce-sim')
- `input_payload` JSONB (dữ liệu nhập, chỉ lịch sử kiểm thử)
- `is_fraud_predicted` INTEGER
- `fraud_probability` DOUBLE PRECISION
- `threshold` DOUBLE PRECISION
- `predicted_at` TIMESTAMPTZ
- `ai_explanation` TEXT NULL
- `ai_explanation_at` TIMESTAMPTZ NULL
- `ai_available` BOOLEAN
- `status` TEXT ('ok' | 'error')

Khởi tạo idempotent khi API startup (CREATE TABLE IF NOT EXISTS). Không ghi vào `marts.fact_transactions`, không dùng dbt cho inference.

### 7. Luồng dữ liệu

1. UI gửi `POST /predictions` với payload giao dịch + mode.
2. API validate (Pydantic), chuẩn hóa, gọi `InferencePipeline.predict_proba` (engineering → frequency encode → preprocessor → XGBoost predict_proba[:,1]).
3. Label = proba >= 0.5 (threshold từ artifact/cấu hình, không tự đặt mới).
4. Tạo `prediction_id` (UUID), ghi `marts.web_test_history`, trả record kèm ID.
5. UI gọi `POST /predictions/{id}/explain` → API build context thực (ID, label, prob, threshold, model version, input, top SHAP features nếu có từ `ml/models/top_features.csv`) → gọi ai-assistant `/chat`, fallback Ollama trực tiếp → lưu `ai_explanation` → trả về.
6. UI hiển thị prediction + phân rõ: kết quả model vs giải thích AI vs dữ liệu truy vấn.
7. Lịch sử đọc từ `GET /predictions` với phân trang.

### 8. Xử lý lỗi / khả năng phục hồi

- Model không load → `/predictions` trả 503, không trả kết quả giả.
- DB không khả dụng → không báo lưu thành công.
- Ollama/ai-assistant không khả dụng → dự đoán vẫn hoạt động, `ai_available = false`, UI hiển thị trạng thái AI không khả dụng.
- CSV upload lỗi → báo chính xác hàng/cột vấn đề.

### 9. Tests cần thêm

- `tests/test_phase31_adapter.py`: unit — artifact load, feature count = 1014, alignment, prediction output domain.
- `tests/test_phase31_api.py`: integration — valid request, missing fields, bad schema, model unavailable, DB read/write, list + filters + pagination, explain with real prediction ID, nonexistent ID, sample endpoint.
- Chạy lại `tests/test_ml.py`, `tests/test_api.py`, `tests/test_security.py` (baseline, không sửa).
- Ollama có sẵn cục bộ (llama3:latest) → test giải thích có thể chạy thật.

### 10. Tiêu chí nghiệm thu (Definition of Done)

- `web/` tồn tại, frontend gọi FastAPI thật.
- FastAPI thực hiện inference bằng XGBoost thật, input tuân thủ schema 1014 feature.
- Prediction có ID, có cấu trúc, lưu và truy vấn lại được.
- AI nhận đúng prediction context, giải thích dựa trên dữ liệu thật; lỗi AI không làm hỏng prediction.
- DW không trực tiếp inference; không ghi test data vào bảng giao dịch thật.
- SQL Assistant vẫn chỉ đọc; rate limiting và validation hoạt động; không lộ secrets.
- Unit/API tests PASS; E2E thật PASS khi dependency sẵn có; frontend build OK.
- Evidence từ chạy thật; báo cáo phân biệt PASS/FAIL/SKIP/BLOCKED.

### 11. Rủi ro và giảm thiểu

| Rủi ro | Giảm thiểu |
|---|---|
| ai-assistant container không chạy cục bộ | Fallback gọi Ollama trực tiếp (`localhost:11434`); dự đoán không phụ thuộc AI |
| Pandas 3.0 / numpy 2.x fragmentation warnings | Chỉ là warning, không ảnh độ chính xác; không can thiệp sâu |
| Ghi lịch sử vào DB thật | Dùng bảng riêng `marts.web_test_history`, cleanup test bằng model_version riêng |
| Threshold | Dùng 0.5 từ cấu hình hiện có, không tự đặt mới |

### 12. Thứ tự triển khai

1. Xác minh artifacts + inference (đã làm, baseline pass).
2. Thêm DDL `sql/31_web_test_history.sql` + helpers DB.
3. Thêm schemas, services (`prediction_service`, `ai_service`), router `predictions`, sửa `main.py`, `config.py`.
4. Test API (TestClient + DB thật).
5. Xây dựng `web/`, kết nối UI ↔ API.
6. Thêm Docker service `web`, kiểm tra compose không hỏng service cũ.
7. Viết tests, chạy toàn bộ suite liên quan.
8. Tài liệu + evidence, báo cáo cuối.
