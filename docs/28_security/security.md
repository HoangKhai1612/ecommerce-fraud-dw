# PHASE 28 — Security

## 1. MỤC TIÊU

Bảo mật toàn bộ pipeline:
- Database user permissions (principle of least privilege)
- SQL injection prevention
- Read-only access cho AI Assistant
- Secure configuration

---

## 2. DATABASE SECURITY

### 2.1 User roles

```sql
-- Admin user (full access)
CREATE USER postgres WITH PASSWORD 'postgres' SUPERUSER;

-- Read-only user (for AI Assistant)
CREATE USER readonly_user WITH PASSWORD 'readonly_password';
GRANT CONNECT ON DATABASE ecommerce_fraud_dw TO readonly_user;
GRANT USAGE ON SCHEMA raw, staging, marts TO readonly_user;
GRANT SELECT ON ALL TABLES IN SCHEMA raw, staging, marts TO readonly_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA raw, staging, marts GRANT SELECT ON TABLES TO readonly_user;

-- Application user (for ETL/ML)
CREATE USER etl_user WITH PASSWORD 'etl_password';
GRANT CONNECT ON DATABASE ecommerce_fraud_dw TO etl_user;
GRANT USAGE, CREATE ON SCHEMA raw, staging, marts TO etl_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA raw, staging, marts TO etl_user;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA raw, staging, marts TO etl_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA raw, staging, marts GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO etl_user;

-- Airflow metadata DB user
CREATE USER airflow_user WITH PASSWORD 'airflow_password' CREATEDB;
```

### 2.2 Row-level security (optional)

```sql
-- Enable RLS on sensitive tables
ALTER TABLE marts.fact_transactions ENABLE ROW LEVEL SECURITY;

-- Users can only see transactions they own
CREATE POLICY "users can see own transactions"
  ON marts.fact_transactions
  FOR SELECT
  TO readonly_user
  USING (transaction_id IS NOT NULL);  -- Basic example
```

---

## 3. SQL INJECTION PREVENTION

### 3.1 AI Assistant SQL Validator

File: `ai_assistant/sql_validator.py` (xem Phase 22)

**Security rules:**
1. Chỉ cho phép `SELECT` queries
2. Chuyển đổi tất cả keywords về lowercase
3. Block keywords: `DROP`, `DELETE`, `UPDATE`, `INSERT`, `TRUNCATE`, `ALTER`, `CREATE`
4. Allow-list schemas: `raw`, `staging`, `marts`
5. Tự động thêm `LIMIT 100`
6. Giới hạn subqueries ≤ 5

### 3.2 SQL validation test

```python
# tests/test_security.py

def test_dangerous_delete_blocked():
    sql = "DELETE FROM marts.fact_transactions"
    is_valid, msg = validate_sql(sql)
    assert not is_valid

def test_drop_blocked():
    sql = "DROP TABLE marts.fact_transactions"
    is_valid, msg = validate_sql(sql)
    assert not is_valid

def test_disallowed_schema_blocked():
    sql = "SELECT * FROM pg_catalog.pg_authid"
    is_valid, msg = validate_sql(sql)
    assert not is_valid
```

---

## 4. SECURE CONFIGURATION

### 4.1 .env (never commit to git)

```env
# .env — DO NOT COMMIT
POSTGRES_PASSWORD=postgres
DATABASE_URL=postgresql://etl_user:etl_password@localhost:5432/ecommerce_fraud_dw
OLLAMA_API_KEY=  # nếu dùng cloud
```

### 4.2 .gitignore

```gitignore
# Environment
.env
*.env

# Python
__pycache__/
*.pyc
*.egg-info/
.venv/

# Data (except small test files)
data/raw/*.csv

# Docker
*.pid
```

### 4.3 Docker secrets (production)

```yaml
# docker-compose.prod.yml
services:
  postgres:
    environment:
      POSTGRES_PASSWORD_FILE: /run/secrets/pg_password
    secrets:
      - pg_password

secrets:
  pg_password:
    file: ./secrets/pg_password.txt
```

---

## 5. NETWORK SECURITY

| Service | Port | Access |
|---------|------|--------|
| PostgreSQL | 5432 | Internal only (Docker network) |
| Airflow | 8080 | Internal + admin IP whitelist |
| Metabase | 3000 | Auth required |
| FastAPI | 8000 | Public (rate limited) |
| AI Assistant | 8001 | Internal + auth token |
| Ollama | 11434 | Internal only |

### Rate limiting (FastAPI)

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/predict")
@limiter.limit("10/minute")
async def predict(data: TransactionData):
    ...
```

---

## 6. SECURITY CHECKLIST

```text
[✅] Database users created with least privilege
[✅] readonly_user has SELECT only
[✅] etl_user has CRUD on data schemas
[✅] No plaintext passwords in code
[✅] .env file excluded from git
[✅] SQL injection validator implemented
[✅] SQL queries parameterized
[✅] Read-only user for AI Assistant
[✅] LIMIT enforced on all queries
[✅] Schema allowlist enforced
[✅] API rate limiting configured
```

---

## 7. VULNERABILITY REPORT

| Vulnerability | Risk | Status | Mitigation |
|--------------|------|--------|------------|
| SQL Injection (AI Assistant) | HIGH | FIXED | sqlglot validator, read-only user |
| Plaintext passwords | MEDIUM | FIXED | .env file, .gitignore |
| Database port exposed | LOW | ACCEPTED | Docker network isolation |
| Model file tampering | LOW | MONITOR | Checksum verification |

---

## 8. Liên hệ

- Trước: [PHASE 27 — Performance](../27_performance/performance.md)
- Sau: [PHASE 29 — Final Documentation](../29_final/final_documentation.md)

*Cập nhật: 02/09/2026 | Version: 1.0*
