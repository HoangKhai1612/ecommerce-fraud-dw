# PHASE 24 — End-to-End Pipeline Implementation & Verification

**Trạng thái: HOÀN THÀNH (có bằng chứng thực tế)**
*Cập nhật: 13/10/2026*

---

## 1. MỤC TIÊU

Chạy toàn bộ pipeline end-to-end với bằng chứng thực tế từng bước:

1. PostgreSQL sẵn sàng
2. Ingestion (CSV → RAW)
3. Xác minh RAW
4. dbt staging
5. dbt marts
6. dbt tests (data quality gate)
7. Xác minh chất lượng DW
8. Huấn luyện 3 model (Logistic Regression, Random Forest, XGBoost)
9. Đánh giá model trên test set
10. Batch prediction → `marts.predictions`
11. SHAP explainability
12. FastAPI health/readiness/prediction
13. Metabase health + kết nối DW
14. Airflow webserver/scheduler/DAG

---

## 2. KIẾN TRÚC VÀ LUỒNG PIPELINE

```text
[data/raw/*.csv]  (KHÔNG CÓ trên hệ thống — xem mục 8)
        ↓ (1) ingestion/load_raw.py — GATE: chỉ chạy khi có CSV
[raw.transactions, raw.identity]  (đã có: 590,540 / 144,233)
        ↓ (2) dbt run --select staging   [trong Airflow container]
[staging.stg_transactions, staging.stg_identity]  (view)
        ↓ (3) dbt run --select marts     [trong Airflow container]
[marts.fact_transactions + dim_product/dim_device/dim_date]  (table)
        ↓ (4) dbt test                   [trong Airflow container]
[38 data-quality tests: not_null, unique, accepted_values, relationships]
        ↓ (5) verify_quality (SQL integrity checks)
        ↓ (6) ml/train.py                [host .venv]
[logistic_regression.pkl, random_forest.pkl, xgboost.pkl, feature_columns.json, training_results.json]
        ↓ (7) ml/evaluate.py             [host .venv]
[{model}_eval.png, evaluation_results.pkl, evaluation_summary.csv]
        ↓ (8) ml/predict.py              [host .venv]
[marts.predictions (88,581 rows), prediction_metrics.json]
        ↓ (9) ml/shap_explain.py         [host .venv]
[shap_summary.png, shap_bar.png, shap_individual_*.png, top_features.csv]
        ↓ (10) HTTP checks
[FastAPI :8000, Metabase :3000, Airflow :8080]
```

**Quy tắc kết nối:** ML scripts chạy trên host `.venv` (Python 3.14) kết nối DW tại `localhost:5432` (Windows PostgreSQL 18). dbt chạy trong Airflow container (Python 3.12) — xem mục 8.

---

## 3. ĐIỀU KIỆN MÔI TRƯỜNG

| Yêu cầu | Thực tế |
|---|---|
| Python venv | `.venv` (Python 3.14.0), deps: pandas, sklearn, xgboost, shap, matplotlib, sqlalchemy, psycopg2, dotenv, pytest |
| dbt | 1.8.2 — **chỉ chạy trong Airflow container** (host dbt CLI lỗi protobuf 4.25.9 + Python 3.14) |
| PostgreSQL | Windows PostgreSQL 18.3 service (`postgresql-x64-18`), host 5432, DB `ecommerce_fraud_dw` |
| Docker | 29.6.2 / Compose v5.3.1, 5 services đang chạy (Phase 23) |
| Ollama | native host 11434, model `llama3:latest` (cho AI Assistant, không cần cho pipeline ML) |
| Dữ liệu ML | `ml/data/{train,val,test}.parquet` (413,378 / 88,581 / 88,581 rows, 1,014 features) |

---

## 4. CÁCH CHẠY TỪNG BƯỚC

```powershell
cd C:\Users\Administrator\Documents\ecommerce-fraud-dw
.venv\Scripts\Activate.ps1

# 1. PostgreSQL readiness
# (runner check_postgres — SELECT 1 qua .env)

# 2. Ingestion — CHỈ chạy khi data/raw/*.csv tồn tại
#    Runner tự GATE: thiếu CSV -> SKIPPED (không bao giờ DROP raw tables)
python ingestion/load_raw.py

# 3-5. dbt — chạy trong Airflow container (host dbt CLI bị lỗi)
docker exec fraud_dw_airflow bash -c "cd /opt/airflow/dbt && dbt run --select staging --profiles-dir ."
docker exec fraud_dw_airflow bash -c "cd /opt/airflow/dbt && dbt run --select marts --profiles-dir ."
docker exec fraud_dw_airflow bash -c "cd /opt/airflow/dbt && dbt test --profiles-dir ."

# 6-9. ML
python ml/train.py        # ~8 phút (RandomizedSearchCV + refit, RANDOM_STATE=42)
python ml/evaluate.py     # ~10 giây
python ml/predict.py      # ~5 phút (recovery transaction_id + write marts.predictions)
python ml/shap_explain.py # ~10 giây
```

---

## 5. CÁCH CHẠY FULL PIPELINE

```powershell
# Chạy tất cả bước (có GATE ingestion, có timeout, có evidence)
.venv\Scripts\python.exe run_pipeline.py --evidence-dir evidence\phase_24

# Chạy subset bước
.venv\Scripts\python.exe run_pipeline.py --steps dbt_staging,dbt_marts,dbt_tests,verify_quality

# Xem kết quả
type evidence\phase_24\pipeline_summary.json
type evidence\phase_24\logs\step_ml_train.log
```

`run_pipeline.py` (tạo mới):
- 14 bước, mỗi bước qua `subprocess` với **kiểm tra exit code** + **timeout** (dbt 900s, train 7200s, predict 1800s)
- Dừng tại bước FAIL đầu tiên, không đánh dấu thành công khi chưa chạy
- Đường dẫn tuyệt đối (không phụ thuộc CWD), tương thích Windows
- Không chứa credential (đọc từ `.env` qua các script con)
- **Ingestion safety gate:** `load_raw.py` DROP+CREATE raw tables, nên runner từ chối chạy khi thiếu CSV nguồn — bảo toàn dữ liệu RAW hiện có
- Log từng bước → `evidence/phase_24/logs/step_<name>.log`, tóm tắt → `pipeline_summary.json`

---

## 6. CÁCH CHẠY E2E TESTS

```powershell
# Verification tests (32 tests độc lập, đọc state thật, không đổi dữ liệu)
.venv\Scripts\python.exe -m pytest tests/test_end_to_end.py -v

# Full pipeline test (opt-in: thực thi run_pipeline.py, bao gồm ML training)
.venv\Scripts\python.exe -m pytest tests/test_end_to_end.py --run-pipeline
```

Thiết kế test (C1-C9 theo spec):
- **C1 Infrastructure**: PostgreSQL, schemas, Airflow/Metabase/Ollama health
- **C2 Ingestion**: RAW counts, primary key unique, **ingestion gate test** (chạy real step, assert SKIPPED khi thiếu CSV)
- **C3 dbt**: staging/fact counts, dimension counts, FK integrity (orphan semantics theo dbt relationships test: chỉ xét NON-NULL FK), **chạy real `dbt test`** trong container
- **C4 ML**: artifacts tồn tại + non-empty, `training_results.json` có 3 model với metrics ∈ [0,1]
- **C5 Prediction**: schema `marts.predictions`, domain probability [0,1], distinct transaction_id, FK đến fact, **batch vs online consistency** (cùng model_version)
- **C6 SHAP**: artifacts PNG hợp lệ (magic bytes)
- **C7 FastAPI**: /health, /ready, POST /predict (valid + 422 invalid), GET /transactions/{id}, /transactions/predictions/top
- **C8 Metabase**: /api/health + DW connection đăng ký trong `metabase_db.metabase_database` (dedicated connection — PostgreSQL không hỗ trợ cross-database query)
- **C9 Airflow**: DAG tồn tại + unpaused, DagBag import errors = 0, task wiring đầy đủ
- Tất cả tests **độc lập** (không phụ thứ tự); fixture session-scoped cho DB engine

---

## 7. KẾT QUẢ THỰC TẾ (13/10/2026)

### 7.1 Full pipeline (`run_pipeline.py`)

**PASS=13, SKIPPED=1, FAIL=0** — `evidence/phase_24/pipeline_summary.json`

| Bước | Trạng thái | Thời gian | Bằng chứng |
|---|---|---|---|
| check_postgres | PASS | 0.5s | SELECT 1 = 1 |
| ingestion | **SKIPPED** | — | CSVs nguồn không tồn tại (safety gate — xem mục 8) |
| verify_raw | PASS | 0.5s | raw.transactions=590,540; raw.identity=144,233 |
| dbt_staging | PASS | 4.1s | PASS=2 view models |
| dbt_marts | PASS | 86.4s | PASS=4 table models |
| dbt_tests | PASS | 107.2s | **PASS=38 WARN=0 ERROR=0 SKIP=0 TOTAL=38** |
| verify_quality | PASS | 2.3s | staging=fact=590,540; fraud=20,663 (3.499%); orphan keys=0 |
| ml_train | PASS | 479.7s | 3 models, 1,014 features, best=XGBoost |
| ml_evaluate | PASS | 8.2s | 3 × {model}_eval.png + evaluation_summary.csv |
| ml_predict | PASS | 301.6s | marts.predictions=88,581 rows; is_fraud recovery verified 88,581/88,581 |
| ml_shap | PASS | 9.7s | 5 PNGs + top_features.csv |
| api_check | PASS | 4.5s | /health /ready /predict /transactions đều 200 |
| metabase_check | PASS | 1.6s | healthy; `ecommerce_fraud_dw` đăng ký trong metabase_db |
| airflow_check | PASS | 0.7s | scheduler+metadb healthy; DAG `fraud_dw_pipeline` hiện diện |

### 7.2 Số dòng (sau pipeline — `evidence/phase_24/row_counts.json`)

| Bảng | Số dòng |
|---|---|
| raw.transactions | 590,540 |
| raw.identity | 144,233 |
| staging.stg_transactions | 590,540 |
| staging.stg_identity | 144,233 |
| marts.fact_transactions | 590,540 |
| marts.fact_transactions (is_fraud=1) | 20,663 (3.499%) |
| marts.dim_product / dim_device / dim_date | 22 / 1,939 / 183 |
| marts.predictions | 88,581 (distinct txn 88,581; prob [0.00498, 0.99823]) |

### 7.3 Model metrics (đo lường thực tế)

**Training (validation set)** — `ml/models/training_results.json`:

| Model | ROC-AUC | PR-AUC | Precision | Recall | F1 |
|---|---|---|---|---|---|
| Logistic Regression | 0.869964 | 0.485851 | 0.817424 | 0.284516 | 0.422111 |
| Random Forest | 0.912991 | 0.645182 | 0.925865 | 0.362581 | 0.521094 |
| **XGBoost** (best) | **0.916026** | 0.591256 | 0.316045 | 0.713548 | 0.438063 |

**Evaluation (held-out test set)** — `ml/models/evaluation_summary.csv`:

| Model | ROC-AUC | PR-AUC | Precision | Recall | F1 | F1-macro |
|---|---|---|---|---|---|---|
| **XGBoost** | **0.917245** | 0.600815 | 0.319582 | 0.709906 | 0.440749 | 0.703677 |
| Random Forest | 0.915310 | 0.650867 | 0.944210 | 0.360439 | 0.521719 | 0.754936 |
| Logistic Regression | 0.872100 | 0.486336 | 0.820728 | 0.283640 | 0.421583 | 0.703820 |

**Prediction (test set, threshold=0.5)** — `ml/models/prediction_metrics.json`:
- 88,581 predictions; actual fraud 3,099 (3.50%); predicted fraud 6,884 (7.77%)
- Confusion matrix: [[80798, 4684], [899, 2200]]
- ROC-AUC 0.917245, PR-AUC 0.600815, F1 0.440749

**SHAP top features** — `ml/models/top_features.csv`:
`num__c14` (0.186), `num__transaction_amt` (0.177), `num__v258` (0.158), `num__c1` (0.150), `num__v70` (0.148)

### 7.4 E2E tests

**32 passed, 1 skipped** (skipped = `TestFullPipeline::test_full_pipeline`, opt-in qua `--run-pipeline`) — `evidence/phase_24/pytest_results.txt`

---

## 8. LỖI ĐÃ PHÁT HIỆN VÀ CÁCH XỬ LÝ

| # | Lỗi | Nguyên nhân | Xử lý |
|---|---|---|---|
| 1 | **Ingestion không thể chạy**: `data/raw/` không tồn tại, CSVs nguồn (`train_transaction.csv`, `train_identity.csv`) không có trong zip dự án và không tìm thấy trên đĩa. DAG `fraud_dw_pipeline` run gần nhất cũng failed tại `ingest_raw_data` (try=2) | Thiếu dữ liệu nguồn trong môi trường | Runner **GATE** ingestion: thiếu CSV → SKIPPED thay vì chạy `load_raw.py` (sẽ DROP raw tables → mất 590,540+144,233 rows). RAW tables đã có sẵn và được verify riêng (mục 7.2). **Đánh giá: SKIPPED, không phải PASS** — xem mục 9 |
| 2 | dbt CLI trên host `.venv` lỗi `TypeError: Metaclasses with custom tp_new are not supported` | protobuf 4.25.9 không tương thích Python 3.14 | Chạy dbt trong Airflow container (Python 3.12, dbt 1.8.2) qua `docker exec` — đúng nơi production DAG chạy dbt |
| 3 | `verify_quality` FAIL ban đầu: "orphan product_key/device_key found" | Bug trong SQL check: LEFT JOIN đếm cả NULL keys (1,577 NULL product_key, 471,919 NULL device_key — đặc điểm dữ liệu hợp lệ: 80% transactions không có identity record) | Sửa semantics theo dbt `relationships` test: chỉ xét NON-NULL FK không có dim match. Kết quả: orphan=0, NULL keys báo cáo riêng (informational) |
| 4 | `query_sql` lỗi `SyntaxError: unterminated string literal` | SQL chứa dấu nháy đơn được embed vào code string `r'''...'''` | Truyền SQL qua `sys.argv` thay vì string embedding |
| 5 | `log_path.relative_to(PROJECT_ROOT)` ValueError khi evidence dir ngoài project | `Path.relative_to` không xử lý đường dẫn ngoài | try/except fallback về absolute path |
| 6 | `pytest_addoption` trong test file bị `ValueError: no option named '--run-pipeline'` | Hook `pytest_addoption` chỉ được gọi từ `conftest.py` | Chuyển vào `tests/conftest.py` |
| 7 | `test_dag_task_dependencies` parse sai task_ids | DagBag log INFO line trên stdout trước print | Lấy last line của stdout |
| 8 | Tài liệu Phase 24 cũ sai: `xgb_model.pkl` (thật: `xgboost.pkl`), DAG `fraud_detection_pipeline` (thật: `fraud_dw_pipeline`), DB_URL hardcode `postgres:postgres`, payload `TransactionID` (thật: `transaction_id`) | Tài liệu viết theo mẫu chưa đối chiếu code | Viết lại tài liệu theo trạng thái thực tế |

---

## 9. GIỚI HẠN CHƯA GIẢI QUYẾT

1. **Ingestion: SKIPPED (BLOCKED bởi dữ liệu nguồn)** — CSVs không có trong môi trường. RAW tables hiện có đã được verify (590,540 / 144,233, PK unique). Để chạy ingestion lại: khôi phục `data/raw/train_transaction.csv` + `train_identity.csv` (590,540 + 144,233 rows) từ nguồn dữ liệu IEEE-CIS Fraud Detection gốc, rồi chạy `python ingestion/load_raw.py` hoặc trigger DAG. **Không thể đánh giá PASS bước ingestion vì bước chưa thực sự thực thi.**
2. **Airflow DAG orchestration chưa hoàn chỉnh end-to-end**: DAG `fraud_dw_pipeline` chỉ orchestrate ingestion → dbt → quality gate. ML training/evaluate/predict/SHAP chạy qua `run_pipeline.py` (host), không phải DAG tasks. Run DAG gần nhất state=failed (tại ingest, do thiếu CSV). Đã ghi nhận khoảng trống này — không tuyên bố DAG orchestration toàn bộ pipeline.
3. **dbt không chạy được trên host `.venv`** (protobuf/Python 3.14) — phải chạy trong container. Nếu muốn chạy host: nâng protobuf ≥5 hoặc dùng Python 3.12 venv riêng.
4. **`marts.predictions` chứa prediction history của model_version `xgboost-v1-phase16`** — pipeline retrain tạo lại model cùng version (deterministic RANDOM_STATE=42); bảng bị TRUNCATE + insert lại theo thiết kế Phase 19.
5. **Docker-local PG (host 5434)** là instance phụ (không chứa marts) — DW chính là Windows PG 18 (xem Phase 23).

---

## 10. BẰNG CHỨNG NGHIỆM THU

| Tiêu chí hoàn thành | Trạng thái | Bằng chứng |
|---|---|---|
| PostgreSQL sẵn sàng | **PASS** | check_postgres PASS; 32/32 infra tests |
| Ingestion thực sự chạy thành công | **SKIPPED** (BLOCKED: thiếu CSV nguồn) | step_ingestion.log: "source CSVs missing"; RAW tables verified riêng |
| RAW được xác minh | **PASS** | verify_raw PASS: 590,540 / 144,233; PK unique=0 dup |
| dbt staging thành công | **PASS** | dbt run --select staging: PASS=2 |
| dbt marts thành công | **PASS** | dbt run --select marts: PASS=4 |
| dbt tests đạt yêu cầu | **PASS** | dbt test: PASS=38 ERROR=0 |
| Data Quality checks đạt yêu cầu | **PASS** | verify_quality PASS: fraud=20,663 (3.499%), orphan FK=0 |
| Ba model huấn luyện thành công | **PASS** | ml_train PASS 479.7s; training_results.json: 3 models, 1,014 features |
| Evaluation thực hiện và lưu kết quả | **PASS** | ml_evaluate PASS; evaluation_summary.csv + 3 PNGs |
| Prediction thực sự chạy và lưu DB | **PASS** | ml_predict PASS 301.6s; marts.predictions=88,581; recovery verified 88,581/88,581 |
| SHAP thực sự chạy và sinh artifact | **PASS** | ml_shap PASS 9.7s; 5 PNGs (magic bytes hợp lệ) + top_features.csv |
| API health/readiness hoạt động | **PASS** | /health 200 ok; /ready 200 ready+database:ok |
| API prediction tested với request hợp lệ | **PASS** | POST /predict 200; xác suất [0,1]; 422 cho request sai |
| Metabase kết nối đúng database | **PASS** | /api/health 200; `ecommerce_fraud_dw` đăng ký trong metabase_db.metabase_database |
| Airflow DAG được xác minh | **PASS (với ghi nhận mục 9.2)** | webserver+scheduler+metadb healthy; DagBag import_errors=0; DAG hiện diện unpaused; run gần nhất failed tại ingest (thiếu CSV) |
| Docker services cần thiết hoạt động | **PASS** | 5 services: postgres/airflow/api/ai-assistant healthy, metabase up |
| E2E tests đạt yêu cầu | **PASS** | 32 passed, 1 skipped (opt-in) |
| Tài liệu và evidence cập nhật | **PASS** | docs/24_end_to_end/end_to_end.md + evidence/phase_24/ (24 files) |

**Kết luận:** 16/18 tiêu chí PASS, 1 SKIPPED (ingestion — thiếu dữ liệu nguồn, không thể thực thi trong môi trường này), 1 PASS có ghi nhận (Airflow DAG tồn tại và healthy nhưng chưa orchestration ML steps). Không có tiêu chí nào bị đánh giá PASS giả tạo.

---

## 11. LIÊN KẾT BẰNG CHỨNG

```
evidence/phase_24/
├── audit_report.md              # Giai đoạn A audit
├── commands_log.md              # Lệnh + exit code
├── files_changed.md             # File tạo mới/sửa đổi
├── pipeline_summary.json        # Tóm tắt pipeline (runner)
├── pytest_results.txt           # Kết quả pytest
├── row_counts.json              # Số dòng RAW/staging/marts/predictions
├── logs/
│   ├── step_check_postgres.log
│   ├── step_ingestion.log          # SKIPPED (gate)
│   ├── step_verify_raw.log
│   ├── step_dbt_staging.log
│   ├── step_dbt_marts.log
│   ├── step_dbt_tests.log          # PASS=38
│   ├── step_verify_quality.log
│   ├── step_ml_train.log
│   ├── step_ml_evaluate.log
│   ├── step_ml_predict.log
│   ├── step_ml_shap.log
│   ├── step_api_check.log
│   ├── step_metabase_check.log
│   └── step_airflow_check.log
└── models_pre_training_backup/  # Artifacts trước retrain
```

---

*Trước: [PHASE 23 — Docker Compose](../23_docker/docker_compose.md)*
*Sau: [PHASE 25 — Testing](../25_testing/testing.md)*

*Cập nhật: 13/10/2026 | Version: 2.0*
