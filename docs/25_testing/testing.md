# PHASE 25 — Testing

## 1. MỤC TIÊU

Xây dựng test suite toàn diện để bảo đảm chất lượng:

| Test Type | Tool | Scope |
|-----------|------|-------|
| Unit Tests | pytest | Individual functions/modules |
| Integration Tests | pytest | Multi-component interaction |
| End-to-End Tests | pytest | Full pipeline |
| Data Quality Tests | dbt test | SQL assertions |
| API Tests | pytest + requests | FastAPI endpoints |
| Security Tests | custom scripts | SQL injection, read-only |

---

## 2. CẤU TRÚC THƯ MỤC

```
tests/
├── __init__.py
├── conftest.py              # Shared fixtures
├── test_ingestion.py        # Phase 09 tests (12 tests)
├── test_end_to_end.py       # E2E pipeline tests
├── test_api.py              # FastAPI endpoint tests
├── test_ml.py               # ML model tests
├── test_dbt.py              # dbt model tests
├── test_security.py         # Security tests
└── fixtures/
    ├── sample_transaction.json
    └── test_queries.sql
```

---

## 3. TEST FILES

### 3.1 conftest.py (shared fixtures)

File: `tests/conftest.py`

```python
"""Shared pytest fixtures."""
import pytest
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DB_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/ecommerce_fraud_dw")


@pytest.fixture(scope="session")
def engine():
    """Database engine fixture."""
    eng = create_engine(DB_URL)
    yield eng
    eng.dispose()


@pytest.fixture
def sample_transaction():
    """Sample transaction data."""
    return {
        "TransactionID": 3561737,
        "TransactionDT": 86400,
        "TransactionAmt": 49.5,
        "ProductCD": "W",
        "card1": 567,
        "card2": 100.0,
        "card3": 200.0,
        "card4": "Visa",
        "card5": 134.0,
        "card6": "credit",
    }
```

### 3.2 test_ingestion.py (12 tests)

File: `tests/test_ingestion.py` — xem Phase 09 docs để biết code

### 3.3 test_ml.py

File: `tests/test_ml.py`

```python
"""Tests cho ML models."""
import pytest
import joblib
import pandas as pd
import numpy as np
import os


class TestMLModels:

    @pytest.fixture(autouse=True)
    def load_artifacts(self):
        """Load model artifacts."""
        self.model = joblib.load('ml/models/xgb_model.pkl')
        self.feature_cols = joblib.load('ml/models/feature_cols.pkl')
        self.scaler = joblib.load('ml/models/scaler.pkl')

    def test_models_exist(self):
        """Kiểm tra model files tồn tại."""
        assert os.path.exists('ml/models/xgb_model.pkl')
        assert os.path.exists('ml/models/rf_model.pkl')
        assert os.path.exists('ml/models/lr_model.pkl')
        assert os.path.exists('ml/models/feature_cols.pkl')

    def test_model_predict_proba(self):
        """Model có thể predict probability."""
        test_df = pd.read_parquet('ml/data/test.parquet')
        X = test_df[self.feature_cols].select_dtypes(include=['int64', 'float64'])
        
        # Handle bool
        bool_cols = X.select_dtypes(include=['bool']).columns
        for col in bool_cols:
            X[col] = X[col].astype(int)
        
        proba = self.model.predict_proba(X)[:, 1]
        assert len(proba) > 0
        assert all(0 <= p <= 1 for p in proba)

    def test_model_accuracy_threshold(self):
        """Model AUC phải >= 0.90."""
        from sklearn.metrics import roc_auc_score
        test_df = pd.read_parquet('ml/data/test.parquet')
        X = test_df[self.feature_cols].select_dtypes(include=['int64', 'float64'])
        
        bool_cols = X.select_dtypes(include=['bool']).columns
        for col in bool_cols:
            X[col] = X[col].astype(int)
        
        proba = self.model.predict_proba(X)[:, 1]
        auc = roc_auc_score(test_df['is_fraud'], proba)
        assert auc >= 0.90, f"AUC too low: {auc}"


class TestMLData:

    def test_train_test_split_ratio(self):
        """Kiểm tra tỷ lệ chia 70/15/15."""
        train = pd.read_parquet('ml/data/train.parquet')
        val = pd.read_parquet('ml/data/val.parquet')
        test = pd.read_parquet('ml/data/test.parquet')
        
        total = len(train) + len(val) + len(test)
        train_ratio = len(train) / total
        val_ratio = len(val) / total
        test_ratio = len(test) / total
        
        assert 0.68 <= train_ratio <= 0.72
        assert 0.13 <= val_ratio <= 0.17
        assert 0.13 <= test_ratio <= 0.17

    def test_stratified_split(self):
        """Kiểm tra fraud rate giống nhau trong 3 splits."""
        train = pd.read_parquet('ml/data/train.parquet')
        val = pd.read_parquet('ml/data/val.parquet')
        test = pd.read_parquet('ml/data/test.parquet')
        
        train_rate = train['is_fraud'].mean()
        val_rate = val['is_fraud'].mean()
        test_rate = test['is_fraud'].mean()
        
        # Rates should be within 0.5% of each other
        assert abs(train_rate - val_rate) < 0.005
        assert abs(train_rate - test_rate) < 0.005
```

### 3.4 test_api.py

File: `tests/test_api.py`

```python
"""Tests cho FastAPI endpoints."""
import pytest
import requests
from fastapi.testclient import TestClient
import sys
import os

# Add api to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'api'))
from main import app

client = TestClient(app)


class TestAPI:

    def test_health_check(self):
        response = requests.get("http://localhost:8000/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    def test_predict_endpoint(self, sample_transaction):
        response = requests.post(
            "http://localhost:8000/predict",
            json=sample_transaction
        )
        assert response.status_code == 200
        data = response.json()
        assert "fraud_probability" in data
        assert 0 <= data["fraud_probability"] <= 1
        assert data["transaction_id"] == sample_transaction["TransactionID"]

    def test_transaction_lookup(self):
        response = requests.get("http://localhost:8000/transactions/3561737")
        assert response.status_code == 200
        data = response.json()
        assert "transaction_id" in data

    def test_top_predictions(self):
        response = requests.get("http://localhost:8000/transactions/predictions/top?limit=5")
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 5
```

### 3.5 test_security.py

File: `tests/test_security.py`

```python
"""Security tests cho AI Assistant SQL validation."""
import pytest
from sql_validator import validate_sql


class TestSQLValidation:

    def test_dangerous_delete_blocked(self):
        sql = "DELETE FROM raw.transactions"
        is_valid, msg = validate_sql(sql)
        assert not is_valid
        assert "DELETE" in msg

    def test_dangerous_drop_blocked(self):
        sql = "DROP TABLE raw.transactions"
        is_valid, msg = validate_sql(sql)
        assert not is_valid
        assert "DROP" in msg

    def test_select_allowed(self):
        sql = "SELECT * FROM marts.fact_transactions LIMIT 10"
        is_valid, msg = validate_sql(sql)
        assert is_valid

    def test_disallowed_schema_blocked(self):
        sql = "SELECT * FROM public.users"
        is_valid, msg = validate_sql(sql)
        assert not is_valid
        assert "not allowed" in msg.lower()

    def test_limit_injected(self):
        sql = "SELECT * FROM marts.fact_transactions"
        is_valid, validated = validate_sql(sql)
        assert "LIMIT" in validated.upper()
```

---

## 4. CHẠY TESTS

```bash
# Chạy tất cả tests
pytest tests/ -v

# Chạy theo category
pytest tests/test_ingestion.py -v
pytest tests/test_ml.py -v
pytest tests/test_api.py -v
pytest tests/test_security.py -v

# Chạy với coverage
pytest tests/ --cov=. --cov-report=html

# Chạy end-to-end (cần dịch vụ đang chạy)
pytest tests/test_end_to_end.py -v
```

---

## 5. CI/CD (GitHub Actions)

File: `.github/workflows/ci.yml`

```yaml
name: CI Pipeline

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_USER: postgres
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: ecommerce_fraud_dw
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.10'
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install pytest pytest-cov
      
      - name: Wait for PostgreSQL
        run: |
          until pg_isready -h localhost -p 5432; do sleep 1; done
      
      - name: Run tests
        run: |
          pytest tests/test_ingestion.py -v
          pytest tests/test_ml.py -v
          pytest tests/test_security.py -v
```

---

## 6. TEST METRICS

| Category | Tests | Target Pass % |
|----------|-------|---------------|
| Ingestion | 12 | 100% |
| E2E Pipeline | 7 | 100% |
| ML | 3 | 90%+ |
| API | 4 | 90%+ |
| Security | 5 | 100% |
| Data Quality (dbt) | 8+ | 95%+ |
| **Total** | **~39+** | **95%+** |

---

## 7. SUCCESS CRITERIA

```text
[✅] All test files created (7 files)
[✅] pytest runs without import errors
[✅] Ingestion tests: 12/12 pass
[✅] ML tests: 3/3 pass
[✅] API tests: 4/4 pass (when services running)
[✅] Security tests: 5/5 pass
[✅] E2E tests: 7/7 pass
[✅] Coverage report generated
[✅] CI/CD pipeline configured
```

---

## 8. Liên hệ

- Trước: [PHASE 24 — End-to-End Pipeline](../24_end_to_end/end_to_end.md)
- Sau: [PHASE 26 — Troubleshooting](../26_troubleshooting/troubleshooting.md)

*Cập nhật: 02/09/2026 | Version: 1.0*
