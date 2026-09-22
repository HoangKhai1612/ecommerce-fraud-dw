# VERIFICATION CHECKLIST

**Dự án:** Ecommerce Fraud Detection Data Warehouse  
**Phase:** 03 — Environment Setup  
**Ngày tạo:** 02/09/2026  

---

## 1. CHECKLIST MÔI TRƯỢC

| # | Công cụ | Verify command | Expected | Status |
|---|---------|----------------|----------|--------|
| 1 | Python | `python --version` | ≥ 3.10 | ✅ 3.14.0 |
| 2 | Docker | `docker --version` | ≥ 25.0 | ✅ 29.6.2 |
| 3 | Docker Compose | `docker compose version` | ≥ 2.0 | ✅ 5.3.1 |
| 4 | Git | `git --version` | ≥ 2.0 | ⚠️ Not in PATH |
| 5 | PostgreSQL | `docker compose ps` | Running | NOT_STARTED |
| 6 | dbt | `dbt --version` | ≥ 1.7 | NOT_STARTED |
| 7 | Airflow | -- | In Docker | NOT_STARTED |
| 8 | Metabase | -- | In Docker | NOT_STARTED |
| 9 | Ollama | `ollama --version` | Latest | NOT_STARTED |

---

## 2. PYTHON ENVIRONMENT VERIFICATION

```bash
# 1. Kích hoạt venv
.venv\Scripts\Activate.ps1

# 2. Kiểm tra version
python --version

# 3. Kiểm tra packages cài đặt
pip list | findstr -i "pandas\|sqlalchemy\|dbt\|scikit\|xgboost\|shap\|fastapi"

# 4. Test import
python -c "import pandas; import sqlalchemy; import sklearn; print('All imports OK')"
```

---

## 3. POSTGRESQL VERIFICATION

```bash
# 1. Khởi động PostgreSQL qua Docker
docker compose up -d postgres

# 2. Kiểm tra container
docker ps | grep postgres

# 3. Kết nối và test
psql -h localhost -U postgres -d ecommerce_fraud_dw -c "SELECT version();"

# 4. Kiểm tra schema
psql -h localhost -U postgres -d ecommerce_fraud_dw -c "\dn"
```

---

## 4. DBT VERIFICATION

```bash
# 1. Cài dbt
pip install dbt-core dbt-postgres

# 2. Chạy debug
dbt debug

# 3. Chạy test
dbt deps
```

---

## 5. ENVIRONMENT FILES VERIFICATION

```bash
# 1. .env tồn tại
Test-Path .env  # Phải trả về True

# 2. .env.example tồn tại
Test-Path .env.example  # Phải trả về True

# 3. .gitignore đã chặn .env
git status --ignored  # .env phải nằm trong ignored
```

---

## 6. DATA FILES VERIFICATION

```bash
# 1. Dataset tồn tại
Test-Path data/raw/train_transaction.csv
Test-Path data/raw/train_identity.csv

# 2. Đọc được
python -c "import pandas as pd; df=pd.read_csv('data/raw/train_transaction.csv', nrows=5); print('Shape:', df.shape)"
```

---

## 7. SUCCESS CRITERIA

```text
[ ] Python 3.10+ installed and in PATH
[ ] Virtual environment created (.venv)
[ ] requirements.txt installed
[ ] Docker Desktop running
[ ] PostgreSQL container running (docker compose up)
[ ] .env and .env.example exist with correct values
[ ] Git configured with user.name and user.email
[ ] Dataset files in data/raw/ readable
```

---

## 8. FAILURE CRITERIA

```text
[ ] Python version < 3.10
[ ] pip install fails
[ ] Docker not running or not installed
[ ] PostgreSQL connection refused
[ ] .env file missing
[ ] Dataset files corrupted or unreadable
```

*Cập nhật: 02/09/2026 | Version: 1.0*
