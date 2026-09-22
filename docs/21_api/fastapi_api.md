# PHASE 21 — FastAPI

## 1. MỤC TIÊU

Xây dựng API REST bằng FastAPI để:
- API health check
- Dự đoán gian lận cho 1 giao dịch
- Lấy thông tin giao dịch từ database
- Swagger UI tự động

---

## 2. CÀI ĐẶT

```bash
.venv\Scripts\Activate.ps1
pip install fastapi uvicorn pydantic python-multipart

# Hoặc dùng Docker (recommended cho production)
```

---

## 3. CẤU TRÚC THƯ MỤC

```
api/
├── main.py              # FastAPI app
├── models.py            # Pydantic models
├── database.py          # Database connection
├── routes/
│   ├── predict.py       # Prediction endpoint
│   ├── transactions.py  # Transaction lookup
│   └── health.py        # Health check
├── requirements.txt
└── Dockerfile
```

---

## 4. CODE

### 4.1 requirements.txt

File: `api/requirements.txt`

```txt
fastapi==0.109.2
uvicorn==0.27.0
pydantic==2.6.1
python-multipart==0.0.9
psycopg2-binary==2.9.12
pandas==2.2.0
scikit-learn==1.4.0
joblib==1.3.0
```

### 4.2 database.py

File: `api/database.py`

```python
"""Database connection utility."""
from sqlalchemy import create_engine, text
from contextlib import contextmanager
import os

DB_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/ecommerce_fraud_dw"
)

engine = create_engine(DB_URL, pool_pre_ping=True)

@contextmanager
def get_db():
    """Context manager for database connection."""
    conn = engine.connect()
    try:
        yield conn
    finally:
        conn.close()
```

### 4.3 models.py

File: `api/models.py`

```python
"""Pydantic models for API."""
from pydantic import BaseModel, Field
from typing import Optional, List

class TransactionData(BaseModel):
    """Input data for fraud prediction."""
    TransactionID: int
    TransactionDT: int
    TransactionAmt: float
    ProductCD: str
    card1: Optional[int] = None
    card2: Optional[float] = None
    card3: Optional[float] = None
    card4: Optional[str] = None
    card5: Optional[float] = None
    card6: Optional[str] = None
    addr1: Optional[int] = None
    addr2: Optional[int] = None
    dist1: Optional[float] = None
    dist2: Optional[float] = None
    P_emaildomain: Optional[str] = None
    R_emaildomain: Optional[str] = None
    # Add C1-C14, D1-D15, M1-M9, V1-V339 as needed...

class PredictionResponse(BaseModel):
    """Response model for prediction."""
    transaction_id: int
    is_fraud: int
    fraud_probability: float
    risk_level: str  # low/medium/high
    message: str

class TransactionResponse(BaseModel):
    """Response model for transaction lookup."""
    transaction_id: int
    is_fraud: int
    transaction_amt: float
    product_cd: str
    # ... more fields
```

### 4.4 routes/predict.py

File: `api/routes/predict.py`

```python
"""Prediction endpoint."""
from fastapi import APIRouter, HTTPException
from api.models import TransactionData, PredictionResponse
from api.database import get_db
import joblib
import numpy as np
import pandas as pd
import os

router = APIRouter()

# Load model
MODEL_PATH = os.getenv("MODEL_PATH", "ml/models/xgb_model.pkl")
SCALER_PATH = os.getenv("SCALER_PATH", "ml/models/scaler.pkl")
FEATURES_PATH = os.getenv("FEATURES_PATH", "ml/models/feature_cols.pkl")

model = joblib.load(MODEL_PATH)
scaler = joblib.load(SCALER_PATH)
feature_cols = joblib.load(FEATURES_PATH)


@router.post("/predict", response_model=PredictionResponse)
async def predict_fraud(data: TransactionData):
    """
    Predict fraud probability for a single transaction.
    
    - **data**: Transaction features
    - Returns fraud probability and risk level
    """
    try:
        # Convert to DataFrame
        df = pd.DataFrame([data.dict()])
        
        # Align features
        for col in feature_cols:
            if col not in df.columns:
                df[col] = 0
        
        X = df[feature_cols]
        
        # Predict
        proba = model.predict_proba(X)[:, 1][0]
        prediction = 1 if proba >= 0.5 else 0
        
        # Risk level
        if proba < 0.3:
            risk = "low"
        elif proba < 0.7:
            risk = "medium"
        else:
            risk = "high"
        
        return PredictionResponse(
            transaction_id=data.TransactionID,
            is_fraud=prediction,
            fraud_probability=round(float(proba), 4),
            risk_level=risk,
            message="Prediction complete" if prediction == 0 else "HIGH RISK: Potential fraud detected"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### 4.5 routes/transactions.py

File: `api/routes/transactions.py`

```python
"""Transaction lookup endpoint."""
from fastapi import APIRouter, HTTPException
from api.models import TransactionResponse
from api.database import get_db
import pandas as pd

router = APIRouter()

@router.get("/transactions/{transaction_id}")
async def get_transaction(transaction_id: int):
    """
    Look up a transaction from the data warehouse.
    
    - **transaction_id**: The TransactionID to look up
    """
    with get_db() as conn:
        result = conn.execute(
            """
            SELECT 
                transaction_id, is_fraud, transaction_amt, 
                product_cd, transaction_dt
            FROM marts.fact_transactions
            WHERE transaction_id = %(tid)s
            """,
            {"tid": transaction_id}
        ).fetchone()
        
        if result is None:
            raise HTTPException(status_code=404, detail="Transaction not found")
        
        return TransactionResponse(
            transaction_id=result[0],
            is_fraud=result[1],
            transaction_amt=float(result[2]),
            product_cd=result[3],
            transaction_dt=result[4],
        )

@router.get("/transactions/predictions/top")
async def get_top_fraud_predictions(limit: int = 10):
    """Get top fraud predictions by probability."""
    with get_db() as conn:
        result = conn.execute(
            """
            SELECT 
                transaction_id,
                is_fraud_actual,
                is_fraud_predicted,
                ROUND(fraud_probability, 4) as fraud_probability,
                transaction_amt
            FROM marts.predictions
            ORDER BY fraud_probability DESC
            LIMIT %(limit)s
            """,
            {"limit": limit}
        ).fetchall()
        
        return [
            {
                "transaction_id": r[0],
                "is_fraud_actual": r[1],
                "is_fraud_predicted": r[2],
                "fraud_probability": float(r[3]),
                "transaction_amt": float(r[4]),
            }
            for r in result
        ]
```

### 4.6 routes/health.py

File: `api/routes/health.py`

```python
"""Health check endpoint."""
from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "ok",
        "service": "fraud-detection-api",
        "timestamp": "2026-09-02"
    }
```

### 4.7 main.py

File: `api/main.py`

```python
"""FastAPI application — Fraud Detection API."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes.predict import router as predict_router
from api.routes.transactions import router as transactions_router
from api.routes.health import router as health_router

app = FastAPI(
    title="Fraud Detection API",
    description="E-commerce fraud detection API powered by XGBoost",
    version="1.0.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(health_router)
app.include_router(predict_router)
app.include_router(transactions_router)

@app.on_event("startup")
async def startup_event():
    """Initialize on startup."""
    print("Fraud Detection API starting up...")
```

---

## 5. CHẠY

### 5.1 Local development

```bash
cd api
.venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Truy cập:
- API docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Health: http://localhost:8000/health

### 5.2 Qua Docker

File: `api/Dockerfile`

```dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Thêm vào docker-compose.yml:

```yaml
  api:
    build: ./api
    ports:
      - "8000:8000"
    depends_on:
      - postgres
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@postgres:5432/ecommerce_fraud_dw
      - MODEL_PATH=/app/ml/models/xgb_model.pkl
    volumes:
      - ./ml/models:/app/ml/models
```

---

## 6. API TEST

### Health check
```bash
curl http://localhost:8000/health
```

### Gửi transaction để dự đoán
```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "TransactionID": 3561737,
    "TransactionDT": 86400,
    "TransactionAmt": 49.5,
    "ProductCD": "W",
    "card1": 567, "card2": 100.0, "card3": 200.0,
    "card4": "Visa", "card5": 134.0, "card6": "credit"
  }'
```

### Expected response:
```json
{
    "transaction_id": 3561737,
    "is_fraud": 0,
    "fraud_probability": 0.12,
    "risk_level": "low",
    "message": "Prediction complete"
}
```

### Transaction lookup:
```bash
curl http://localhost:8000/transactions/3561737
curl http://localhost:8000/transactions/predictions/top?limit=5
```

---

## 7. SUCCESS CRITERIA

```text
[✅] FastAPI app running (http://localhost:8000)
[✅] Swagger docs accessible (/docs)
[✅] Health check returns OK
[✅] POST /predict works (returns fraud_probability)
[✅] GET /transactions/{id} works
[✅] GET /transactions/predictions/top works
[✅] CORS configured
[✅] Dockerfile created
```

---

## 8. Liên hệ

- Trước: [PHASE 20 — Metabase](../20_dashboard/metabase_dashboard.md)
- Sau: [PHASE 22 — AI Assistant](../22_ai_assistant/ai_assistant.md)

*Cập nhật: 02/09/2026 | Version: 1.0*
