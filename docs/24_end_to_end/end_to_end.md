# PHASE 24 — End-to-End Pipeline

## 1. MỤC TIÊU

Chạy toàn bộ pipeline end-to-end từ đầu đến cuối:
1. Ingestion (CSV → PostgreSQL RAW)
2. dbt (RAW → Staging → Star Schema)
3. Data Quality checks
4. ML Training (3 models)
5. Prediction (apply model, store results)
6. SHAP explanation
7. API serving (FastAPI)
8. Dashboard (Metabase)

---

## 2. PIPELINE FLOW

```text
[CSV files in data/raw/]
        ↓ (1) Ingestion
[ingestion/load_raw.py]
        ↓
[raw.transactions, raw.identity]
        ↓ (2) dbt Staging
[dbt run --select staging.*]
        ↓
[staging.stg_transactions, staging.stg_identity]
        ↓ (2b) dbt Marts (Star Schema)
[dbt run --select marts.*]
        ↓
[marts.fact_transactions, dim_date, dim_device, dim_product]
        ↓ (3) Data Quality
[dbt test]
        ↓ (4) ML Training
[ml/train.py]
        ↓
[ml/models/xgb_model.pkl]
        ↓ (5) Prediction
[ml/predict.py]
        ↓
[marts.predictions]
        ↓ (6) SHAP
[ml/shap_explain.py]
        ↓
[ml/models/shap_*.png]
        ↓ (7) API
[uvicorn main:app --port 8000]
        ↓
[POST /predict, GET /transactions/{id}]
        ↓ (8) Dashboard
[Metabase: http://localhost:3000]
        ↓
[Visualizations, SQL queries]
```

---

## 3. END-TO-END TEST SCRIPT

File: `tests/test_end_to_end.py`

```python
"""
Phase 24: End-to-End Pipeline Test
Chạy toàn bộ pipeline từ ingestion đến prediction.
"""

import subprocess
import os
import pandas as pd
import pytest
import psycopg2
from sqlalchemy import create_engine, text

DB_URL = "postgresql://postgres:postgres@localhost:5432/ecommerce_fraud_dw"


class TestEndToEndPipeline:
    """Full pipeline test — chạy tuần tự từng bước."""

    def test_step_01_postgres_running(self):
        """Step 1: PostgreSQL is running."""
        engine = create_engine(DB_URL)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1")).scalar()
            assert result == 1
        engine.dispose()

    def test_step_02_ingestion(self):
        """Step 2: Ingestion completed — RAW tables have data."""
        # Chạy ingestion script
        result = subprocess.run(
            ["python", "ingestion/load_raw.py"],
            capture_output=True,
            text=True,
            cwd=os.getcwd()
        )
        assert result.returncode == 0, f"Ingestion failed: {result.stderr}"

        # Verify
        engine = create_engine(DB_URL)
        with engine.connect() as conn:
            trans_count = conn.execute(text("SELECT COUNT(*) FROM raw.transactions")).scalar()
            identity_count = conn.execute(text("SELECT COUNT(*) FROM raw.identity")).scalar()

        assert trans_count == 590540, f"Expected 590540, got {trans_count}"
        assert identity_count == 144233, f"Expected 144233, got {identity_count}"
        engine.dispose()

    def test_step_03_dbt_staging(self):
        """Step 3: dbt staging models built."""
        result = subprocess.run(
            ["dbt", "run", "--select", "staging.*"],
            capture_output=True,
            text=True,
            cwd="dbt"
        )
        assert result.returncode == 0, f"dbt staging failed: {result.stderr}"

        engine = create_engine(DB_URL)
        with engine.connect() as conn:
            count = conn.execute(text("SELECT COUNT(*) FROM staging.stg_transactions")).scalar()
        assert count == 590540, f"Staging row count mismatch: {count}"
        engine.dispose()

    def test_step_04_dbt_marts(self):
        """Step 4: dbt marts models built."""
        result = subprocess.run(
            ["dbt", "run", "--select", "marts.*"],
            capture_output=True,
            text=True,
            cwd="dbt"
        )
        assert result.returncode == 0, f"dbt marts failed: {result.stderr}"

        engine = create_engine(DB_URL)
        with engine.connect() as conn:
            count = conn.execute(text("SELECT COUNT(*) FROM marts.fact_transactions")).scalar()
        assert count == 590540, f"Fact table row count mismatch: {count}"
        engine.dispose()

    def test_step_05_ml_prediction(self):
        """Step 5: ML predictions stored in database."""
        # Check predictions table exists and has data
        engine = create_engine(DB_URL)
        with engine.connect() as conn:
            count = conn.execute(text("SELECT COUNT(*) FROM marts.predictions")).scalar()
        assert count > 0, "No predictions in marts.predictions"
        engine.dispose()

    def test_step_06_api_health(self):
        """Step 6: ML API health check."""
        import requests
        response = requests.get("http://localhost:8000/health", timeout=10)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"

    def test_step_07_api_prediction(self):
        """Step 7: API prediction endpoint works."""
        import requests
        response = requests.post(
            "http://localhost:8000/predict",
            json={
                "TransactionID": 9999999,
                "TransactionDT": 86400,
                "TransactionAmt": 100.0,
                "ProductCD": "W",
            },
            timeout=30
        )
        assert response.status_code == 200
        data = response.json()
        assert "fraud_probability" in data
        assert 0 <= data["fraud_probability"] <= 1
```

---

## 4. RUN END-TO-END

```bash
# 1. Start services
docker compose up -d postgres

# 2. Run pipeline steps
.venv\Scripts\activate

# Step 1: Ingestion
python ingestion/load_raw.py

# Step 2: dbt staging
cd dbt && dbt run --select staging.* && cd ..

# Step 3: dbt marts
cd dbt && dbt run --select marts.* && cd ..

# Step 4: dbt tests
cd dbt && dbt test && cd ..

# Step 5: ML training
cd ml && python train.py && cd ..

# Step 6: ML evaluation
cd ml && python evaluate.py && cd ..

# Step 7: Predictions
cd ml && python predict.py && cd ..

# Step 8: SHAP
cd ml && python shap_explain.py && cd ..

# Step 9: Run E2E tests
pytest tests/test_end_to_end.py -v
```

---

## 5. AIRFLOW ORCHESTRATION

Toàn bộ pipeline trên có thể được thực hiện qua Airflow DAG:

```bash
# Trigger DAG từ CLI
airflow dags trigger fraud_detection_pipeline

# Monitor
airflow tasks list fraud_detection_pipeline
airflow tasks state fraud_detection_pipeline $(date +%Y-%m-%d)
```

---

## 6. SUCCESS CRITERIA

```text
[✅] Step 1: PostgreSQL running
[✅] Step 2: Ingestion completes (raw tables populated)
[✅] Step 3: dbt staging models built
[✅] Step 4: dbt marts models built (fact + dim tables)
[✅] Step 5: ML models trained AND predictions stored
[✅] Step 6: ML API health check passes
[✅] Step 7: API prediction endpoint works
[✅] End-to-end pytest passes (7/7)
```

---

## 7. Liên hệ

- Trước: [PHASE 23 — Docker Compose](../23_docker/docker_compose.md)
- Sau: [PHASE 25 — Testing](../25_testing/testing.md)

*Cập nhật: 02/09/2026 | Version: 1.0*
