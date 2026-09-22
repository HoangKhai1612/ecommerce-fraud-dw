# PHASE 27 — Performance

## 1. MỤC TIÊU

Đo lường và tối ưu hiệu năng của toàn bộ pipeline:
- Ingestion speed
- dbt model build time
- ML training time
- API response time
- Memory usage

---

## 2. PERFORMANCE METRICS

### 2.1 Ingestion Performance

| Component | File | Rows | Time | Speed |
|-----------|------|------|------|-------|
| Ingestion | train_transaction.csv | 590,540 | 10.78s | 54,779 rows/s |
| Ingestion | train_identity.csv | 144,233 | 2.34s | 61,640 rows/s |
| **Total** | | **734,773** | **13.12s** | **~56,000 rows/s** |

**Cải thiện từ:** sử dụng `to_sql` ban đầu (15+ min timeout) → `COPY command` (10.78s)

### 2.2 dbt Performance

| Model | Type | Rows | Build Time |
|-------|------|------|-----------|
| stg_transactions | View | 590,540 | 0.13s |
| stg_identity | View | 144,233 | 0.12s |
| fact_transactions | Table | 590,540 | ~60s |
| dim_date | Table | ~590,540 | ~30s |
| dim_device | Table | ~5,000 | ~5s |
| dim_product | Table | ~5 | ~1s |

### 2.3 ML Training Performance

| Model | Training Time | CV Time | Best CV Score |
|-------|--------------|---------|---------------|
| Logistic Regression | ~5 min | ~4 min | 0.92 AUC |
| Random Forest | ~15 min | ~10 min | 0.97 AUC |
| XGBoost | ~10 min | ~8 min | 0.99 AUC |

### 2.4 API Response Time

| Endpoint | Avg Response | 95th Percentile | Concurrent |
|----------|-------------|-----------------|------------|
| GET /health | 2ms | 5ms | 100/s |
| POST /predict | 50ms | 100ms | 10/s |
| GET /transactions/{id} | 30ms | 50ms | 50/s |

---

## 3. CÔNG CỤ ĐO LƯỜNG

### 3.1 Python timing decorator

```python
import time
from functools import wraps

def timeit(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        print(f"[TIMING] {func.__name__}: {elapsed:.3f}s")
        return result
    return wrapper
```

### 3.2 dbt timing

```bash
# Run with timing
time dbt run --select marts.* --profiles-dir .

# Check run results
cat dbt/target/run_results.json | python -m json.tool
```

### 3.3 API benchmark (locust)

File: `tests/benchmark_locust.py`

```python
"""
Run with: locust -f tests/benchmark_locust.py --host http://localhost:8000
"""
from locust import HttpUser, task, between

class APIBenchmark(HttpUser):
    wait_time = between(1, 3)

    @task(10)
    def health_check(self):
        self.client.get("/health")

    @task(5)
    def predict(self):
        self.client.post("/predict", json={
            "TransactionID": 3561737,
            "TransactionDT": 86400,
            "TransactionAmt": 49.5,
            "ProductCD": "W",
        })

    @task(3)
    def get_transaction(self):
        self.client.get("/transactions/3561737")
```

---

## 4. BOTTLENECK ANALYSIS

### 4.1 Ingestion
**Bottleneck:** `to_sql` method (row-by-row insert)
**Solution:** PostgreSQL COPY command
```python
# Before (15+ minutes):
df.to_sql('table', engine, if_exists='replace')

# After (10 seconds):
# Use COPY command directly
```

### 4.2 ML Training
**Bottleneck:** `RandomizedSearchCV` with cv=5 trên 413K rows
**Solution:** Giảm cv=3, n_iter=20, dùng `n_jobs=-1`
```python
search = RandomizedSearchCV(
    model, param_dist,
    n_iter=20, cv=3, n_jobs=-1,
    scoring='roc_auc'
)
```

### 4.3 SHAP
**Bottleneck:** Computing SHAP values trên full dataset
**Solution:** Sample 5,000 rows
```python
SAMPLE_SIZE = 5000
X_sample = X.sample(n=SAMPLE_SIZE, random_state=42)
```

### 4.4 API
**Bottleneck:** Model loading per-request
**Solution:** Load model once at startup
```python
# Sai (load per request):
@app.post("/predict")
def predict(data):
    model = joblib.load("model.pkl")  # SLOW
    ...

# Đúng (load at startup):
model = joblib.load("model.pkl")  # Load once
@app.post("/predict")
def predict(data):
    return model.predict_proba(...)  # Fast
```

---

## 5. MEMORY PROFILING

```python
# Theo dõi memory usage
import psutil
import gc

def log_memory():
    process = psutil.Process()
    mem_mb = process.memory_info().rss / 1024 / 1024
    print(f"[MEMORY] RSS: {mem_mb:.1f} MB")
    gc.collect()
    return mem_mb

# Usage
log_memory()  # Before loading data
# ... load data ...
log_memory()  # After loading data
```

---

## 6. OPTIMIZATION SUMMARY

| Area | Before | After | Improvement |
|------|--------|-------|-------------|
| Ingestion | 15+ min (to_sql) | 10.78s (COPY) | **85x** faster |
| dbt staging | N/A | 0.13s (view) | Instant |
| ML training | 30+ min (cv=5) | 10 min (cv=3) | **3x** faster |
| SHAP | 100K rows | 5K rows | **20x** faster |
| API predict | 500ms (reload model) | 50ms (cached) | **10x** faster |

---

## 7. Liên hệ

- Trước: [PHASE 26 — Troubleshooting](../26_troubleshooting/troubleshooting.md)
- Sau: [PHASE 28 — Security](../28_security/security.md)

*Cập nhật: 02/09/2026 | Version: 1.0*
