# TECHNOLOGY DECISIONS

**Dự án:** Ecommerce Fraud Detection Data Warehouse  
**Phase:** 07 — System Architecture  
**Ngày tạo:** 02/09/2026  

---

## 1. TECHNOLOGY STACK DECISION TABLE

| Layer | Technology | Option A | Option B | Option C | Decision | Reason |
|-------|-----------|---------|---------|---------|----------|--------|
| Language | Python | ✅ Chosen | Java | Go | **Python** | Đề cương quy định; hệ sinh thái phong phú cho DE/ML/API |
| Database | PostgreSQL | ✅ Chosen | MySQL | SQLite | **PostgreSQL** | Đề cương quy định; mạnh về analytical queries, hỗ trợ dbt tốt |
| Orchestration | Airflow | ✅ Chosen | Prefect | Cron | **Airflow** | Đề cương quy định; industry standard, có UI monitor |
| Transformation | dbt Core | ✅ Chosen | dbt Cloud | Custom SQL scripts | **dbt Core** | Free, local, có tests/docs/lineage tích hợp |
| ML Baseline | Logistic Regression | ✅ Chosen | SVM | KNN | **LR** | Đề cương quy định; simple, interpretable |
| ML Ensemble | Random Forest | ✅ Chosen | Gradient Boosting | Extra Trees | **RF** | Đề cương quy định; robust, good general |
| ML Boosting | XGBoost | ✅ Chosen | LightGBM | CatBoost | **XGBoost** | Đề cương quy định; thường cho performance cao nhất |
| XAI | SHAP | ✅ Chosen | LIME | Feature Importance | **SHAP** | Đề cương quy định; standard, có visualizations |
| API | FastAPI | ✅ Chosen | Flask | Django REST | **FastAPI** | Đề cương quy định; modern, async, auto docs |
| BI | Metabase | ✅ Chosen | Superset | Grafana | **Metabase** | Đề cương quy định; đơn giản, dễ dùng |
| LLM | Ollama | ✅ Chosen | OpenAI API | Local transformers | **Ollama** | Local, không cần API key, phù hợp đồ án |
| Container | Docker | ✅ Chosen | -- | -- | **Docker** | Đề cương quy định |
| Compose | Docker Compose | ✅ Chosen | Kubernetes | -- | **Docker Compose** | Đề cương quy định; đủ cho local deployment |
| Version Control | Git | ✅ Chosen | -- | -- | **Git** | Standard practice |

---

## 2. PYTHON PACKAGE DECISIONS

### Core Data Engineering
| Package | Version | Alternative | Decision | Reason |
|---------|---------|-------------|----------|--------|
| pandas | >=2.0 | dask | **pandas** | Đủ cho 590K rows, ecosystem phong phú |
| numpy | >=1.24 | -- | **numpy** | Dependency của pandas/sklearn |
| psycopg2-binary | >=2.9 | asyncpg | **psycopg2** | Standard, ổn định với SQLAlchemy |
| sqlalchemy | >=2.0 | -- | **sqlalchemy** | Kết nối DB clean, có ORM support |
| python-dotenv | >=1.0 | -- | **python-dotenv** | Quản lý .env đơn giản |

### dbt
| Package | Version | Decision |
|---------|---------|----------|
| dbt-core | >=1.7 | ✅ Core |
| dbt-postgres | >=1.7 | ✅ Postgres adapter |

### Machine Learning
| Package | Version | Alternative | Decision | Reason |
|---------|---------|-------------|----------|--------|
| scikit-learn | >=1.3 | -- | **sklearn** | Đề cương quy định, LR + RF |
| xgboost | >=2.0 | lightgbm | **xgboost** | Đề cương quy định |
| imbalanced-learn | >=0.11 | -- | **imbalanced-learn** | SMOTE support |
| shap | >=0.44 | lime | **shap** | Đề cương quy định |
| joblib | >=1.3 | pickle | **joblib** | Fast serialization |

### API
| Package | Version | Alternative | Decision | Reason |
|---------|---------|-------------|----------|--------|
| fastapi | >=0.110 | flask | **fastapi** | Đề cương quy định |
| uvicorn | >=0.27 | werkzeug | **uvicorn** | ASGI server |
| pydantic | >=2.5 | marshmallow | **pydantic** | Input validation |
| requests | >=2.31 | httpx | **requests** | HTTP client |

### AI Assistant
| Package | Version | Alternative | Decision | Reason |
|---------|---------|-------------|----------|--------|
| openai | >=1.0 | ollama | **conditional** | Dùng nếu có API key |
| ollama | >=0.1 | -- | **ollama** (default) | Local LLM |
| sqlparse | >=0.4 | sqlglot | **sqlparse** | SQL parsing/validation |

### Testing
| Package | Version | Alternative | Decision | Reason |
|---------|---------|-------------|----------|--------|
| pytest | >=7.4 | unittest | **pytest** | Simple, powerful, fixtures |
| pytest-cov | >=4.1 | -- | **pytest-cov** | Coverage reporting |
| httpx | >=0.26 | requests | **httpx** | Test FastAPI |

---

## 3. TECHNOLOGY DECISION LOG

| Decision ID | Technology | Options Considered | Decision | Rationale |
|-------------|-----------|-------------------|----------|-----------|
| DEC-001 | PostgreSQL | MySQL, SQLite | PostgreSQL | Đề cương yêu cầu, hỗ trợ dbt, analytical queries |
| DEC-002 | Airflow | Prefect, Cron | Airflow | Đề cương yêu cầu, industry standard |
| DEC-003 | dbt Core | dbt Cloud | dbt Core | Free, local, có tests/docs |
| DEC-004 | Metabase | Superset, Grafana | Metabase | Dễ dùng, đề cương yêu cầu |
| DEC-005 | FastAPI | Flask | FastAPI | Modern, async, auto docs |
| DEC-006 | SHAP | LIME, Feature Importance | SHAP | Đề cương yêu cầu, chuẩn industry |
| DEC-007 | Ollama | OpenAI API | Ollama | Local LLM, không cần internet |
| DEC-008 | XGBoost | LightGBM | XGBoost | Đề cương yêu cầu |
| DEC-009 | scikit-learn | -- | scikit-learn | LR + RF đề cương yêu cầu |
| DEC-010 | Docker Compose | Kubernetes | Docker Compose | Local deployment đủ, không cần k8s |

---

## 4. RISK MITIGATION CHO TECHNOLOGY

| Technology | Risk | Mitigation |
|-----------|------|-----------|
| PostgreSQL (Docker) | OOM trên máy 8GB RAM | Giảm shared_buffers, tắt service khác |
| Airflow | Nặng, chậm | Chạy qua Docker, tắt khi không dùng |
| XGBoost | Chậm trên 590K rows | Sampling nếu RAM < 8GB |
| SHAP | Rất chậm (~30-60s/trade) | Chỉ chạy trên sample 5000 rows |
| Ollama | Cần RAM ~4GB cho model | Dùng model nhỏ (llama3:8b) hoặc GPT API |
| dbt | Schema mismatch | Validation trước khi chạy |

*Cập nhật: 02/09/2026 | Version: 1.0*
