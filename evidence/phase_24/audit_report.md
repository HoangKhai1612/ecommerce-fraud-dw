# Phase 24 — Audit Report (Giai đoạn A)

*Ngày audit: 13/10/2026*

## 1. Trạng thái repository

- Thư mục gốc: `C:\Users\Administrator\Documents\ecommerce-fraud-dw`
- Python venv: `.venv` (Python 3.14.0) — deps OK: fastapi, sqlglot, langchain_ollama, xgboost, sklearn, shap, matplotlib
- Docker: 29.6.2, Compose v5.3.1
- Git: binary không có trên máy (`where.exe git` thất bại) → không có `git status`/`git diff`

## 2. Kiến trúc thực tế (đối chiếu Phase 23)

| Thành phần | Thực tế |
|---|---|
| DW chính | Windows PostgreSQL 18.3 (service `postgresql-x64-18`, Automatic), host 5432. Chứa `ecommerce_fraud_dw`, `airflow_db`, `metabase_db` |
| docker-local PG | container `postgres:15-alpine`, host 5434, volume `ecommerce-fraud-dw_postgres_data` |
| Airflow | container `apache/airflow:2.10.5`+dbt 1.8.2, LocalExecutor, DAG `fraud_dw_pipeline` |
| Metabase | container `metabase/metabase:v0.49.0`, app DB `metabase_db` |
| ML API | container build từ `api/Dockerfile`, port 8000 |
| AI Assistant | container build từ `ai_assistant/Dockerfile`, port 8001 |
| Ollama | native trên host (127.0.0.1:11434), model `llama3:latest` 8B Q4_0 |

## 3. Vấn đề phát hiện

| # | Vấn đề | Ảnh hưởng | Xử lý |
|---|---|---|---|
| 1 | `data/raw/` KHÔNG TỒN TẠI — thiếu CSV nguồn (`train_transaction.csv`, `train_identity.csv`). Zip dự án cũng không chứa CSVs. Không tìm thấy CSV ở bất kỳ đâu trên đĩa | Ingestion không thể chạy. Quan trọng: `load_raw.py` dùng DROP+CREATE, chạy khi thiếu CSV sẽ HỦY raw tables (590,540 + 144,233 rows) | Runner GATE ingestion: thiếu CSV → SKIPPED, không bao giờ chạy phá hủy. RAW tables đã có sẵn và được verify riêng |
| 2 | dbt CLI trên host `.venv` bị lỗi: `TypeError: Metaclasses with custom tp_new are not supported` (protobuf 4.25.9 + Python 3.14) | Không chạy dbt staging/marts/tests trên host | Chạy dbt trong Airflow container (Python 3.12, dbt 1.8.2) qua `docker exec` — đúng nơi production DAG chạy dbt |
| 3 | DAG `fraud_dw_pipeline` run mới nhất (manual__2026-09-16) state=failed tại `ingest_raw_data` (try=2), downstream `upstream_failed` | Hệ quả trực tiếp của vấn đề #1 (thiếu CSV) | Ghi nhận là bằng chứng, không sửa DAG. `scheduled__2026-09-15` state=success (chạy khi CSV còn tồn tại) |
| 4 | `docs/24_end_to_end/end_to_end.md` cũ chứa thông tin sai: artifact `ml/models/xgb_model.pkl` (thật: `xgboost.pkl`), DAG `fraud_detection_pipeline` (thật: `fraud_dw_pipeline`), DB_URL hardcode `postgres:postgres`, test schema payload `TransactionID` (thật: `transaction_id`) | Tài liệu gây hiểu lầm | Viết lại tài liệu theo trạng thái thực tế |
| 5 | Chưa có pipeline runner, chưa có `tests/test_end_to_end.py`, `evidence/phase_24/` trống | Thiếu cơ chế chạy lại + bằng chứng | Tạo `run_pipeline.py`, `tests/test_end_to_end.py`, điền evidence |

## 4. Dữ liệu hiện có (trước pipeline)

- `raw.transactions`: 590,540 — `raw.identity`: 144,233
- `staging.stg_transactions`: 590,540 — `staging.stg_identity`: 144,233
- `marts.fact_transactions`: 590,540 (fraud=20,663, 3.499%)
- `marts.dim_product`: 22, `marts.dim_device`: 1,939, `marts.dim_date`: 183
- `marts.predictions`: 88,581 (model_version=xgboost-v1-phase16)
- Đặc điểm dữ liệu hợp lệ: 1,577 rows NULL `product_key`, 471,919 rows NULL `device_key` (LEFT JOIN không khớp — 80% transactions không có identity record). dbt `relationships` test đúng khi chỉ xét NON-NULL FK.

## 5. Artifact ML hiện có (trước pipeline)

- `ml/models/xgboost.pkl` (0.54 MB), `random_forest.pkl` (88 MB), `logistic_regression.pkl`, `logistic_scaler.pkl`
- `feature_columns.json` (1,014 features), `frequency_encoder.pkl`, `preprocessor.pkl`
- `training_results.json`: train 413,378 / val 88,581; val ROC-AUC: LR 0.870, RF 0.913, XGBoost 0.916
- Backup trước retrain: `evidence/phase_24/models_pre_training_backup/` (xgboost.pkl, feature_columns.json, frequency_encoder.pkl, preprocessor.pkl)

## 6. Cấu hình pipeline thực tế

- Ingestion: `ingestion/load_raw.py` — DATA_DIR=`./data/raw`, EXPECTED_TRANSACTIONS=590540, EXPECTED_IDENTITY=144233, DROP+CREATE (idempotent khi có CSV)
- dbt: `dbt/dbt_project.yml` — staging=view (schema staging), marts=table (schema marts); tests trong `models/marts/schema.yml` (not_null, unique, accepted_values, relationships)
- ML train: `ml/train.py` — RandomizedSearchCV (LR 4 iter, RF 6 iter, XGB 8 iter, cv=2, tune trên 50k rows) + refit full; RANDOM_STATE=42; lưu `{logistic_regression,logistic_scaler,random_forest,xgboost}.pkl`, `feature_columns.json`, `training_results.json`
- ML evaluate: `ml/evaluate.py` — test set, lưu `{model}_eval.png`, `evaluation_results.pkl`, `evaluation_summary.csv`
- ML predict: `ml/predict.py` — test.parquet + recovery transaction_id bằng replay Phase 15 split (random_state=42) với safety gate is_fraud 88,581/88,581; TRUNCATE + insert `marts.predictions`; lưu `prediction_metrics.{pkl,json}`
- SHAP: `ml/shap_explain.py` — sample 5,000, lưu `shap_summary.png`, `shap_bar.png`, `shap_individual_{0,100,500}.png`, `top_features.csv`
- API: `/health`, `/ready`, `/predict`, `/transactions/{id}`, `/transactions/predictions/top`
