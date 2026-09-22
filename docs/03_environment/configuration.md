# CONFIGURATION

**Dự án:** Ecommerce Fraud Detection Data Warehouse  
**Phase:** 03 — Environment Setup  
**Ngày tạo:** 02/09/2026  

---

## 1. BIẾN MÔI TRƯỜNG (.env)

Dự án sử dụng file `.env` để quản lý tất cả cấu hình. **KHÔNG bao giờ commit `.env` vào Git.**

### File `.env.example`:
```env
# POSTGRES CONFIG
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=ecommerce_fraud_dw
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# POSTGRES READ-ONLY USER FOR AI ASSISTANT
POSTGRES_RO_USER=ai_assistant_ro
POSTGRES_RO_PASSWORD=ai_assistant_ro_pass

# AIRFLOW CONFIG
AIRFLOW_ADMIN_USER=admin
AIRFLOW_ADMIN_PASSWORD=admin
AIRFLOW_WWW_USER_CREATE=true

# FASTAPI CONFIG
API_HOST=0.0.0.0
API_PORT=8000

# LLM / AI ASSISTANT CONFIG
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3
OPENAI_API_KEY=your_openai_api_key_here

# METABASE CONFIG
METABASE_PORT=3000

# SYSTEM PATHS
DATA_DIR=./data/raw
MODEL_DIR=./ml/saved_models
```

### Cách dùng:
```bash
# Copy từ .env.example
cp .env.example .env

# Sửa giá trị tùy môi trường
# .env được tự động load bởi python-dotenv
```

---

## 2. CẤU HÌNH DBT

### `dbt/dbt_project.yml`:
```yaml
name: ecommerce_fraud_dw
version: "1.0"
profile: ecommerce_fraud_dw
config-version: 2
model-paths: ["models"]
seed-paths: ["seeds"]
test-paths: ["tests"]
```

### `dbt/profiles.yml` (kết nối đến PostgreSQL):
```yaml
ecommerce_fraud_dw:
  target: dev
  outputs:
    dev:
      type: postgres
      host: localhost
      user: ${POSTGRES_USER}
      password: ${POSTGRES_PASSWORD}
      port: 5432
      dbname: ${POSTGRES_DB}
      schema: marts
      threads: 4
```

---

## 3. CẤU HÌNH AIRFLOW

### `airflow/airflow.cfg`:
- `executor = LocalExecutor` (cho development)
- `fernet_key` — để mã hóa connection
- `sql_alchemy_conn` — kết nối PostgreSQL

### Environment variables cho Airflow:
```env
AIRFLOW__CORE__EXECUTOR=LocalExecutor
AIRFLOW__CORE__SQL_ALCHEMY_CONN=postgresql+psycopg2://postgres:postgres@postgres:5432/airflow
```

---

## 4. CẤU HÌNH FASTAPI

### `api/config.py`:
```python
from dotenv import load_dotenv
load_dotenv()

API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", 8000))
```

---

## 5. CẤU HÌNH AI ASSISTANT

### `ai_assistant/config.py`:
```python
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# Read-only database connection
POSTGRES_RO_USER = os.getenv("POSTGRES_RO_USER", "ai_assistant_ro")
POSTGRES_RO_PASSWORD = os.getenv("POSTGRES_RO_PASSWORD", "ai_assistant_ro_pass")
```

---

## 6. CẤU HÌNH DOCKER COMPOSE

File `docker-compose.yml` định nghĩa các service:
| Service | Port | Volume | Purpose |
|---------|------|--------|---------|
| postgres | 5432 | postgres_data | Main database |
| airflow-postgres | 5433 | airflow_pg_data | Airflow metadata DB |
| airflow-webserver | 8080 | -- | Airflow UI |
| airflow-scheduler | -- | -- | Airflow scheduler |
| metabase | 3000 | metabase_data | BI Dashboard |
| api | 8000 | -- | FastAPI service |
| ollama | 11434 | ollama_data | LLM service |

---

## 7. PYTHON PATH CONFIG

Tạo `.env` và chạy:
```bash
# Kích hoạt virtual environment
.venv\Scripts\Activate.ps1

# Cài đặt packages
pip install -r requirements.txt
```

*Cập nhật: 02/09/2026 | Version: 1.0*
