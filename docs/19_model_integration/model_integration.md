# PHASE 19 — Model Integration

**Trạng thái: COMPLETED AND VERIFIED** — mọi tiêu chí nghiệm thu có bằng chứng thực tế (mục 6–9).

## 1. MỤC TIÊU VÀ PHẠM VI

Hoàn thành pipeline tích hợp mô hình ML với Data Warehouse:

1. Phát hiện và load đúng mô hình đã huấn luyện
2. Load đúng feature list và test dataset từ Phase 15–17
3. Tạo xác suất gian lận và nhãn dự đoán cho từng giao dịch trong test set
4. Lưu kết quả vào bảng `marts.predictions` trong PostgreSQL
5. Tính chỉ số đánh giá từ kết quả dự đoán thực tế
6. Xác minh dữ liệu bằng Python và SQL
7. Lưu metrics và cập nhật tài liệu
8. Giữ tương thích với các phase trước, chuẩn bị schema cho Phase 20

**Không trong phạm vi:** triển khai dashboard (Phase 20), huấn luyện lại model, thay đổi test split.

---

## 2. KIỂM TRA REPOSITORY TRƯỚC KHI SỬA

### 2.1 Git

`git` không có trên máy phát triển và project không phải git repo → không có git status/diff. Kiểm soát thay đổi bằng file system và evidence log (`evidence/phase_19/`).

### 2.2 Model artifacts (`ml/models`)

| File | Size | Ghi chú |
|------|------|---------|
| `xgboost.pkl` | 562,233 B | ✅ model cần tích hợp (Phase 16, XGBClassifier) |
| `feature_columns.json` | 22,680 B | ✅ 1,014 feature columns (JSON array — load bằng `json.load`, **không phải** `joblib.load`) |
| `logistic_regression.pkl` | 4,907 B | baseline |
| `logistic_scaler.pkl` | 43,799 B | scaler **chỉ cho Logistic Regression** — XGBoost không dùng |
| `random_forest.pkl` | 92,427,993 B | Phase 16 |
| `training_results.json` | 1,374 B | val metrics Phase 16 |

⚠️ Kế hoạch ban đầu dùng `xgb_model.pkl` / `feature_cols.pkl` / `scaler.pkl` — **các file này không tồn tại**.

### 2.3 Test data (`ml/data`)

| File | Size | Ghi chú |
|------|------|---------|
| `test.parquet` | 13,708,168 B | 88,581 rows × 1,015 cols (1,014 features + `is_fraud`) |
| `train.parquet` | 60,344,978 B | 413,378 rows |
| `val.parquet` | 13,749,304 B | 88,581 rows |
| `feature_metadata.json` | 27,067 B | metadata Phase 15 |

⚠️ `test.parquet` **không có `transaction_id`** — Phase 15 (`ml/features/prepare.py:304-324`) drop ID column khi lưu processed data. Xử lý ở mục 4.3.

### 2.4 Containers (`docker compose ps`)

| Container | Status | Ghi chú |
|-----------|--------|---------|
| `fraud_dw_postgres` (postgres:15-alpine) | Up (healthy), :5432 | ⚠️ **không phải** server mà host kết nối tới (mục 2.5) |
| `fraud_dw_airflow` | Up, :8080 | |
| `fraud_dw_api` | **Restarting (loop)** | `uvicorn: Permission denied` trong image — lỗi infra, không ảnh hưởng Phase 19 (predict.py chạy từ host) |

### 2.5 PostgreSQL thực tế — HAI instance riêng biệt

Phát hiện quan trọng nhất của bước kiểm tra:

| Instance | Version | data_directory | Nội dung |
|----------|---------|----------------|----------|
| **Windows PostgreSQL** (localhost:5432, PID 8140) — **đích đến thực tế của `.env`** | 18.3 | `C:/Program Files/PostgreSQL/18/data` | `marts.dim_date`, `marts.dim_device`, `marts.dim_product`, **`marts.fact_transactions` (590,540 rows)**, `marts.predictions` (Phase 19 tạo), `raw.identity`, `raw.transactions`, `staging.stg_*` |
| Docker `fraud_dw_postgres` | 15-alpine | `/var/lib/postgresql/data` | chỉ `raw.identity` (144,233 rows) + views `stg_identity` |

- Port 5432 trên host đang được Windows PostgreSQL giữ → kết nối `localhost:5432` (`.env`: `POSTGRES_HOST=localhost`) đi vào **Windows PostgreSQL 18.3** — cùng server mà Phase 15 đã đọc `marts.fact_transactions`.
- `docker exec fraud_dw_postgres psql ...` inspects **docker instance** — không thấy `marts.predictions` dù pipeline ghi thành công. Đây là bình thường: hai instance riêng biệt.
- **Hệ quả:** `marts.fact_transactions` còn tồn tại → có thể phục hồi `transaction_id` (mục 4.3).

---

## 3. KIẾN TRÚC PREDICTION PIPELINE

```
ml/data/test.parquet (88,581 × 1,015)
        │
        ▼
load_model_and_data()          ml/models/feature_columns.json (1,014 cols)
        │                        ml/models/xgboost.pkl (XGBClassifier)
        ▼
build_feature_matrix()         bool→int8 TRƯỚC dtype filter; giữ nguyên thứ tự
        │                       cột theo feature_columns.json; inf→NaN
        ▼
recover_transaction_ids()      replay split Phase 15 (stratified 70/15/15,
        │                       random_state=42) trên marts.fact_transactions
        │                       + verification gate: is_fraud phải khớp
        │                       phần tử với parquet (88,581/88,581)
        ▼
predict()                      predict_proba(X)[:, 1] (lớp fraud),
        │                       threshold = 0.5
        ▼
ensure_predictions_table()     DDL tường minh (KHÔNG if_exists='replace')
        ▼
save_predictions()             to_sql(if_exists='append', chunksize=10000)
        ▼
verify_in_db()                 SQL verification trong pipeline
        ▼
calculate_metrics()            metrics từ dự đoán thực tế
        ▼
save_metrics()                 ml/models/prediction_metrics.{pkl,json}
```

File: `ml/predict.py` (632 dòng). Script dùng `Path(__file__).resolve().parent` nên chạy được từ mọi cwd; DB URL dựng từ env vars (convention `ingestion/load_raw.py`) — **không hard-code mật khẩu**.

---

## 4. QUY TRÌNH XỬ LÝ FEATURE VÀ DỮ LIỆU

### 4.1 Load artifact

- Model: `joblib.load(ml/models/xgboost.pkl)` — XGBClassifier, sklearn interface.
- Feature list: `json.load(ml/models/feature_columns.json)` — JSON array 1,014 tên cột.
- **Không load scaler**: chỉ Logistic Regression dùng `logistic_scaler.pkl`; XGBoost Phase 16 huấn luyện trên feature matrix đã preprocessing trực tiếp (xem `ml/train.py`, `ml/models/training_results.json`).

### 4.2 Feature matrix (`build_feature_matrix`)

Tái tạo đúng đầu vào lúc huấn luyện:

1. Chọn cột theo `feature_columns.json` — **thứ tự cột khớp lúc train** (XGBClassifier lưu `feature_names_in_`).
2. Convert bool → `int8` **trước** khi `select_dtypes(["number"])` — tránh drop feature hợp lệ (lỗi của kế hoạch cũ: `select_dtypes(['int64','float64'])` trước khi check bool).
3. Assert `X_test.shape[1] == 1,014` — fail loudly nếu có training/serving skew.
4. `inf`/`-inf` → NaN (XGBoost xử lý NaN natively). **Không** tự điền NULL bằng 0, **không** loại feature.

### 4.3 Phục hồi transaction_id (vì parquet không có ID)

Phase 15 (`ml/features/prepare.py:143-177`) tạo test set bằng stratified split deterministic:

```python
train_df, temp_df = train_test_split(
    df, test_size=0.30, stratify=df["is_fraud"], random_state=42)
val_df, test_df = train_test_split(
    temp_df, test_size=0.5, stratify=temp_df["is_fraud"], random_state=42)
```

với `df = SELECT t.* FROM marts.fact_transactions` (590,540 rows, 590,540 distinct transaction_id, fraud rate 3.499%). Split deterministic với cùng input + `random_state=42` → replay trên cùng fact table cho đúng tập test và đúng thứ tự. Parquet test row *i* ↔ replayed test row *i*.

**Verification gate (bắt buộc trước khi dùng):** dãy `is_fraud` phục hồi phải bằng `parquet.is_fraud` từng phần tử. Kết quả thực tế: **88,581/88,581 khớp** + 88,581 distinct + 0 NULL. Bất kỳ mismatch nào → `ValueError` và abort **trước khi ghi DB**.

### 4.4 Prediction

- `y_pred_proba = model.predict_proba(X_test)[:, 1]` — lớp 1 = `is_fraud=1`, đúng lớp gian lận.
- `threshold = 0.5` (mặc định; không phase trước chọn threshold khác — Phase 16/17 đều dùng 0.5).
- Xác suất hữu hạn, ∈ [0, 1] (đã verify: min 0.004984, max 0.998232).

---

## 5. THIẾT KẾ BẢNG `marts.predictions`

### 5.1 DDL

```sql
CREATE TABLE marts.predictions (
    prediction_id      INTEGER PRIMARY KEY,
    transaction_id     BIGINT NOT NULL,
    model_version      TEXT NOT NULL,
    is_fraud_actual    INTEGER NOT NULL,
    is_fraud_predicted INTEGER NOT NULL,
    fraud_probability  DOUBLE PRECISION NOT NULL,
    threshold          DOUBLE PRECISION NOT NULL,
    predicted_at       TIMESTAMPTZ NOT NULL,
    UNIQUE (transaction_id, model_version)
);
```

### 5.2 Quyết định khóa duy nhất

Unique constraint trên **(transaction_id, model_version)**, **không phải** chỉ `transaction_id`. Lý do: trong thiết kế tương lai, một giao dịch có thể được dự đoán nhiều lần theo các model version khác nhau — unique chỉ trên `transaction_id` sẽ vô cấm lưu lịch sử đó. Với phạm vi đồ án hiện tại (một model version, một test set), composite unique vẫn ngăn ghi trùng khi chạy lại. `prediction_id` là surrogate key.

### 5.3 Ghi dữ liệu an toàn

- **Không** dùng `to_sql(if_exists="replace")` (có thể xóa bảng, constraint, index hiện có).
- DDL tường minh qua `CREATE SCHEMA IF NOT EXISTS` / `CREATE TABLE`.
- Nếu table tồn tại nhưng thiếu cột mới (`transaction_id` hoặc `model_version`) → **DROP tường minh, có log**, rồi recreate (chỉ áp dụng với bảng Phase 19 tạo, không phải bảng marts hiện hữu).
- Nếu table đầy đủ schema và có rows → **TRUNCATE tường minh, có log** rồi insert (re-run pipeline deterministic là có chủ đích).
- Insert qua `to_sql(if_exists="append", chunksize=10000, method="multi")`.
- **Không** sửa `marts.fact_transactions` hay bảng marts hiện hữu khác.

### 5.4 Cấu hình kết nối

- `.env`: `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `POSTGRES_HOST=localhost`, `POSTGRES_PORT=5432` — load qua `python-dotenv`, dựng URL bằng `sqlalchemy.engine.URL.create` (an toàn với mật khẩu có ký tự đặc biệt `@`).
- **Không hard-code secret** trong source code hay log (đã scan: no hardcoded secrets).
- Script chạy trên Windows host → `localhost:5432` là đúng (Windows PostgreSQL 18.3). Nếu chạy trong container thì phải dùng hostname service `postgres` trong Docker network — không phải trường hợp này.

---

## 6. CHẠY CHƯƠNG TRÌNH VÀ KẾT QUẢ THỰC TẾ

### 6.1 Cách chạy

```bash
.venv\Scripts\Activate.ps1
.venv\Scripts\python.exe ml\predict.py              # pipeline chính
.venv\Scripts\python.exe ml\verify_predictions.py   # SQL verification standalone
.venv\Scripts\python.exe -m pytest ml/tests -v      # automated tests
```

Chạy từ **root project** `C:\Users\Administrator\Documents\ecommerce-fraud-dw`.

### 6.2 Run #1 (tạo bảng với schema đầy đủ)

Log: `evidence/phase_19/execution_log.txt`

```
Loading test data...
Test rows    : 88,581
Test columns : 1,015
Features     : 1,014
Loading XGBoost model...

Actual fraud rate: 3.4985%
Recovering transaction_id (replaying Phase 15 split)...
Base fact rows: 590,540
Replay split: train=413,378 val=88,581 test=88,581
is_fraud verification: 88,581 / 88,581 rows match
transaction_id recovered and verified: 88,581 distinct, 0 NULLs
Running predictions...
Predicted fraud rate (threshold=0.5): 7.7714%
marts.predictions exists WITHOUT ['model_version'] (legacy schema).
Dropping it explicitly to recreate with the full schema...
Created marts.predictions with full schema.
Saving predictions to marts.predictions...
```

### 6.3 Run #2 — idempotency (chạy lại có kiểm soát)

Log: `evidence/phase_19/execution_log_rerun.txt`

```
marts.predictions already exists with 88,581 rows
Truncating explicitly before insert...
Row count: 88,581
Duplicate (transaction_id, model_version) pairs: 0
ROC-AUC : 0.917245
PR-AUC  : 0.600815
>>> Predictions saved to marts.predictions (88,581 rows)
```

→ Chạy lại an toàn: row count không đổi (88,581), 0 duplicate, metrics identical (pipeline deterministic).

---

## 7. SQL VERIFICATION (kết quả thật, thực thi qua `ml/verify_predictions.py`)

Log đầy đủ: `evidence/phase_19/sql_verification.txt`

**1. Tổng số bản ghi:** `total_rows = 88,581` ✅

**2. Duplicate (transaction_id, model_version):** empty — 0 bản ghi trùng ✅

**3. NULL và probability không hợp lệ:**

| null_ids | null_model_versions | null_probabilities | invalid_probabilities | null_actuals | null_predictions |
|----------|---------------------|--------------------|-----------------------|--------------|------------------|
| 0 | 0 | 0 | 0 | 0 | 0 |

**4. Thật vs dự đoán:**

| is_fraud_actual | is_fraud_predicted | n | avg_probability |
|-----------------|--------------------|----|-----------------|
| 0 | 0 | 80,798 | 0.141395 |
| 0 | 1 | 4,684 | 0.639542 |
| 1 | 0 | 899 | 0.270944 |
| 1 | 1 | 2,200 | 0.838343 |

**5. Top 10 xác suất gian lận cao nhất** (`model_version='xgboost-v1-phase16'`, ORDER BY fraud_probability DESC, transaction_id):

| transaction_id | is_fraud_actual | is_fraud_predicted | fraud_prob |
|----------------|-----------------|--------------------|------------|
| 3122167 | 1 | 1 | 0.9982 |
| 3127114 | 1 | 1 | 0.9971 |
| 3524493 | 1 | 1 | 0.9968 |
| 3224515 | 1 | 1 | 0.9968 |
| 3360008 | 1 | 1 | 0.9968 |
| 3516426 | 1 | 1 | 0.9967 |
| 3231532 | 1 | 1 | 0.9967 |
| 3231534 | 1 | 1 | 0.9967 |
| 3085461 | 1 | 1 | 0.9966 |
| 3395166 | 1 | 1 | 0.9966 |

**6. Model version / threshold:** 1 version `xgboost-v1-phase16`, threshold 0.5, 88,581 rows.

**7. JOIN integrity vs `marts.fact_transactions`:** `matched_rows = 88,581`, `fraud_flag_match = 88,581` — mọi prediction row join được giao dịch thật và cờ fraud khớp 100% → khóa giao dịch đúng. ✅

**8. Columns/types:** prediction_id integer, transaction_id bigint, model_version text, is_fraud_actual integer, is_fraud_predicted integer, fraud_probability double precision, threshold double precision, predicted_at timestamptz — all `is_nullable = NO`.

**9. Constraints:** PRIMARY KEY (prediction_id), UNIQUE (transaction_id, model_version), 8 NOT NULL CHECK.

---

## 8. KẾT QUẢ METRICS THỰC TẾ

Tính từ dự đoán thực tế trên test set 88,581 (artifact `ml/models/prediction_metrics.json`):

| Metric | Giá trị thực tế |
|--------|------------------|
| ROC-AUC | **0.917245** |
| PR-AUC (`average_precision_score` — diện tích dưới precision-recall curve) | **0.600815** |
| Precision | 0.319582 |
| Recall | 0.709906 |
| F1 | 0.440749 |
| Confusion matrix | TN=80,798 / FP=4,684 / FN=899 / TP=2,200 |
| Actual fraud rate | 3.4985% (3,099) — khớp Phase 15 |
| Predicted fraud rate | 7.7714% (6,884) |
| Threshold | 0.5 |
| Model version | xgboost-v1-phase16 |

Classification report:

```
              precision    recall  f1-score   support

   Non-Fraud       0.99      0.95      0.97     85482
       Fraud       0.32      0.71      0.44      3099

    accuracy                           0.94     88581
   macro avg       0.65      0.83      0.70     88581
weighted avg       0.97      0.94      0.95     88581
```

**Nhất quán Phase 17:** cùng model, test set và threshold → ROC-AUC/PR-AUC/Precision/Recall/F1 và confusion matrix khớp chính xác Phase 17 (XGBoost: 0.917245 / 0.600815 / 0.319582 / 0.709906 / 0.440749). Đây là bằng chứng chéo giữa pipeline đánh giá (Phase 17) và pipeline tích hợp (Phase 19).

⚠️ **Bảng "Expected Output" trong kế hoạch ban đầu (ROC-AUC 0.9785, PR-AUC 0.6234, predicted fraud rate 0.0325) là số tham khảo, KHÔNG phải kết quả thực tế và không được đưa vào báo cáo.** Metrics trên được tính từ dự đoán thực tế.

---

## 9. KẾT QUẢ KIỂM THỬ

`ml/tests/test_predict.py` — 13 tests (pytest 9.1.1, Python 3.14.0):

```
ml/tests/test_predict.py::test_load_model_and_data PASSED                              [ 7%]
ml/tests/test_predict.py::test_load_model_and_data_rejects_missing_model PASSED       [15%]
ml/tests/test_predict.py::test_load_model_and_data_rejects_unknown_feature PASSED     [23%]
ml/tests/test_predict.py::test_build_feature_matrix_preserves_order_and_types PASSED  [30%]
ml/tests/test_predict.py::test_build_feature_matrix_replaces_inf_with_nan PASSED      [38%]
ml/tests/test_predict.py::test_build_feature_matrix_rejects_dropped_columns PASSED    [46%]
ml/tests/test_predict.py::test_predict_probabilities_and_threshold PASSED             [53%]
ml/tests/test_predict.py::test_predict_real_model_proba_bounds PASSED                 [61%]
ml/tests/test_predict.py::test_transaction_id_recovery PASSED                         [69%]
ml/tests/test_predict.py::test_metrics_calculation PASSED                             [76%]
ml/tests/test_predict.py::test_metrics_single_class_raises PASSED                     [84%]
ml/tests/test_predict.py::test_postgres_roundtrip_scratch_table PASSED                [92%]
ml/tests/test_predict.py::test_prediction_metrics_artifact PASSED                     [100%]

======================== 13 passed in 88.99s (0:01:28) ========================
```

Log: `evidence/phase_19/test_results.txt`

Phân loại:
- **Unit tests (8):** feature order/dtype, inf→NaN, reject dropped columns, threshold classification (FakeModel), metrics calculation (known case), single-class raises, missing model artifact, unknown feature.
- **Integration tests (5):** load artifact thật, predict model thật trên 88,581 rows (probability bounds), transaction_id recovery (DB read-only), PostgreSQL roundtrip trên **scratch table** `marts_tests.scratch_roundtrip` (tạo → insert → verify → unique reject → drop; **không chạm `marts.predictions`**), metrics artifact.
- **Idempotency:** verified bằng controlled double-run của pipeline thật (mục 6.3), không phải bằng cách ghi đè dữ liệu thật trong test.

---

## 10. GIỚI HẠN VÀ GIẢ ĐỊNH

1. **Hai PostgreSQL instance:** Windows PostgreSQL 18.3 (localhost:5432 — đang dùng, có full DW) và docker `fraud_dw_postgres` 15-alpine (chỉ có `raw.identity`). Phase 20 (Metabase) phải kết nối đúng Windows instance. Docker compose vẫn hiển thị port mapping 5432 nhưng thực tế host port thuộc về Windows PostgreSQL.
2. **`fraud_dw_api` restart loop** (`uvicorn: Permission denied` trong image) — lỗi Docker image, không thuộc Phase 19; cần sửa Dockerfile/image riêng.
3. **transaction_id phục hồi bằng replay split** — dựa trên giả định `SELECT t.* FROM marts.fact_transactions` trả về thứ tự ổn định (bảng không đổi sau Phase 15). Verification gate (is_fraud khớp 88,581/88,581) bảo đảm đúng trước khi ghi; nếu fact table thay đổi thứ tự, pipeline abort an toàn.
4. **Threshold 0.5** là mặc định; không có threshold nào được tối ưu và ghi nhận ở phase trước. Recall 0.71 / Precision 0.32 phản ánh trade-off ở threshold này (xem phân tích Phase 17).
5. **`marts.predictions` chỉ chứa kết quả test set** (88,581 rows) của một model version — không phải bảng dự đoán production streaming.
6. Metrics artifact lưu cả `.pkl` (convention Phase 16–18) và `.json` (readable, ưu tiên cho báo cáo/tích hợp Phase 20).

---

## 11. HƯỚNG TÍCH HỢP SANG PHASE 20

- Metabase kết nối **Windows PostgreSQL 18.3**: host `localhost` (hoặc `host.docker.internal` nếu Metabase chạy trong Docker), port 5432, db `ecommerce_fraud_dw`, user/pass từ `.env`.
- Các bảng nên dùng cho dashboard: `marts.predictions` (dự đoán + probability), `marts.fact_transactions` (ground truth), join trên `transaction_id`.
- Metabase service đang bị comment trong `docker-compose.yml` (mục 75–88) — bỏ comment để chạy Phase 20.
- Gợi ý metrics cho dashboard: fraud rate thật vs dự đoán, confusion matrix, phân phối fraud_probability, top-N probability.

---

## 12. EVIDENCE FILES

```
ml/
├── predict.py                        # Pipeline Phase 19 (632 dòng)
├── verify_predictions.py             # SQL verification standalone
├── tests/
│   ├── conftest.py                   # sys.path setup cho pytest
│   └── test_predict.py               # 13 automated tests
├── models/
│   ├── prediction_metrics.pkl        # Metrics (joblib)
│   └── prediction_metrics.json       # Metrics (readable)

evidence/phase_19/
├── execution_log.txt                 # Run #1
├── execution_log_rerun.txt           # Run #2 (idempotency)
├── test_results.txt                  # pytest output
└── sql_verification.txt              # 9 SQL verification queries

PostgreSQL (Windows instance, localhost:5432):
└── marts.predictions                 # 88,581 rows, schema mục 5.1
```

---

## 13. LIÊN HỆ

- Trước: [PHASE 18 — SHAP/XAI](../18_shap/shap_explanation.md)
- Sau: [PHASE 20 — Metabase Dashboard](../20_dashboard/metabase_dashboard.md)

*Cập nhật: 09/10/2026 | Version: 3.1 (kết quả thực nghiệm, verified)*
