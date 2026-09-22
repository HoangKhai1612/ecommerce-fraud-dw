# TROUBLESHOOTING

**Dự án:** Ecommerce Fraud Detection Data Warehouse  
**Phase:** 03 — Environment Setup  
**Ngày tạo:** 02/09/2026  

---

## 1. PYTHON VENV ACTIVATION ERROR

### Vấn đề:
```
execution of scripts disabled on this system
```

### Nguyên nhân:
PowerShell bảo mật chặn script execution.

### Cách sửa:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.venv\Scripts\Activate.ps1
```

---

## 2. PORT 5432 BỊ CHIẾM

### Vấn đề:
```
could not bind to IPv4 address "0.0.0.0":5432 — Address already in use
```

### Nguyên nhân:
PostgreSQL hoặc service khác đang dùng port 5432.

### Cách sửa:
```powershell
# Kiểm tra công dụ đang dùng port 5432
netstat -ano | findstr :5432

# Dừng service
docker stop <container_name>
# Hoặc thay đổi port trong .env
POSTGRES_PORT=5433
```

---

## 3. DOCKER OUT OF MEMORY

### Vấn đề:
Docker container bị kill do hết RAM.

### Cách sửa:
```yaml
# Trong docker-compose.yml, thêm resource limits:
services:
  postgres:
    deploy:
      resources:
        limits:
          memory: 2G
```

Hoặc tắt service không dùng (Metabase, Airflow).

---

## 4. PIP INSTALL FAIL

### Vấn đề:
```
ERROR: Could not find a version that satisfies the requirement
```

### Cách sửa:
```bash
# Nâp cấp pip
python -m pip install --upgrade pip

# Cài lại
pip install -r requirements.txt
```

---

## 5. DATABASE CONNECTION FAIL

### Vấn đề:
```
psycopg2.OperationalError: could not connect to server
```

### Cách sửa:
1. Kiểm tra Docker container đang chạy:
   ```bash
   docker ps | grep postgres
   ```
2. Kiểm tra file `.env` có đúng giá trị không
3. Restart container:
   ```bash
   docker compose restart postgres
   ```

---

## 6. DBT CONNECTION FAIL

### Vấn đề:
```
Runtime Error
  Credentials in profile "ecommerce_fraud_dw", target "dev" invalid: Runtime Error
    Database Error
      28000: FATAL:  password authentication failed for user "postgres"
```

### Cách sửa:
1. Kiểm tra `.env` file
2. Restart PostgreSQL container
3. Kiểm tra `dbt/profiles.yml` đúng user/password

---

## 7. GIT NOT FOUND

### Vấn đề:
```
git : The term 'git' is not recognized
```

### Cách sửa:
- Cài Git từ [git-scm.com](https://git-scm.com/download/win)
- Thêm vào PATH hoặc restart terminal

---

## 8. CSV ENCODING ERROR

### Vấn đề:
```
UnicodeDecodeError: 'utf-8' codec can't decode byte
```

### Cách sửa:
Trong `load_raw.py`, thêm `encoding='utf-8'` hoặc `encoding='latin-1'`:
```python
pd.read_csv(path, encoding='utf-8')
```

---

## 9. AIRFLOW DAG IMPORT ERROR

### Vấn đề:
```
Broken DAG: ModuleNotFoundError
```

### Cách sửa:
1. Kiểm tra dependencies trong Dockerfile của Airflow
2. Cài đặt packages vào Airflow container
3. Test DAG locally: `python -c "from airflow.models import DAG; ..."`

*Cập nhật: 02/09/2026 | Version: 1.0*
