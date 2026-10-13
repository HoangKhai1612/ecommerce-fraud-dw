# PHASE 20 — Metabase Dashboard

**Trạng thái: COMPLETED AND VERIFIED** — mọi tiêu chí có bằng chứng thực tế (mục 8–10).

## 1. MỤC TIÊU VÀ PHẠM VI

Triển khai Metabase dashboard cho hệ thống Data Warehouse phát hiện gian lận:

1. Thêm dịch vụ Metabase vào Docker Compose (v0.49.0), expose `http://localhost:3000`
2. Cấu hình database metadata riêng (`metabase_db`) — không ghi vào bảng nghiệp vụ/schema `marts`
3. Kết nối Metabase tới Data Warehouse `ecommerce_fraud_dw` qua tài khoản đọc riêng `metabase_ro`
4. Xây dựng 5 nhóm phân tích: Overview (4 KPI), Fraud Trend, Device Analysis, Product Analysis, Prediction Results
5. Tạo dashboard `E-commerce Fraud Analytics` và xác minh bằng kết quả thực tế

**Không trong phạm vi:** sửa `fraud_dw_api` (lỗi infra có sẵn), huấn luyện lại model, thay đổi Phase 16–19.

---

## 2. KIỂM TRA HIỆN TRẠNG (trước khi sửa)

### 2.1 Docker

| Container | Status | Ghi chú |
|-----------|--------|---------|
| `fraud_dw_postgres` (postgres:15-alpine) | Up (healthy), :5432 | ⚠️ **không chứa** DW `marts.*` — chỉ có `raw.identity` |
| `fraud_dw_airflow` | Up, :8080 | kết nối tới Windows PG qua `host.docker.internal` |
| `fraud_dw_api` | **Restarting (loop)** | lỗi `uvicorn: Permission denied` trong image — có sẵn từ trước, ngoài phạm vi Phase 20 |
| `fraud_dw_metabase` | — | chưa tồn tại (service bị comment trong `docker-compose.yml`) |

- Port 3000 trống trước khi triển khai.
- Network thực tế: `ecommerce-fraud-dw_fraud_dw_network` (project name `ecommerce-fraud-dw`).
- `.env` đã gitignored (kiểm tra `.gitignore`) — an toàn cho secrets.

### 2.2 Hai PostgreSQL instance

| Instance | Version | Nội dung |
|----------|---------|----------|
| **Windows PostgreSQL** (localhost:5432, PID 8140) — đích đến của `.env` | 18.3 | `ecommerce_fraud_dw` với `marts.*` (full DW), `airflow_db` |
| Docker `fraud_dw_postgres` | 15-alpine | chỉ `raw.identity` |

**Kiểm tra kết nối từ trong Docker network** (bước quan trọng):

```
docker run --rm -e PGPASSWORD=... postgres:15-alpine \
  psql -h host.docker.internal -p 5432 -U postgres -d postgres
=> connectivity-ok | 127.0.0.1
```

Container Docker kết nối tới Windows PG qua `host.docker.internal:5432` **thành công** (cùng pattern Airflow đang dùng — `airflow_db` tồn tại là bằng chứng). `pg_hba.conf` chỉ cho phép loopback, nhưng kết nối từ Docker được server thấy là `127.0.0.1` nên không cần sửa `pg_hba`.

### 2.3 Data Warehouse đã xác minh

`information_schema.columns` trên `ecommerce_fraud_dw`:

| Bảng | Cột chính | Ghi chú |
|------|-----------|---------|
| `marts.fact_transactions` | `transaction_key`, `transaction_id` (bigint), `is_fraud` (smallint), `transaction_dt` (**bigint epoch tương đối**), `transaction_amt` (numeric), `product_key`, `device_key`, `product_cd` (varchar), `device_type` (varchar), `device_info`, 339 cột v*, 38 cột id_, `_loaded_at` | `device_type`, `device_info`, `product_cd` **đã materialize** — không cần join dimension |
| `marts.dim_date` | `date_key` (int, 1..183), `transaction_day`, `day_of_week`, `week_number` | 183 rows — **không có FK** từ fact_transactions |
| `marts.dim_device` | `device_key`, `device_type`, `device_info` | 1,939 rows |
| `marts.dim_product` | `product_key`, `product_cd`, `card4` | 22 rows |
| `marts.predictions` | `prediction_id` (PK), `transaction_id`, `model_version`, `is_fraud_actual`, `is_fraud_predicted`, `fraud_probability` (**double precision, thang 0–1**), `threshold`, `predicted_at` — all NOT NULL, UNIQUE(transaction_id, model_version) | Phase 19 ghi, 88,581 rows |

**Đặc thù dữ liệu (ảnh hưởng SQL):**

- `device_type`: **449,730/590,540 (76%) là NULL** → cần `COALESCE(NULLIF(...), 'Unknown')`
- `product_cd`: chỉ 5 giá trị (C/S/H/R/W), không NULL
- `transaction_dt`: epoch tương đối của dataset (Kaggle convention) → `to_timestamp()` cho 1970-01-02 .. 1970-07-03

**Baseline đối chiếu (truy vấn thật, không dùng số cũ):**

```
total_transactions = 590,540     fraud_count = 20,663
fraud_rate         = 3.4990%     total_amount  = 79,738,980.37
```

Khớp kết quả Phase 15/19.

---

## 3. KIẾN TRÚC TRIỂN KHAI

```
docker-compose.yml
  └─ metabase (metabase/metabase:v0.49.0)
       ├─ MB_DB_*  → metabase_db @ Windows PostgreSQL 18.3 (host.docker.internal:5432)
       │              [metadata: 89 tables — users, collections, cards, dashboards]
       ├─ Port     → 0.0.0.0:3000->3000
       └─ Kết nối DW → ecommerce_fraud_dw @ host.docker.internal:5432
                        với role metabase_ro (CONNECT/USAGE/SELECT trên marts)

Windows PostgreSQL 18.3 (localhost:5432)
  ├─ ecommerce_fraud_dw  ← Data Warehouse (marts.*)
  ├─ metabase_db         ← Metabase metadata (tạo mới Phase 20)
  └─ airflow_db          ← Airflow (có sẵn)
```

**Persistence:** metadata Metabase nằm trong `metabase_db` trên Windows PostgreSQL (persistent trên host) — đây là setup production được Metabase khuyến nghị; không dùng file H2 cục bộ nên không cần volume riêng.

---

## 4. CẤU HÌNH DOCKER VÀ DATABASE METADATA

### 4.1 Service Metabase (`docker-compose.yml`)

```yaml
  metabase:
    image: metabase/metabase:v0.49.0
    container_name: fraud_dw_metabase
    restart: unless-stopped
    environment:
      MB_DB_TYPE: postgres
      MB_DB_DBNAME: metabase_db
      MB_DB_HOST: host.docker.internal
      MB_DB_PORT: 5432
      MB_DB_USER: ${POSTGRES_USER:-postgres}
      MB_DB_PASS: ${POSTGRES_PASSWORD:-postgres}
    ports:
      - "${METABASE_PORT:-3000}:3000"
    extra_hosts:
      - "host.docker.internal:host-gateway"
    depends_on:
      postgres:
        condition: service_healthy
    networks:
      - fraud_dw_network
```

- `depends_on: condition: service_healthy` (không phải depends_on đơn thuần) + Metabase tự retry kết nối metadata DB khi khởi động (log: "Metabase Initialization COMPLETE in 48.6 s").
- `MB_DB_DBNAME: metabase_db` — **không** ghi metadata vào `ecommerce_fraud_dw` hay schema `marts` (sửa lỗi cấu hình placeholder cũ dùng `${POSTGRES_DB}`).
- Secrets lấy từ `.env` (gitignored), không hard-code.

### 4.2 Database metadata + role đọc (`metabase/init_database.ps1`)

Idempotent, chạy từ project root:

```powershell
.\metabase\init_database.ps1
```

Thực hiện:
1. Tạo role `metabase_ro` (LOGIN, mật khẩu random 24 ký tự alphanumeric)
2. Tạo database `metabase_db` (kiểm tra tồn tại trước)
3. Grants: `CONNECT` trên `ecommerce_fraud_dw`, `USAGE` trên `marts`, `SELECT` trên tất cả bảng `marts` (+ default privileges cho bảng future)
4. Ghi `METABASE_RO_PASSWORD`, `METABASE_ADMIN_EMAIL`, `METABASE_ADMIN_PASSWORD` vào `.env` (chỉ khi chưa có)
5. Verify: login `metabase_ro` và đọc `marts.predictions`

Kết quả thực tế:

```
Created role metabase_ro
Database metabase_db already exists (unchanged)
Granted CONNECT/USAGE/SELECT to metabase_ro on marts
.env already contains all Metabase settings
metabase_ro read-only login verified (marts.predictions rows: 88581)
```

`metabase_ro` **không có** quyền ghi hay admin — đúng nguyên tắc least privilege cho BI.

---

## 5. KẾT NỐI DATA WAREHOUSE VÀ TỰ ĐỘNG HÓA

### 5.1 Khởi động

```powershell
docker compose config          # hợp lệ
docker compose up -d metabase  # pull v0.49.0 (~500MB) + start
docker compose ps
```

Log khởi động: `Metabase Initialization COMPLETE in 48.6 s`; `GET http://localhost:3000` → **HTTP 200**.

### 5.2 Tự động hóa qua Metabase REST API (`metabase/setup_metabase.py`)

```powershell
$env:PYTHONIOENCODING="utf-8"
.venv\Scripts\python.exe metabase\setup_metabase.py
```

Script (idempotent — chạy lại không tạo trùng):

1. Login admin (hoặc hoàn tất first-run setup qua setup token từ `GET /api/session/properties`)
2. Thêm database `ecommerce_fraud_dw` (engine postgres, host `host.docker.internal`, user `metabase_ro`) — check trùng theo tên
3. `POST /api/database/:id/sync_schema` + chờ metadata hiện đủ 5 bảng `marts`
4. Tạo collection **Fraud Analytics**
5. Tạo 8 câu hỏi SQL (4 KPI scalar, 1 line, 2 bar, 1 table) — check trùng theo tên, **update SQL nếu thay đổi**
6. Tạo dashboard **E-commerce Fraud Analytics**, gắn 8 cards theo layout lưới 12 cột
7. Verify: thực thi mỗi card **qua chính kết nối Metabase** (`POST /api/card/:id/query`)

Tài nguyên đã tạo:

| Loại | Tên | ID |
|------|-----|----|
| Database | ecommerce_fraud_dw | 2 |
| Collection | Fraud Analytics | 2 |
| Cards | Tổng số giao dịch / Tổng số giao dịch gian lận / Tỷ lệ giao dịch gian lận (%) / Tổng giá trị giao dịch / Tỷ lệ gian lận theo ngày / Gian lận theo loại thiết bị / Gian lận theo mã sản phẩm / Top 50 dự đoán gian lận | 1–8 |
| Dashboard | E-commerce Fraud Analytics | 1 |

### 5.3 Layout dashboard

| Vị trí | Card |
|--------|------|
| Hàng 0 (4 KPI, mỗi card 3×2) | Tổng số giao dịch · Tổng số gian lận · Tỷ lệ gian lận · Tổng giá trị |
| Hàng 2 (12×5) | Tỷ lệ gian lận theo ngày (line) |
| Hàng 7 (6×5 + 6×5) | Gian lận theo thiết bị (bar) · Gian lận theo sản phẩm (bar) |
| Hàng 12 (12×8) | Top 50 dự đoán gian lận (table) |

URL: `http://localhost:3000/dashboard/1`

---

## 6. NĂM NHÓM PHÂN TÍCH — SQL VÀ KẾT QUẢ THỰC TẾ

SQL files lưu tại `docs/20_dashboard/sql/`. Mọi số liệu dưới đây là kết quả truy vấn thật qua **kết nối Metabase** (không phải SQL client khác), đối chiếu với psql trực tiếp.

### 6.1 Overview — 4 KPI (`overview_metrics.sql`)

| KPI | SQL | Kết quả |
|-----|-----|---------|
| Tổng số giao dịch | `COUNT(*)` | **590,540** |
| Tổng số giao dịch gian lận | `COUNT(*) WHERE is_fraud = 1` | **20,663** |
| Tỷ lệ gian lận | `ROUND(100.0 * COUNT(*) FILTER (...) / NULLIF(COUNT(*), 0), 2)` | **3.50%** (3.4990% trước làm tròn) |
| Tổng giá trị giao dịch | `SUM(transaction_amt)` | **79,738,980.37** |

Đối chiếu: khớp hoàn toàn kết quả psql trực tiếp trên `marts.fact_transactions`.

### 6.2 Fraud Trend — đường theo ngày (`fraud_trend.sql`)

```sql
SELECT to_timestamp(transaction_dt)::date AS transaction_date,
       COUNT(*) AS total_transactions,
       COUNT(*) FILTER (WHERE is_fraud = 1) AS fraud_transactions,
       ROUND(100.0 * COUNT(*) FILTER (WHERE is_fraud = 1)
             / NULLIF(COUNT(*), 0), 2) AS fraud_rate_pct
FROM marts.fact_transactions
GROUP BY transaction_date
ORDER BY transaction_date;
```

- 182 ngày có giao dịch (1970-01-02 .. 1970-07-02), ~2,000–6,800 giao dịch/ngày
- Tỷ lệ gian lận theo ngày dao động ~1.10% .. 6.99%
- ⚠️ `transaction_dt` là epoch **tương đối** của dataset → trục hoành là thời gian tương đối, không phải ngày lịch thật
- Tỷ lệ tính từ **số lượng** giao dịch (FILTER/COUNT), không phải trung bình các tỷ lệ ngày
- Chưa kết luận xu hướng tăng/giảm (cần phân tích thêm)

### 6.3 Device Analysis (`fraud_by_device.sql`)

| device_type | Tổng GD | Gian lận | Tỷ lệ |
|-------------|---------|----------|-------|
| mobile | 55,645 | 5,657 | **10.17%** |
| desktop | 85,165 | 5,554 | **6.52%** |
| Unknown (NULL) | 449,730 | 9,452 | **2.10%** |

- `device_type` materialize trong fact table — không join `dim_device`, không nhân bản giao dịch
- 76% NULL → gom nhóm `Unknown` minh bạch (không loại bỏ âm thầm)
- Sắp xếp tỷ lệ giảm dần; hiển thị kèm tổng số GD để tránh hiểu nhầm

### 6.4 Product Analysis (`fraud_by_product.sql`)

| product_cd | Tổng GD | Gian lận | Tỷ lệ |
|------------|---------|----------|-------|
| C | 68,519 | 8,008 | **11.69%** |
| S | 11,628 | 686 | **5.90%** |
| H | 33,024 | 1,574 | **4.77%** |
| R | 37,699 | 1,426 | **3.78%** |
| W | 439,670 | 8,969 | **2.04%** |

- `product_cd` materialize trong fact table — không join `dim_product`
- Giữ nguyên mã sản phẩm (không có bảng ánh xạ tên thương mại đáng tin cậy)

### 6.5 Prediction Results — Top 50 (`top_fraud_predictions.sql`)

```sql
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
```

- 50 rows, xác suất 99.82% .. 99.47%, sắp xếp xác suất giảm dần
- Top 10 khớp **chính xác** SQL verification Phase 19: 3122167 (99.82), 3127114 (99.71), 3524493/3224515/3360008 (99.68), 3516426/3231532/3231534 (99.67), 3085461/3395166 (99.66)
- `fraud_probability` lưu thang 0–1 (verify Phase 19: [0.004984, 0.998232]) → nhân 100 đúng; `CAST ::numeric` vì PostgreSQL không có `round(double precision, integer)`
- JOIN 1:1 (88,581/88,581 khớp Phase 19) chỉ để lấy `transaction_amt`
- UNIQUE(transaction_id, model_version) đảm bảo không bản ghi trùng
- Sắp xếp theo **xác suất**, không theo nhãn thực tế
- ⚠️ Đây là **dự đoán của mô hình**, không phải kết luận điều tra

---

## 7. KIỂM THỬ VÀ ĐỐI CHIẾU

### A. Hạ tầng

| Check | Kết quả |
|-------|---------|
| `docker compose config` | hợp lệ ✅ |
| Container `fraud_dw_metabase` | Up, `0.0.0.0:3000->3000` ✅ |
| `GET http://localhost:3000` | HTTP 200 ✅ |
| `metabase_db` có 89 metadata tables | ✅ (action, activity, collection, report_card...) |
| PostgreSQL/Airflow hiện có | không bị ảnh hưởng (Up healthy / Up) ✅ |

### B. Kết nối dữ liệu

| Check | Kết quả |
|-------|---------|
| Metabase kết nối `ecommerce_fraud_dw` | Database id=2, `initial_sync_status` complete ✅ |
| Schema `marts` được sync | 5 bảng: dim_date, dim_device, dim_product, fact_transactions, predictions ✅ |
| Truy vấn chạy qua kết nối Metabase | 8/8 cards thực thi thành công (`POST /api/card/:id/query` → HTTP 202) ✅ |

### C. Chất lượng SQL

- 4 KPI trả về 1 row hợp lệ mỗi KPI ✅
- Trend: 182 rows theo thời gian, vẽ được line chart ✅
- Device/Product: 3 và 5 nhóm, sắp xếp giảm dần ✅
- Predictions: đúng 50 rows, sắp xếp xác suất giảm ✅
- Không lỗi tên cột, không chia cho 0 (`NULLIF`), không join nhân bản (không join dimension) ✅

### D. Đối chiếu đúng đắn (Metabase vs psql trực tiếp)

| Chỉ số | Metabase | psql | Khớp |
|--------|----------|------|------|
| total_transactions | 590,540 | 590,540 | ✅ |
| total_fraud | 20,663 | 20,663 | ✅ |
| fraud_rate | 3.50% | 3.4990% → 3.50% | ✅ |
| total_amount | 79,738,980.37 | 79,738,980.37 | ✅ |
| device rates | 10.17 / 6.52 / 2.10 | 10.17 / 6.52 / 2.10 | ✅ |
| product rates | 11.69 / 5.90 / 4.77 / 3.78 / 2.04 | y hệt | ✅ |
| top prediction | 3122167 @ 99.82% | 3122167 @ 99.82% | ✅ |

### E. Dashboard

| Check | Kết quả |
|-------|---------|
| Dashboard lưu thành công | id=1, collection_id=2 (Fraud Analytics) ✅ |
| Đủ 5 nhóm phân tích, 8 cards | ✅ |
| Layout đúng (KPI hàng 0, trend hàng 2, device/product hàng 7, predictions hàng 12) | ✅ (verify qua `GET /api/dashboard/1`) |
| Mở lại sau restart Metabase | `docker restart fraud_dw_metabase` → HTTP 200, dashboard vẫn có 8 dashcards ✅ |
| Không card lỗi | 8/8 query thành công ✅ |

**Ảnh chụp màn hình:** không tạo được (môi trường headless, không có trình duyệt) — NOT RUN, bằng chứng là JSON responses lưu tại `evidence/phase_20/`.

---

## 8. LỖI ĐÃ PHÁT HIỆN VÀ CÁCH XỬ LÝ

| # | Lỗi | Nguyên nhân | Xử lý |
|---|-----|-------------|-------|
| 1 | `GET /api/setup` → "API endpoint does not exist" | v0.49 bỏ GET setup; token nằm ở `GET /api/session/properties` → `setup-token` | Đọc token từ session properties |
| 2 | `POST /api/setup` → 400 `site_name must be a non-blank string` | v0.49 validate `site_name`/`email`/`password` ở **top-level** body (xác nhận qua source `src/metabase/api/setup.clj`), trong khi handler đọc từ `:user` và `:prefs` | Payload gửi cả top-level lẫn nested `user`/`prefs` |
| 3 | Setup 400 lần đầu để lại trạng thái kẹt (token bị tiêu thụ, `core_user` 0 rows, login 401) | Validation fail trước khi tạo user, token chưa được restore | Hoàn tất setup bằng stored token từ table `setting` → user tạo thành công |
| 4 | `GET /api/database` trả object, code đọc list | v0.49 đổi list endpoint sang paginated `{"data": [...], "total": N}` | Helper `_list_payload` |
| 5 | `POST /api/database/:id/sync` → 404 | v0.49 đổi thành `POST /:id/sync_schema` (async) | Đổi endpoint; metadata shape cũng đổi (tables ở top-level, không phải `schemas[]`) |
| 6 | `POST /api/dashboard/:id/cards` → 404 | v0.49 bỏ endpoint này; dùng `PUT /api/dashboard/:id/cards` (deprecated) hoặc `PUT /:id` | Dùng `PUT /:id/cards` với `card_id` + **id âm** (temporary) cho card mới, id thật cho card đã có |
| 7 | Dashboard tạo nhưng không nằm trong collection | Body create dùng `collection` (sai key) | v0.49 dùng `collection_id`; script thêm bước PUT move nếu sai |
| 8 | `POST /api/card/:id/query` → script báo lỗi | Endpoint trả **202 Accepted** kèm dữ liệu (async query) | Chấp nhận cả 200/202 |
| 9 | Card predictions trả 0 rows: `function round(double precision, integer) does not exist` | PostgreSQL không có `round(dp, int)`; `fraud_probability` là double precision | `ROUND((p.fraud_probability * 100)::numeric, 2)` — cast sang numeric |
| 10 | In log tiếng Việt lỗi `UnicodeEncodeError: cp1252` | Console Windows mặc định cp1252 | `sys.stdout.reconfigure(encoding="utf-8")` + `PYTHONIOENCODING=utf-8` |

---

## 9. HẠN CHẾ CÒN TỒN TẠI

1. **`fraud_dw_api` restart loop** — lỗi Docker image có sẵn (`uvicorn: Permission denied`), không thuộc Phase 20, chưa sửa.
2. **Hai PostgreSQL instance** — Windows PG 18.3 (localhost:5432, chứa DW) và docker `fraud_dw_postgres` 15-alpine (chỉ `raw.identity`). Metabase kết nối đúng Windows instance qua `host.docker.internal`. Cần lưu ý khi vận hành: `docker compose ps` hiển thị mapping 5432 của container nhưng host port 5432 thực tế thuộc Windows PG.
3. **Trục thời gian trend là tương đối** — `transaction_dt` là epoch của dataset (1970-01-02..1970-07-03), không phải ngày lịch thật; dashboard ghi chú rõ điều này.
4. **`device_type` 76% NULL** — nhóm Unknown chiếm đa số; không kết luận "thiết bị không xác định an toàn nhất" vì giá trị bị thiếu, không phải bằng chứng hành vi.
5. **Chưa có bộ lọc thời gian dùng chung** — các card native query chưa gắn dashboard parameter; trend có trường ngày nhưng bảng predictions không có trường thời gian tương ứng (chỉ `predicted_at`). Bổ sung được sau bằng dashboard filters + parameter mappings.
6. **Không có screenshot** — môi trường headless; bằng chứng là JSON API responses và logs.
7. **Tài khoản admin Metabase** (`admin@frauddw.local`) và `metabase_ro` password nằm trong `.env` (gitignored) — người dùng nên đổi mật khẩu admin qua UI sau lần đăng nhập đầu.

---

## 10. FILES & EVIDENCE

```
docker-compose.yml                      # thêm service metabase (sửa placeholder cũ)
metabase/
├── init_database.ps1                   # tạo metabase_db + metabase_ro + grants (idempotent)
└── setup_metabase.py                   # automation qua Metabase REST API (idempotent)
docs/20_dashboard/
├── metabase_dashboard.md               # tài liệu này
└── sql/
    ├── overview_metrics.sql            # 4 KPI
    ├── fraud_trend.sql                 # line chart
    ├── fraud_by_device.sql             # bar chart
    ├── fraud_by_product.sql            # bar chart
    └── top_fraud_predictions.sql       # table top 50
evidence/phase_20/
├── metabase_database.json              # GET /api/database/2
├── card_total_transactions.json        # card definitions (8 files)
├── ...
├── dashboard.json                      # GET /api/dashboard/1 (sau khi gắn cards)
└── card_query_results.json             # kết quả 8 card query qua kết nối Metabase
```

.env (gitignored) thêm: `METABASE_RO_PASSWORD`, `METABASE_ADMIN_EMAIL`, `METABASE_ADMIN_PASSWORD`.

---

## 11. TIÊU CHÍ HOÀN THÀNH

| Tiêu chí | Trạng thái |
|----------|------------|
| Metabase chạy ổn định trên cổng 3000 | **PASS** (HTTP 200, container Up) |
| Database metadata được cấu hình đúng | **PASS** (`metabase_db`, 89 tables, không ghi vào `marts`) |
| Metabase kết nối được `ecommerce_fraud_dw` | **PASS** (database id=2, sync complete) |
| Schema phân tích được đồng bộ | **PASS** (5 bảng marts visible) |
| Overview có đủ bốn KPI | **PASS** (4 scalar cards, giá trị đối chiếu khớp) |
| Fraud Trend có biểu đồ đường | **PASS** (line card, 182 rows) |
| Device Analysis có biểu đồ phù hợp | **PASS** (bar card, 3 nhóm) |
| Product Analysis có biểu đồ phù hợp | **PASS** (bar card, 5 nhóm) |
| Prediction Results có bảng Top 50 | **PASS** (table card, 50 rows, dữ liệu Phase 19 thật) |
| Các truy vấn được kiểm thử và đối chiếu với PostgreSQL | **PASS** (8/8 cards query qua Metabase, đối chiếu psql) |
| Dashboard được lưu và có thể mở lại | **PASS** (restart test: HTTP 200, 8 dashcards còn nguyên) |
| Tài liệu Phase 20 được cập nhật | **PASS** (tài liệu này) |
| Không phá vỡ các service hoặc pipeline trước đó | **PASS** (postgres/airflow Up; Phase 19 artifacts không đổi) |

---

## 12. LIÊN HỆ

- Trước: [PHASE 19 — Model Integration](../19_model_integration/model_integration.md) (nguồn dữ liệu `marts.predictions`)
- Sau: [PHASE 21 — FastAPI API](../21_api/fastapi_api.md)

*Cập nhật: 09/10/2026 | Metabase v0.49.0 | Kết quả thực nghiệm, verified*
