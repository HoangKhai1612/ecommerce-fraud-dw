# PHASE 23 — Docker Compose Integration and Validation

## 1. MỤC TIÊU

Đóng gói và xác thực toàn bộ hệ thống bằng Docker Compose:

- PostgreSQL Data Warehouse
- Airflow (webserver + scheduler, LocalExecutor)
- Metabase (BI Dashboard)
- ML FastAPI (Phase 21)
- AI Assistant (Phase 22)
- Ollama (LLM backend)

Yêu cầu: build được, khởi động được, health check được, kết nối liên dịch vụ được, **bảo toàn dữ liệu hiện có**.

---

## 2. KIẾN TRÚC THỰC TẾ

Khảo sát thực tế (13/10/2026) cho thấy hệ thống **không** theo mô hình "all-in-one-container". Data Warehouse chính chạy trên Windows PostgreSQL 18, không phải container:

| Thành phần | Thực tế | Truy cập từ container |
|---|---|---|
| Data Warehouse chính | Windows PostgreSQL 18.3 (service `postgresql-x64-18`, Automatic), host port **5432**. Chứa `ecommerce_fraud_dw` (raw/staging/marts), `airflow_db`, `metabase_db` | `host.docker.internal:5432` |
| PostgreSQL docker-local | Container `postgres:15-alpine`, volume `ecommerce-fraud-dw_postgres_data` (bảo toàn), host port **5434** — instance phụ, cách ly | `localhost:5434` (host) |
| Ollama | Native trên Windows host (`127.0.0.1:11434`), model `llama3:latest` (8B, Q4_0, ~4.66 GB) đã tải sẵn | `host.docker.internal:11434` |
| Airflow | Container `apache/airflow:2.10.5` + dbt, LocalExecutor (webserver + scheduler trong 1 container), metadata = `airflow_db` | `localhost:8080` |
| Metabase | Container `metabase/metabase:v0.49.0`, application DB = `metabase_db`, query DW `ecommerce_fraud_dw` | `localhost:3000` |
| ML API | Container build từ `api/Dockerfile` (python:3.12-slim), artifact XGBoost bake trong image | `localhost:8000` |
| AI Assistant | Container build từ `ai_assistant/Dockerfile` (python:3.12-slim), role `ai_assistant_ro` read-only | `localhost:8001` |

**Quy tắc kết nối:** container giao tiếp với Data Warehouse qua tên đặc biệt `host.docker.internal` (Docker Desktop host-gateway), **không** dùng `localhost`. Ollama không cần container hóa vì đã chạy native và container truy cập được qua `host.docker.internal:11434` (đã xác minh).

**Tại sao không có Redis:** Airflow dùng LocalExecutor, không dịch vụ nào cần Redis → không bổ sung thành phần ngoài phạm vi.

---

## 3. CẤU TRÚC FILE

```
ecommerce-fraud-dw/
├── docker-compose.yml          # Compose chính (postgres, airflow, metabase, api, ai-assistant, ollama*)
├── .env                        # Biến môi trường thực tế
├── .env.example                # File mẫu (placeholder, không chứa secret thật)
├── docker/init_db.sh           # Init idempotent cho docker-local PG (chỉ chạy khi volume rỗng)
├── Dockerfile                  # Root image (đã sửa bug pip --user)
├── Dockerfile.airflow          # Airflow image (apache/airflow:2.10.5 + dbt provider)
├── api/Dockerfile              # ML API image (python:3.12-slim)
├── ai_assistant/Dockerfile     # AI Assistant image (python:3.12-slim)
└── ...
```

*Ollama nằm sau profile `optional-services`, mặc định tắt.

**File đã xóa:** `docker-compose.airflow.yml` — gộp vào `docker-compose.yml` để một file triển khai nhất quán (hai file cùng `container_name: fraud_dw_airflow` nên không thể tồn tại song song).

---

## 4. docker-compose.yml

```yaml
services:
  # PostgreSQL docker-local (instance phụ). DW chính là Windows PostgreSQL 18.
  postgres:
    image: postgres:15-alpine
    container_name: fraud_dw_postgres
    restart: unless-stopped
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-postgres}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-postgres}
      POSTGRES_DB: ${POSTGRES_DB:-ecommerce_fraud_dw}
    ports:
      - "${DOCKER_POSTGRES_PORT:-5434}:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./docker/init_db.sh:/docker-entrypoint-initdb.d/init_db.sh:ro
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-postgres} -d ${POSTGRES_DB:-ecommerce_fraud_dw}"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - fraud_dw_network

  # Airflow webserver + scheduler (LocalExecutor). Metadata: airflow_db trên Windows PG.
  airflow:
    build:
      context: .
      dockerfile: Dockerfile.airflow
    container_name: fraud_dw_airflow
    restart: unless-stopped
    ports:
      - "${AIRFLOW_PORT:-8080}:8080"
    environment:
      AIRFLOW__CORE__EXECUTOR: LocalExecutor
      AIRFLOW__DATABASE__SQL_ALCHEMY_CONN: postgresql+psycopg2://${POSTGRES_USER:-postgres}:${POSTGRES_PASSWORD_URI}@host.docker.internal:5432/airflow_db
      AIRFLOW__CORE__LOAD_EXAMPLES: "false"
      AIRFLOW__API__AUTH_BACKENDS: airflow.api.auth.backend.basic_auth
      AIRFLOW_CONN_POSTGRES_DEFAULT: postgres://${POSTGRES_USER:-postgres}:${POSTGRES_PASSWORD_URI}@host.docker.internal:5432/${POSTGRES_DB:-ecommerce_fraud_dw}
      AIRFLOW__SCHEDULER__ENABLE_HEALTH_CHECK: "true"
      POSTGRES_HOST: host.docker.internal
      POSTGRES_USER: ${POSTGRES_USER:-postgres}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-postgres}
      POSTGRES_DB: ${POSTGRES_DB:-ecommerce_fraud_dw}
      DBT_POSTGRES_HOST: host.docker.internal
      DBT_POSTGRES_USER: ${POSTGRES_USER:-postgres}
      DBT_POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-postgres}
      DBT_POSTGRES_DB: ${POSTGRES_DB:-ecommerce_fraud_dw}
    volumes:
      - ./airflow/dags:/opt/airflow/dags
      - ./airflow/logs:/opt/airflow/logs
      - ./airflow/plugins:/opt/airflow/plugins
      - ./airflow/config:/opt/airflow/config
      - ./ingestion:/opt/airflow/ingestion
      - ./dbt:/opt/airflow/dbt
      - ./data:/opt/airflow/data
    command: >
      bash -c "
        airflow db migrate &&
        airflow users create --username ${AIRFLOW_ADMIN_USER:-admin} --password ${AIRFLOW_ADMIN_PASSWORD:-admin} --firstname Admin --lastname User --role Admin --email admin@example.com || true &&
        airflow scheduler &
        exec airflow webserver --port 8080
      "
    healthcheck:
      test: ["CMD-SHELL", "python -c \"import urllib.request; urllib.request.urlopen('http://localhost:8080/api/v1/health', timeout=5)\""]
      interval: 30s
      timeout: 10s
      retries: 5
      start_period: 40s
    extra_hosts:
      - "host.docker.internal:host-gateway"
    networks:
      - fraud_dw_network

  # Metabase. Application DB: metabase_db trên Windows PG. Query DW: ecommerce_fraud_dw.
  metabase:
    image: metabase/metabase:v0.49.0
    container_name: fraud_dw_metabase
    restart: unless-stopped
    environment:
      MB_DB_TYPE: postgres
      MB_DB_DBNAME: metabase_db
      MB_DB_HOST: host.docker.internal
      MB_DB_PORT: "5432"
      MB_DB_USER: ${POSTGRES_USER:-postgres}
      MB_DB_PASS: ${POSTGRES_PASSWORD:-postgres}
    ports:
      - "${METABASE_PORT:-3000}:3000"
    extra_hosts:
      - "host.docker.internal:host-gateway"
    networks:
      - fraud_dw_network

  # ML FastAPI (Phase 21). Artifact XGBoost trong ml/models/ được bake vào image.
  api:
    build:
      context: .
      dockerfile: api/Dockerfile
    container_name: fraud_dw_api
    restart: unless-stopped
    environment:
      API_HOST: 0.0.0.0
      API_PORT: "8000"
      POSTGRES_HOST: host.docker.internal
      POSTGRES_PORT: "5432"
      POSTGRES_USER: ${POSTGRES_USER:-postgres}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-postgres}
      POSTGRES_DB: ${POSTGRES_DB:-ecommerce_fraud_dw}
    ports:
      - "${API_PORT:-8000}:8000"
    healthcheck:
      test: ["CMD-SHELL", "python -c \"import urllib.request; urllib.request.urlopen('http://localhost:8000/health', timeout=5)\""]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 15s
    extra_hosts:
      - "host.docker.internal:host-gateway"
    networks:
      - fraud_dw_network

  # AI Assistant (Phase 22). Read-only Text-to-SQL trên schema marts.
  ai-assistant:
    build:
      context: .
      dockerfile: ai_assistant/Dockerfile
    container_name: fraud_dw_ai_assistant
    restart: unless-stopped
    environment:
      AI_DB_HOST: host.docker.internal
      AI_DB_PORT: "5432"
      AI_DB_NAME: ${POSTGRES_DB:-ecommerce_fraud_dw}
      AI_DB_USER: ${AI_DB_USER:-ai_assistant_ro}
      AI_DB_PASSWORD: ${AI_DB_PASSWORD:-}
      AI_ALLOWED_SCHEMAS: ${AI_ALLOWED_SCHEMAS:-marts}
      OLLAMA_BASE_URL: http://host.docker.internal:11434
      LLM_MODEL: ${LLM_MODEL:-llama3}
    ports:
      - "${AI_ASSISTANT_PORT:-8001}:8001"
    healthcheck:
      test: ["CMD-SHELL", "python -c \"import urllib.request; urllib.request.urlopen('http://localhost:8001/health', timeout=5)\""]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 15s
    extra_hosts:
      - "host.docker.internal:host-gateway"
    networks:
      - fraud_dw_network

  # Ollama containerized (TÙY CHỌN, mặc định tắt). Hệ thống dùng native Ollama trên host.
  # Bật: docker compose --profile optional-services up -d ollama
  # (phải stop native Ollama trước vì trùng port 11434; model cần tải lại ~4.66 GB
  # trừ khi mount store host vào /root/.ollama)
  ollama:
    image: ollama/ollama:latest
    container_name: fraud_dw_ollama
    profiles:
      - optional-services
    restart: unless-stopped
    environment:
      OLLAMA_NUM_GPU: "0"
    ports:
      - "${OLLAMA_PORT:-11434}:11434"
    volumes:
      - ollama_data:/root/.ollama
    networks:
      - fraud_dw_network

volumes:
  postgres_data:
  ollama_data:

networks:
  fraud_dw_network:
    driver: bridge
```

**Giải thích thiết kế:**

- **Không `depends_on` giả tạo:** các service kết nối tới Windows PG 18 (bên ngoài Compose) qua `host.docker.internal`, nên không thể `depends_on` một dịch vụ ngoài Compose. Windows PG 18 là Windows service tự động (Automatic start).
- **Healthcheck** dùng `python -c urllib.request` (image python-slim không có `curl`) và `pg_isready` cho Postgres.
- **Secret:** toàn bộ qua biến `.env` (interpolation `${...}`), không hardcode trong Compose/Dockerfile. `POSTGRES_PASSWORD_URI` là mật khẩu đã URL-encode (ví dụ `@` → `%40`) dùng cho Airflow SQL Alchemy URL.
- **Volume `postgres_data`:** named volume đã tồn tại (`ecommerce-fraud-dw_postgres_data`), Compose tái sử dụng — **không mất dữ liệu** khi recreate container.

---

## 5. DOCKERFILES

### 5.1 api/Dockerfile (ML API — Phase 21)

```dockerfile
FROM python:3.12-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev && rm -rf /var/lib/apt/lists/*
COPY api/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt
COPY . /app/
ENV PYTHONPATH=/app
EXPOSE 8000
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 5.2 ai_assistant/Dockerfile (AI Assistant — Phase 22, mới tạo)

```dockerfile
FROM python:3.12-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev && rm -rf /var/lib/apt/lists/*
COPY ai_assistant/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt
COPY . /app/
ENV PYTHONPATH=/app PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
EXPOSE 8001
CMD ["uvicorn", "ai_assistant.main:app", "--host", "0.0.0.0", "--port", "8001"]
```

### 5.3 Dockerfile.airflow

```dockerfile
FROM apache/airflow:2.10.5
USER root
RUN apt-get update && apt-get install -y --no-install-recommends git \
    && apt-get clean && rm -rf /var/lib/apt/lists/*
USER airflow
COPY airflow/requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r /requirements.txt
```

`airflow/requirements.txt`: `apache-airflow-providers-postgres==6.0.0`, `dbt-core==1.8.2`, `dbt-postgres==1.8.2`, `dbt-adapters<1.24.0`, `dbt-common<1.37.0`, `protobuf<5.0.0`.

### 5.4 docker/init_db.sh

Chỉ chạy khi volume `postgres_data` **rỗng** (lần init đầu tiên) — cơ chế `/docker-entrypoint-initdb.d/` của PostgreSQL. Tạo idempotent schema `raw`/`staging`/`marts` và role read-only `POSTGRES_RO_USER` (CONNECT + USAGE + SELECT).

---

## 6. BIẾN MÔI TRƯỜNG (.env)

```env
# PostgreSQL (DW chính trên Windows host, port 5432)
POSTGRES_USER=postgres
POSTGRES_PASSWORD=<mat_khau_thuc>
POSTGRES_DB=ecommerce_fraud_dw
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
# Mật khẩu đã URL-encode cho Airflow SQL Alchemy URL ("@" -> "%40")
POSTGRES_PASSWORD_URI=<uri_encoded>

# Read-only user cho AI Assistant (Phase 22)
POSTGRES_RO_USER=ai_assistant_ro
POSTGRES_RO_PASSWORD=<mat_khau_thuc>
AI_DB_USER=ai_assistant_ro
AI_DB_PASSWORD=<mat_khau_thuc>
AI_ALLOWED_SCHEMAS=marts

# Airflow
AIRFLOW_ADMIN_USER=admin
AIRFLOW_ADMIN_PASSWORD=<mat_khau_thuc>
AIRFLOW_PORT=8080

# ML API (Phase 21)
API_HOST=0.0.0.0
API_PORT=8000

# LLM / AI Assistant (Ollama native trên host)
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
LLM_MODEL=llama3

# Metabase
METABASE_PORT=3000

# AI Assistant service port (container)
AI_ASSISTANT_PORT=8001

# Docker-local PostgreSQL host port (instance phụ, tránh trùng 5432)
DOCKER_POSTGRES_PORT=5434

# System paths
DATA_DIR=./data/raw
MODEL_DIR=./ml/models
```

File mẫu `.env.example` dùng placeholder `change_me`, không chứa secret thật.

---

## 7. KHỞI CHẠY

```powershell
# 1. Đảm bảo Windows PostgreSQL 18 service đang chạy (DW chính)
Get-Service postgresql-x64-18          # phải là Running
# Đảm bảo Ollama native đang chạy và có model llama3
# ollama list  ->  llama3  8B  Q4_0

# 2. Validate cấu hình
docker compose config -q

# 3. Build image cần build (api, ai-assistant, airflow)
docker compose build

# 4. Khởi động tất cả service
docker compose up -d

# 5. Kiểm tra
docker compose ps                      # tất cả healthy
curl http://localhost:8000/health      # ML API
curl http://localhost:8001/health      # AI Assistant
curl http://localhost:8080/api/v1/health   # Airflow
curl http://localhost:3000/api/health      # Metabase
curl http://localhost:11434/api/tags       # Ollama
```

**Dừng an toàn:**

```powershell
docker compose stop        # KHÔNG xóa volume
# TUYỆT ĐỐI KHÔNG: docker compose down -v   (xóa volume postgres_data)
```

---

## 8. KẾT QUẢ XÁC THỰC (13/10/2026)

### 8.1 Kiểm thử từng dịch vụ

| Dịch vụ | Bằng chứng thực tế |
|---|---|
| PostgreSQL (Windows PG 18) | `marts.fact_transactions` = 590,540 rows; schemas raw/staging/marts; `airflow_db`, `metabase_db` tồn tại |
| PostgreSQL (docker-local 5434) | `pg_isready` healthy; `ALTER USER` đồng bộ password với `.env` thành công |
| Airflow | `/api/v1/health`: metadb `healthy`, scheduler heartbeat mới; UI 200; `airflow users list` có `admin` (Admin role) |
| Airflow DAG | `GET /api/v1/dags` (Basic auth): `fraud_dw_pipeline \| paused=False` |
| ML API | `/health` 200; `/ready` 200 `database:ok`; log: `Model loaded: XGBClassifier`, `Feature columns: 1014`, `All artifacts loaded successfully!` |
| ML API prediction | `POST /predict` → 200 `fraud_probability=0.2585, risk_level=low`; `GET /transactions/3411796` → data thật; `GET /transactions/predictions/top?limit=3` → 3 rows xác suất ~0.998 |
| AI Assistant | `/health` 200; `POST /chat` end-to-end: Ollama phân loại → tạo SQL `SELECT COUNT(*) FROM marts.fact_transactions LIMIT 100` → validator duyệt → query DW thật → kết quả 590,540 → tóm tắt tiếng Việt |
| Ollama | `/api/tags`: `llama3:latest 8.0B Q4_0`; `/api/generate` → 200 |
| Metabase | `/api/health` 200; UI 200; log: `Successfully verified PostgreSQL 18.3 application database connection`; `metabase_db` có 89 tables, cấu hình DW `ecommerce_fraud_dw` |

### 8.2 Quyền SQL an toàn (bằng chứng thực tế)

- `ai_assistant_ro`: `rolsuper=f, rolcreaterole=f, rolcreatedb=f`; GRANT `SELECT` trên đúng 5 bảng `marts.*` (dim_date, dim_device, dim_product, fact_transactions, predictions).
- Thử `INSERT` bằng `ai_assistant_ro` → `ERROR: permission denied for table predictions`.
- Validator (sqlglot) từ chối: `INSERT`, `DROP`, multi-statement, hàm bị chặn (`pg_sleep`, `nextval`, ...), bảng ngoài schema `marts`.

### 8.3 Regression tests

- Trong container: `api/tests` → **20 passed**; `ai_assistant/tests` → **12 passed**.
- Host `.venv` (Python 3.14): `pytest api/tests ai_assistant/tests` → **32 passed**.

### 8.4 Bảo toàn dữ liệu

| Bảng | Trước | Sau |
|---|---|---|
| marts.fact_transactions | 590,540 | 590,540 |
| marts.predictions | 88,581 | 88,581 |
| raw.transactions | 590,540 | 590,540 |
| raw.identity | 144,233 | 144,233 |
| marts.dim_date | 183 | 183 |
| marts.dim_product | 22 | 22 |
| marts.dim_device | 1,939 | 1,939 |

Volume `ecommerce-fraud-dw_postgres_data` giữ nguyên mountpoint. Không xóa database/table nào.

---

## 9. CÁC VẤN ĐỀ ĐÃ SỬA

| # | Vấn đề | Khắc phục |
|---|---|---|
| 1 | `docker-compose.yml` lỗi cú pháp: duplicate key `api` (line 26 & 105) — Compose không parse được | Viết lại compose, một service `api` duy nhất dùng `api/Dockerfile` |
| 2 | ML API crash-loop: root `Dockerfile` dùng `pip install --user` (vào `/root/.local`) rồi `USER appuser` → `Permission denied` chạy uvicorn | Sửa root Dockerfile cài system-wide; compose dùng `api/Dockerfile` |
| 3 | Compose mount `./ml/saved_models` (không tồn tại); artifact thật ở `ml/models/` | Gỡ mount sai; `api/Dockerfile` COPY cả project, artifact bake vào image (`xgboost.pkl`, `feature_columns.json`, `frequency_encoder.pkl`, `preprocessor.pkl`) |
| 4 | AI Assistant chưa có Dockerfile | Tạo `ai_assistant/Dockerfile`, port 8001 |
| 5 | `airflow users create` thất bại âm thầm (`|| true` nuốt lỗi) do YAML folded scalar phá vỡ line-continuation `\` → không có user admin → REST API 401 | Viết command single-line; verify `airflow users list` có admin |
| 6 | Docker-local PG công host port 5432 trùng Windows PG 18 → ambiguous connections | Remap docker-local PG sang host **5434** (`DOCKER_POSTGRES_PORT`); 5432 thuộc độc quyền Windows PG 18 |
| 7 | Secret hardcode trong `docker-compose.airflow.yml` | Dùng biến `.env`; thêm `POSTGRES_PASSWORD_URI` (URI-encoded) |
| 8 | `.env.example` chứa mật khẩu thật; `MODEL_DIR` sai (`ml/saved_models`) | Placeholder `change_me`; `MODEL_DIR=./ml/models`; bổ sung `AI_DB_*`, `AI_ALLOWED_SCHEMAS`, `POSTGRES_PASSWORD_URI`, `DOCKER_POSTGRES_PORT`, `AI_ASSISTANT_PORT` |
| 9 | `ecommerce-fraud-dw-khai.zip` (90.7 MB) trong build context | Thêm `*.zip`, `logs/`, `.kilo/` vào `.dockerignore` |

**Không thay đổi:** AI Assistant Phase 22, ML API Phase 21, DAG `fraud_dw_pipeline`, dbt models, dashboard Metabase, logic ML, artifact model.

*Lưu ý: git binary không có trên máy này nên chưa chạy `git diff`; thay đổi được liệt kê ở bảng trên.*

---

## 10. VẤN ĐỀ CÒN TỒN TẠI

1. **Docker-local PG (5434) là instance phụ:** volume từ 2026-09-09 chỉ chứa bản partial (`raw.identity`), không có `marts`. Cố ý không migrate để ưu tiên bảo toàn dữ liệu. Nếu cần đồng bộ DW vào container: `pg_dump` từ Windows PG 18 → `pg_restore` có kiểm soát (Phase 24+).
2. **`init_db.sh` chỉ chạy khi volume rỗng** — đúng cơ chế PostgreSQL entrypoint, không áp dụng cho volume đã có dữ liệu.
3. **Mật khẩu docker-local PG:** đã đồng bộ bằng `ALTER USER postgres PASSWORD` để khớp `.env`; nếu xóa volume và tạo lại, password lấy từ `.env` lúc init.
4. **Ollama container hóa:** cần stop native Ollama trước (trùng port 11434) và tải lại model ~4.66 GB trừ khi mount `C:\Users\Administrator\.ollama` vào `/root/.ollama`.

---

## 11. URL DỊCH VỤ

| Dịch vụ | URL | Ghi chú |
|---|---|---|
| PostgreSQL (DW chính) | `localhost:5432` | Windows PG 18, user `postgres` |
| PostgreSQL (docker-local) | `localhost:5434` | `postgres:15-alpine`, password theo `.env` |
| Airflow UI | http://localhost:8080 | Basic auth: `admin` / `AIRFLOW_ADMIN_PASSWORD` |
| Airflow REST API | http://localhost:8080/api/v1/health | Cần Basic auth |
| ML API | http://localhost:8000 | `/health`, `/ready`, `/docs` |
| AI Assistant | http://localhost:8001 | `/health`, `POST /chat` |
| Metabase | http://localhost:3000 | App DB `metabase_db`, DW `ecommerce_fraud_dw` |
| Ollama | http://localhost:11434/api/tags | Native trên host |

---

## 12. TIÊU CHÍ NGHIỆM THU

| Tiêu chí | Trạng thái | Bằng chứng |
|---|---|---|
| Compose hợp lệ | PASS | `docker compose config -q` → VALID |
| Build thành công | PASS | `docker compose build api ai-assistant airflow` → exit 0, 3 image |
| PostgreSQL hoạt động | PASS | Healthcheck healthy cả 2 instance |
| Dữ liệu DW bảo toàn | PASS | Bảng 8.4 (trước = sau) |
| Airflow hoạt động | PASS | Webserver 200, scheduler heartbeat, metadb healthy |
| DAG được nhận diện | PASS | `fraud_dw_pipeline` qua REST API, `paused=False` |
| ML API hoạt động | PASS | HTTP 200 + log load model XGBClassifier/1014 features |
| AI Assistant hoạt động | PASS | HTTP 200 + query end-to-end thành công |
| Quyền SQL an toàn | PASS | INSERT bị `permission denied`; validator chặn INSERT/DROP |
| Ollama hoạt động | PASS | `/api/tags` + `/api/generate` 200 |
| Metabase hoạt động | PASS | HTTP 200 + verified PostgreSQL 18.3 connection |
| Integration | PASS | Container → host.docker.internal:5432/5434/11434 đều OK |
| Bảo toàn cấu hình | PASS | Volume giữ nguyên; không mất database/table |
| Tài liệu Phase 23 | PASS | File này, cập nhật theo trạng thái thực tế |

---

## 13. CÁC BƯỚC TIẾP THEO CHO PHASE 24 — END-TO-END PIPELINE

1. Trigger DAG `fraud_dw_pipeline` thủ công qua Airflow UI/API sau khi xác nhận idempotency (ingestion dùng DROP+CREATE từ CSV, dbt staging=view / marts=table — đã an toàn để re-run).
2. Verify task `verify_marts_quality` thành công trên run mới.
3. Kiểm tra dashboard Metabase còn hoạt động với data mới.
4. Test AI Assistant với câu hỏi phân tích phức tạp hơn (JOIN nhiều bảng trong `marts`).

---

*Trước: [PHASE 22 — AI Assistant](../22_ai_assistant/ai_assistant.md)*
*Sau: [PHASE 24 — End-to-End Pipeline](../24_end_to_end/end_to_end.md)*

*Cập nhật: 13/10/2026 | Version: 2.0*
