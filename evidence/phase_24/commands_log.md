# Phase 24 — Commands & Exit Codes

*Ngày thực thi: 13/10/2026. Tất cả lệnh chạy từ project root với `.venv`.*

## Static validation

| Lệnh | Exit | Kết quả |
|---|---|---|
| `.venv\Scripts\python.exe -c "import ast; ast.parse(open('run_pipeline.py').read())"` | 0 | syntax OK |
| `.venv\Scripts\python.exe -m pytest tests/test_end_to_end.py -v` | 0 | 32 passed, 1 skipped (opt-in --run-pipeline) |

## Full pipeline

| Lệnh | Exit | Kết quả |
|---|---|---|
| `.venv\Scripts\python.exe run_pipeline.py --evidence-dir evidence\phase_24` | 0 | PASS=13 SKIPPED=1 FAIL=0 (xem `pipeline_summary.json`) |

Chi tiết từng bước (exit code + thời gian) trong `pipeline_summary.json` và `logs/step_*.log`.

## dbt (trong Airflow container — host dbt CLI bị lỗi protobuf/Python 3.14)

| Lệnh | Exit | Kết quả |
|---|---|---|
| `docker exec fraud_dw_airflow bash -c "cd /opt/airflow/dbt && dbt run --select staging --profiles-dir ."` | 0 | PASS=2 WARN=0 ERROR=0 (2 view models) |
| `docker exec fraud_dw_airflow bash -c "cd /opt/airflow/dbt && dbt run --select marts --profiles-dir ."` | 0 | PASS=4 WARN=0 ERROR=0 (4 table models) |
| `docker exec fraud_dw_airflow bash -c "cd /opt/airflow/dbt && dbt test --profiles-dir ."` | 0 | PASS=38 WARN=0 ERROR=0 SKIP=0 TOTAL=38 |

## E2E tests

| Lệnh | Exit | Kết quả |
|---|---|---|
| `.venv\Scripts\python.exe -m pytest tests/test_end_to_end.py -v` | 0 | 32 passed, 1 skipped (xem `pytest_results.txt`) |
| `.venv\Scripts\python.exe -m pytest tests/test_end_to_end.py --run-pipeline` | 0 | full pipeline (tùy chọn, bao gồm ML training ~10 phút) |

## Docker (Phase 23 compose, không thay đổi)

| Lệnh | Exit | Kết quả |
|---|---|---|
| `docker compose build api` | 0 | image `ecommerce-fraud-dw-api` rebuild với artifacts đã retrain |
| `docker compose up -d api` | 0 | container `fraud_dw_api` recreated, healthy |
| `docker compose ps` | 0 | 5 services: postgres(healthy), airflow(healthy), metabase, api(healthy), ai-assistant(healthy) |

## API smoke (sau pipeline)

| Endpoint | Status | Kết quả |
|---|---|---|
| GET /health | 200 | `{"status":"ok","service":"fraud-detection-api"}` |
| GET /ready | 200 | `{"status":"ready","database":"ok"}` |
| POST /predict | 200 | fraud_probability trong [0,1], is_fraud ∈ {0,1} |
| GET /transactions/3411796 | 200 | transaction thật từ DW |
| GET /transactions/predictions/top?limit=3 | 200 | 3 rows, xác suất ~0.998 |

## Quyền an toàn (AI Assistant read-only, xác minh lại)

| Lệnh | Kết quả |
|---|---|
| INSERT với `ai_assistant_ro` | `ERROR: permission denied for table predictions` |

*Không lệnh nào chứa secret. Password chỉ truyền qua `.env`.*
