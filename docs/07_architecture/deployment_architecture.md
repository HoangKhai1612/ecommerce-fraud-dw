# DEPLOYMENT ARCHITECTURE

**Dự án:** Ecommerce Fraud Detection Data Warehouse  
**Phase:** 07 — System Architecture  
**Ngày tạo:** 02/09/2026  

---

## 1. DEPLOYMENT OVERVIEW

Hệ thống được triển khai trên môi trường **local development** bằng Docker Compose.

```text
┌──────────────────────────────────────────────────────────┐
│                    HOST MACHINE                          │
│  (Windows, RAM ≥ 8GB, Docker Desktop)                   │
│                                                          │
│  ┌────────────────────────────────────────────────────┐  │
│  │  Docker Compose Network (fraud-dw-net)              │  │
│  │                                                    │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐         │  │
│  │  │ PostgreSQL│  │ Airflow  │  │ Metabase │         │  │
│  │  │  :5432   │  │   :8080  │  │   :3000  │         │  │
│  │  └──────────┘  └──────────┘  └──────────┘         │  │
│  │                                                    │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐         │  │
│  │  │ FastAPI  │  │ Ollama   │  │  ──ext─   │         │  │
│  │  │   :8000  │  │  :11434  │  │  Other   │         │  │
│  │  └──────────┘  └──────────┘  └──────────┘         │  │
│  └────────────────────────────────────────────────────┘  │
│                                                          │
│  ┌────────────────────────────────────────────────────┐  │
│  │  Local Python (outside Docker)                      │  │
│  │  ├─ ml/ scripts (train, predict, shap)               │  │
│  │  └─ ingestion/load_raw.py (có thể chạy local)       │  │
│  └────────────────────────────────────────────────────┘  │
│                                                          │
│  ┌────────────────────────────────────────────────────┐  │
│  │  Data Files                                         │  │
│  │  └─ data/raw/*.csv (NOT in Docker, mounted)         │  │
│  └────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
```

---

## 2. DOCKER COMPOSE SERVICES

| Service | Image | Port | Volume | Purpose |
|---------|-------|------|--------|---------|
| `postgres` | postgres:15-alpine | 5432 | postgres_data | Main database |
| `postgres_readonly` | postgres:15-alpine | (share 5432) | postgres_data | Read-only user (same DB) |
| `airflow-postgres` | postgres:15-alpine | 5433 | airflow_pg_data | Airflow metadata DB |
| `airflow-webserver` | apache/airflow:2.8.0 | 8080 | -- | Airflow UI |
| `airflow-scheduler` | apache/airflow:2.8.0 | -- | -- | Airflow scheduler |
| `metabase` | metabase/metabase:v0.49.0 | 3000 | metabase_data | BI Dashboard |
| `api` | custom (Python/FastAPI) | 8000 | ./data:/app/data | REST API |
| `ollama` | ollama/ollama | 11434 | ollama_data | LLM service |

---

## 3. PORT MAPPING

| Service | Host Port | Container Port | URL |
|---------|-----------|----------------|-----|
| PostgreSQL | 5432 | 5432 | `postgresql://localhost:5432/ecommerce_fraud_dw` |
| Airflow Web | 8080 | 8080 | http://localhost:8080 |
| Airflow DB | 5433 | 5432 | (internal only) |
| Metabase | 3000 | 3000 | http://localhost:3000 |
| FastAPI | 8000 | 8000 | http://localhost:8000 |
| Ollama | 11434 | 11434 | http://localhost:11434 |

---

## 4. VOLUME MANAGEMENT

| Volume | Mount Path | Purpose | Backup |
|--------|-----------|---------|--------|
| postgres_data | /var/lib/postgresql/data | PostgreSQL data | Docker volume |
| airflow_pg_data | /var/lib/postgresql/data | Airflow metadata | Docker volume |
| metabase_data | /metabase-data | Metabase DB + settings | Docker volume |
| ollama_data | /root/.ollama | Ollama models | Docker volume |
| (local) ./data | /app/data | Dataset CSV files | Local disk |
| (local) ./ml | /app/ml | Model artifacts | Local disk |

---

## 5. NETWORK CONFIG

```yaml
networks:
  fraud-dw-net:
    driver: bridge
    name: fraud_dw_network
```

- Tất cả services nằm trên cùng network
- Services giao tiếp qua service name (ví dụ: `postgres`, `airflow-postgres`)
- FastAPI và ML scripts kết nối đến PostgreSQL qua `localhost:5432` (port mapping)

---

## 6. DEPLOYMENT STEPS

### Step 1: Setup .env
```bash
cp .env.example .env
# Edit .env with correct values
```

### Step 2: Start core services
```bash
docker compose up -d postgres
# Wait for health check
```

### Step 3: Run ingestion
```bash
python ingestion/load_raw.py
```

### Step 4: Start all services
```bash
docker compose up -d
# PostgreSQL, Airflow, Metabase, API, Ollama
```

### Step 5: Verify
```bash
docker compose ps        # All services running
docker compose logs      # Check logs
```

---

## 7. ENVIRONMENTS

| Environment | Deployment | Purpose |
|-------------|-----------|---------|
| Development | Docker Compose local | Coding, testing, demo |
| (Future) Production | N/A | Out of scope |

---

## 8. BACKUP & RECOVERY

| Component | Backup Strategy |
|-----------|----------------|
| PostgreSQL | `docker exec postgres pg_dump` |
| Model artifacts | Git lfs hoặc local backup |
| Dataset | Local disk (already downloaded) |
| Metabase | Export dashboard as JSON |
| Airflow | Export DAG files |

*Cập nhật: 02/09/2026 | Version: 1.0*
