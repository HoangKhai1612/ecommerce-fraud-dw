# PHASE 26 — Troubleshooting & Failure Engineering

## 1. MỤC TIÊU

Ghi chép các lỗi thường gặp và cách khắc phục:
- Environment issues
- Pipeline failures
- Performance issues
- Security issues

---

## 2. ISSUE DATABASE

### ISS-001 — PostgreSQL port 5432 conflict

- **Symptoms:** `connection to server at "localhost", port 5432 failed: FATAL`
- **Cause:** PostgreSQL local chạy trùng port với Docker
- **Fix:** `taskkill /PID <postgres_pid> /F`
- **Phase:** PHASE 09

### ISS-002 — dbt schema concatenation

- **Symptoms:** dbt tạo schema `raw_staging` thay vì `staging`
- **Cause:** dbt default macro nối `{target_schema}_{custom_schema}`
- **Fix:** Override `default__generate_schema_name` macro trong `macros/schema_override.sql`
- **Phase:** PHASE 11

### ISS-003 — protobuf incompatible with Python 3.14

- **Symptoms:** `TypeError: Metaclasses with custom tp_new are not supported`
- **Cause:** protobuf 4.x không tương thích Python 3.14
- **Fix:** `pip install --upgrade protobuf`
- **Phase:** PHASE 11

### ISS-004 — File encoding error

- **Symptoms:** `UnicodeDecodeError: 'utf-8' codec can't decode byte`
- **Cause:** CSV file encoding không phải UTF-8
- **Fix:** Thêm `encoding='latin-1'` vào `pd.read_csv()`

### ISS-005 — Memory error loading large CSV

- **Symptoms:** `MemoryError: Unable to allocate` khi load 653MB CSV
- **Cause:** File quá lớn để nạp vào memory
- **Fix:** Sử dụng `chunksize` parameter trong `pd.read_csv()`

### ISS-006 — Ollama model not responding

- **Symptoms:** `Connection refused` khi gọi Ollama API
- **Cause:** Ollama container chưa khởi động hoặc model chưa được pull
- **Fix:** 
  ```bash
  docker compose up -d ollama
  curl http://localhost:11434/api/pull -d '{"model": "llama3"}'
  ```

### ISS-007 — XGBoost tree_method warning

- **Symptoms:** `UserWarning: `tree_method` is deprecated`
- **Fix:** Sử dụng `tree_method='hist'` (default trong phiên bản mới)

### ISS-008 — SQLAlchemy connection pool exhausted

- **Symptoms:** `TimeoutError: QueuePool limit overflow`
- **Fix:** Tăng pool size hoặc đóng connection đúng cách
```python
engine.dispose()  # Đóng sau mỗi lần dùng
```

### ISS-009 — Docker disk space full

- **Symptoms:** Docker stuck ở "Starting"
- **Fix:**
```bash
docker system prune -a --volumes
docker volume prune -f
```

---

## 3. FALLBACK STRATEGIES

| Component | Failure Scenario | Fallback |
|-----------|------------------|----------|
| PostgreSQL | Docker fails | Cài đặt local PG, cập nhật .env |
| Ollama | Model too slow | Dùng DeepSeek API (cloud) hoặc giảm sample_size |
| XGBoost | Training too slow | Dùng subsampling, giảm n_estimators |
| dbt | Parse error | Chạy từng model riêng: `dbt run --select stg_transactions` |
| Airflow | DAG failure | Chạy thủ công từng bước (ingestion → dbt → ml) |

---

## 4. DEBUGGING CHECKLIST

```text
[ ] PostgreSQL running? → docker compose ps
[ ] Port 5432 available? → netstat -an | findstr 5432
[ ] CSV files present? → ls data/raw/
[ ] .env config correct? → cat .env
[ ] dbt connection? → dbt debug
[ ] Model files exist? → ls ml/models/
[ ] API running? → curl http://localhost:8000/health
[ ] Ollama running? → curl http://localhost:11434/api/tags
[ ] Memory usage? → Task Manager / htop
```

---

## 5. LOGGING

Tất cả components phải có logging:

```python
# Python logging standard
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler('logs/pipeline.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)
```

Log files được lưu tại:
- `logs/ingestion.log`
- `dbt/logs/dbt.log`
- `logs/ml_train.log`
- `logs/e2e.log`

---

## 6. PERFORMANCE OPTIMIZATION

| Issue | Solution | Expected Speedup |
|-------|----------|-----------------|
| Large CSV load | Use COPY command | 10x |
| dbt compile slow | Use `--threads 4` | 4x |
| XGBoost training | Use `tree_method='hist'` + `n_jobs=-1` | 3x |
| SHAP explanation | Sample 5,000 rows (not full) | 10x |
| API prediction | Cache model loading | 5x |

---

## 7. Liên hệ

- Trước: [PHASE 25 — Testing](../25_testing/testing.md)
- Sau: [PHASE 27 — Performance](../27_performance/performance.md)

*Cập nhật: 02/09/2026 | Version: 1.0*
