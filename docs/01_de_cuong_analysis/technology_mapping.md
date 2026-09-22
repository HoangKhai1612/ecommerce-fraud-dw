# TECHNOLOGY MAPPING

**Ngày tạo:** 02/09/2026

---

## 1. STACK OVERVIEW

```
┌─────────────────────────────────────────────────────────┐
│                    DATA SOURCES                         │
│         IEEE-CIS Fraud Detection (CSV files)           │
└─────────────────────┬───────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────┐
│              INGESTION LAYER                            │
│                  Python 3.10+                          │
│             (pandas, psycopg2, sqlalchemy)             │
└─────────────────────┬───────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────┐
│              STORAGE LAYER                              │
│              PostgreSQL 15+                            │
│        raw | staging | marts schemas                   │
└─────────────────────┬───────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────┐
│           TRANSFORMATION LAYER                          │
│               dbt Core 1.7+                           │
│        (staging models → mart models)                  │
└─────────────────────┬───────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────┐
│          ORCHESTRATION LAYER                            │
│            Apache Airflow 2.8+                        │
│         (DAG → Task → Scheduling)                     │
└──────────────┬──────────────────────────────────────────┘
               │
    ┌──────────┼─────────────────┐
    │          │                 │
    ▼          ▼                 ▼
┌───────┐  ┌──────────┐  ┌─────────────┐
│  ML   │  │Dashboard │  │ AI/API      │
│Python │  │Metabase  │  │FastAPI      │
│sklearn│  │0.49+     │  │LLM/Ollama   │
│XGBoost│  │          │  │Text-to-SQL  │
│SHAP   │  │          │  │             │
└───────┘  └──────────┘  └─────────────┘
               │
┌──────────────▼──────────────────────────────────────────┐
│            DEPLOYMENT                                   │
│          Docker Compose                                │
└─────────────────────────────────────────────────────────┘
```

---

## 2. TECHNOLOGY TABLE

| Layer | Technology | Version | Vai trò | Tại sao chọn |
|-------|-----------|---------|---------|-------------|
| Language | Python | 3.10+ | Ingestion, ML, API | Universal trong Data Engineering |
| Database | PostgreSQL | 15+ | All layers storage | Đề cương quy định, mạnh về analytics |
| Transformation | dbt Core | 1.7+ | STG → DW | SQL-first, có tests, có docs |
| Orchestration | Apache Airflow | 2.8+ | Pipeline automation | Đề cương quy định, industry standard |
| ML Baseline | scikit-learn LR | 1.3+ | Logistic Regression | Simple, interpretable baseline |
| ML Ensemble | scikit-learn RF | 1.3+ | Random Forest | Good general-purpose |
| ML Boosting | XGBoost | 2.0+ | XGBoost | Best performance thường thấy |
| Explainability | SHAP | 0.44+ | Feature explanation | Đề cương quy định, SHAP values |
| API | FastAPI | 0.110+ | REST endpoints | Đề cương quy định, modern, async |
| BI | Metabase | 0.49+ | Dashboard | Đề cương quy định, open-source |
| LLM | Ollama / OpenAI | latest | Text-to-SQL | Local LLM (Ollama) hoặc API |
| Container | Docker | 25+ | Service packaging | Đề cương quy định |
| Compose | Docker Compose | 2.x | Multi-service | Đề cương quy định |
| Source Control | Git | 2.x+ | Code versioning | Standard |

---

## 3. PYTHON PACKAGES

### Core Data Engineering
```
pandas==2.x          # Data manipulation
numpy==1.x           # Numerical computing
psycopg2-binary==2.x # PostgreSQL driver
sqlalchemy==2.x      # ORM / connection pooling
python-dotenv==1.x   # .env file loading
```

### dbt
```
dbt-core==1.7.x
dbt-postgres==1.7.x
```

### Machine Learning
```
scikit-learn==1.3.x
xgboost==2.0.x
imbalanced-learn==0.11.x  # SMOTE
shap==0.44.x
joblib==1.3.x             # Model serialization
```

### API
```
fastapi==0.110.x
uvicorn==0.27.x
pydantic==2.x
```

### AI Assistant
```
openai==1.x         # hoặc
ollama==0.1.x       # tùy LLM choice
sqlparse==0.4.x     # SQL parsing/validation
```

### Airflow
```
apache-airflow==2.8.x  # cài riêng trong Docker
```

### Testing
```
pytest==7.x
pytest-cov==4.x
httpx==0.26.x  # test FastAPI
```

---

## 4. PORT MAPPING (Docker)

| Service | Port | URL |
|---------|------|-----|
| PostgreSQL | 5432 | postgresql://localhost:5432 |
| Airflow Webserver | 8080 | http://localhost:8080 |
| Metabase | 3000 | http://localhost:3000 |
| FastAPI | 8000 | http://localhost:8000 |
| Ollama | 11434 | http://localhost:11434 |

---

*Cập nhật: 02/09/2026 | Version: 1.0*
