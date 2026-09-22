# PHASE 23 — Docker Compose

## 1. MỤC TIÊU

Đóng gói toàn bộ hệ thống vào Docker Compose để dễ triển khai:
- PostgreSQL (Data Warehouse)
- Airflow (Orchestration)
- Metabase (BI Dashboard)
- FastAPI (ML API)
- AI Assistant
- Ollama (LLM)

---

## 2. CẤU TRÚC FILE

```
ecommerce-fraud-dw/
├── docker-compose.yml         # Main compose file
├── .env                       # Environment variables
├── init_db.sql                # Database initialization
├── ingestion/
│   └── load_raw.py
├── dbt/
│   ├── dbt_project.yml
│   ├── profiles.yml
│   ├── models/
│   └── macros/
├── ml/
│   └── [model code]
├── api/
│   └── [FastAPI code]
├── ai_assistant/
│   └── [AI assistant code]
├── airflow/
│   └── dags/
├── metabase/                  # Metabase data
├── data/
│   └── raw/                   # CSV files (mounted)
└── tests/
    └── [test files]
```

---

## 3. docker-compose.yml

```yaml
version: '3.9'

services:
  # --- PostgreSQL ---
  postgres:
    image: postgres:15-alpine
    container_name: ecommerce_fraud_pg
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-postgres}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-postgres}
      POSTGRES_DB: ${POSTGRES_DB:-ecommerce_fraud_dw}
    ports:
      - "${POSTGRES_PORT:-5432}:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init_db.sql:/docker-entrypoint-initdb.d/init_db.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-postgres}"]
      interval: 5s
      timeout: 5s
      retries: 10
    restart: unless-stopped

  # --- Airflow ---
  airflow-webserver:
    image: apache/airflow:2.8.0
    container_name: ecommerce_airflow_web
    depends_on:
      postgres:
        condition: service_healthy
    environment:
      - AIRFLOW__CORE__EXECUTOR=LocalExecutor
      - AIRFLOW__CORE__SQL_ALCHEMY_CONN=postgresql+psycopg2://postgres:postgres@postgres:5432/airflow_db
      - AIRFLOW__CORE__LOAD_EXAMPLES=False
      - AIRFLOW__WEBSERVER__RBAC=True
    volumes:
      - ./airflow/dags:/opt/airflow/dags
      - ./ingestion:/opt/airflow/ingestion
      - ./dbt:/opt/airflow/dbt
    ports:
      - "8080:8080"
    command: webserver
    restart: unless-stopped

  airflow-scheduler:
    image: apache/airflow:2.8.0
    container_name: ecommerce_airflow_sched
    depends_on:
      - airflow-webserver
    environment:
      - AIRFLOW__CORE__EXECUTOR=LocalExecutor
      - AIRFLOW__CORE__SQL_ALCHEMY_CONN=postgresql+psycopg2://postgres:postgres@postgres:5432/airflow_db
      - AIRFLOW__CORE__LOAD_EXAMPLES=False
    volumes:
      - ./airflow/dags:/opt/airflow/dags
      - ./ingestion:/opt/airflow/ingestion
      - ./dbt:/opt/airflow/dbt
    command: scheduler
    restart: unless-stopped

  # --- ML API ---
  ml-api:
    build:
      context: .
      dockerfile: api/Dockerfile
    container_name: ecommerce_ml_api
    depends_on:
      - postgres
    ports:
      - "8000:8000"
    volumes:
      - ./ml/models:/app/ml/models
      - ./ml/data:/app/ml/data
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@postgres:5432/ecommerce_fraud_dw
      - MODEL_PATH=/app/ml/models/xgb_model.pkl
    restart: unless-stopped

  # --- AI Assistant ---
  ollama:
    image: ollama/ollama
    container_name: ecommerce_ollama
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    restart: unless-stopped

  ai-assistant:
    build:
      context: .
      dockerfile: ai_assistant/Dockerfile
    container_name: ecommerce_ai_assistant
    depends_on:
      - ollama
      - postgres
    ports:
      - "8001:8001"
    volumes:
      - ./ai_assistant:/app
    environment:
      - OLLAMA_BASE_URL=http://ollama:11434
      - LLM_MODEL=llama3
      - DB_HOST=postgres
    restart: unless-stopped

  # --- Metabase ---
  metabase:
    image: metabase/metabase:v0.49.0
    container_name: ecommerce_metabase
    depends_on:
      postgres:
        condition: service_healthy
    ports:
      - "3000:3000"
    environment:
      - MB_DB_TYPE=postgres
      - MB_DB_DBNAME=metabase_db
      - MB_DB_PORT=5432
      - MB_DB_USER=postgres
      - MB_DB_PASS=postgres
      - MB_DB_HOST=postgres
    volumes:
      - metabase_data:/metabase-data
    restart: unless-stopped

  # --- Redis (optional, for Airflow Celery) ---
  redis:
    image: redis:7-alpine
    container_name: ecommerce_redis
    ports:
      - "6379:6379"
    restart: unless-stopped

volumes:
  postgres_data:
  metabase_data:
  ollama_data:
  airflow_data:
```

---

## 4. init_db.sql

File: `init_db.sql` — chạy tự động khi container PostgreSQL khởi tạo lần đầu

```sql
-- Create schemas
CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS marts;

-- Create user roles
CREATE USER readonly_user WITH PASSWORD 'readonly_password';
CREATE USER airflow_user WITH PASSWORD 'airflow_password';

-- Grant permissions
GRANT CONNECT ON DATABASE ecommerce_fraud_dw TO readonly_user;
GRANT CONNECT ON DATABASE ecommerce_fraud_dw TO airflow_user;
GRANT USAGE ON SCHEMA raw, staging, marts TO readonly_user;
GRANT USAGE ON SCHEMA raw, staging, marts TO airflow_user;
GRANT SELECT ON ALL TABLES IN SCHEMA raw, staging, marts TO readonly_user;
GRANT SELECT ON ALL TABLES IN SCHEMA raw, staging, marts TO airflow_user;
GRANT ALL ON SCHEMA raw, staging, marts TO airflow_user;

-- Create airflow metadata database
CREATE DATABASE airflow_db;
```

---

## 5. .env FILE

File: `.env`

```env
# PostgreSQL
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=ecommerce_fraud_dw
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# Database URLs
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/ecommerce_fraud_dw
AIRFLOW__CORE__SQL_ALCHEMY_CONN=postgresql+psycopg2://postgres:postgres@localhost:5432/airflow_db

# Paths
DATA_DIR=./data/raw
MODEL_PATH=./ml/models/xgb_model.pkl

# Ollama
OLLAMA_BASE_URL=http://localhost:11434
LLM_MODEL=llama3
```

---

## 6. CHẠY HỆ THỐNG

```bash
# 1. Build all images
docker compose build

# 2. Start all services
docker compose up -d

# 3. Pull Ollama model (chạy sau khi container khởi động)
curl http://localhost:11434/api/pull -d '{"model": "llama3"}'

# 4. Chạy Airflow DAG manually
# Truy cập http://localhost:8080
# Unpause DAG "fraud_detection_pipeline"
# Trigger DAG

# 5. Kiểm tra services
curl http://localhost:8000/health     # ML API
curl http://localhost:8001/health     # AI Assistant
curl http://localhost:3000            # Metabase
curl http://localhost:8080            # Airflow UI
curl http://localhost:11434/api/tags  # Ollama
```

---

## 7. SERVICE ENDPOINTS

| Service | URL | Purpose |
|---------|-----|---------|
| PostgreSQL | localhost:5432 | Data Warehouse |
| Airflow UI | http://localhost:8080 | Pipeline orchestration |
| ML API | http://localhost:8000 | Prediction API |
| AI Assistant | http://localhost:8001 | Chatbot |
| Metabase | http://localhost:3000 | BI Dashboard |
| Ollama | http://localhost:11434 | LLM Backend |

---

## 8. DEPLOYMENT ORDER

```text
1. docker compose up -d postgres    (Database first)
2. docker compose up -d redis      (Redis for Airflow)
3. docker compose up -d ollama     (LLM backend)
4. docker compose up -d airflow-webserver airflow-scheduler (wait for DB health)
5. docker compose up -d metabase   (BI)
6. docker compose up -d ml-api     (ML)
7. docker compose up -d ai-assistant (AI)
8. curl localhost:11434/api/pull... (pull model)
9. Truy cập Airflow UI, trigger DAG
```

---

## 9. SUCCESS CRITERIA

```text
[✅] docker-compose.yml configured with all services
[✅] init_db.sql creates schemas và users
[✅] .env file configured
[✅] docker compose build succeeds
[✅] All services start (postgres, airflow, metabase, ml-api, ai-assistant, ollama)
[✅] PostgreSQL healthcheck passes
[✅] Airflow UI accessible
[✅] Metabase connects to database
[✅] ML API health check returns OK
[✅] AI Assistant health check returns OK
[✅] Ollama model pulled
```

---

## 10. Liên hệ

- Trước: [PHASE 22 — AI Assistant](../22_ai_assistant/ai_assistant.md)
- Sau: [PHASE 24 — End-to-End Pipeline](../24_end_to_end/end_to_end.md)

*Cập nhật: 02/09/2026 | Version: 1.0*
