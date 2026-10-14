# PHASE 26 — RUNBOOK

## 1. Điều kiện tiên quyết
- Python 3.14.x (khớp môi trường)
- pip installed
- Docker Desktop/daemon available (nếu cần kiểm tra services)
- .env hợp lệ (không in secrets)
- Dự án nằm tại C:\Users\Administrator\Documents\ecommerce-fraud-dw

## 2. Cách chạy (PowerShell)

### 2.1 Kiểm tra môi trường
`powershell
cd C:\Users\Administrator\Documents\ecommerce-fraud-dw
python scripts/diagnose_environment.py
`
Kết quả ghi tại: evidence/phase_26/diagnostics.json

### 2.2 Chẩn đoán nhanh bằng PowerShell
`powershell
cd C:\Users\Administrator\Documents\ecommerce-fraud-dw
.\scripts\diagnose_environment.ps1
`
Kết quả ghi tại: evidence/phase_26/environment_report.txt

### 2.3 Quét log
`powershell
cd C:\Users\Administrator\Documents\ecommerce-fraud-dw
python scripts/check_logs.py
python scripts/check_logs.py --files logs/pipeline.log logs/ingestion.log dbt/logs/dbt.log
`
Chỉ đọc log; không xóa/sửa log gốc.

### 2.4 Chạy unit tests Phase 26
`powershell
cd C:\Users\Administrator\Documents\ecommerce-fraud-dw
python -m pytest tests/test_phase26.py -v
`

### 2.5 Chạy regression tests (trong phạm vi có thể)
`powershell
cd C:\Users\Administrator\Documents\ecommerce-fraud-dw
python -m pytest tests/test_logging.py tests/test_security.py -v 2>
python -m pytest tests/test_ingestion.py tests/test_ml.py -v 2>
`
Chỉ chạy những test không yêu cầu services thực tế nếu chưa sẵn sàng.

## 3. Exit codes
- diagnose_environment.py: 0 nếu không có FAIL; 1 nếu có ít nhất 1 FAIL
- check_logs.py: luôn trả về 0 (chỉ quét đọc)

## 4. Cách đọc kết quả
- PASS: kiểm tra thành công
- WARN: cần chú ý, không chặn
- FAIL: cần xử lý
- SKIPPED/BLOCKED: ghi rõ lý do trong evidence

## 5. Evidence
Lưu kết quả vào evidence/phase_26/. Không đưa credentials, dữ liệu giao dịch thật, hoặc toàn bộ env vars vào evidence.

## 6. Lưu ý an toàn
- Không drop DB/schema/tables
- Không chạy docker system prune -a --volumes
- Không vô hiệu hóa SQL validator/read-only/timeouts/row limits
- Không tự động sửa môi trường
- Không tạo evidence giả
