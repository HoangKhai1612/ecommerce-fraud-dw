# IMPLEMENTATION MAPPING

**Dự án:** Ecommerce Fraud Detection Data Warehouse  
**Phase:** 01 — Đề cương Analysis  
**Ngày tạo:** 02/09/2026  

> File này ánh xạ từng yêu cầu đề cương sang kế hoạch implementation cụ thể, bao gồm file code, thư mục, và test case tương ứng.

---

## 1. IMPLEMENTATION ROADMAP

### PHASE 09 — Data Ingestion
**Yêu cầu:** FR-01 (Nạp dữ liệu CSV → PostgreSQL RAW)  
**Files:**
- `ingestion/load_raw.py` — Script chính (đã tồn tại, cần review & fix)
- `ingestion/__init__.py`
- `tests/test_ingestion.py` — Unit test
- `docs/09_ingestion/` — Documentation

**Sub-tasks:**
1. Review and fix `load_raw.py` (error handling, validation, logging)
2. Create unit tests
3. Run script với PostgreSQL local (qua Docker)
4. Verify row count, schema

### PHASE 10 — RAW Layer
**Yêu cầu:** RAW phản ánh dữ liệu nguồn gần nhất  
**Files:**
- `docs/10_raw/raw_layer.md`
- SQL verification scripts

### PHASE 11 — Staging Layer
**Yêu cầu:** FR-02 (Rename, cast, standardize)  
**Files:**
- `dbt/models/staging/stg_transactions.sql`
- `dbt/models/staging/stg_identity.sql`
- `docs/11_staging/staging_layer.md`

### PHASE 12 — dbt Models
**Yêu cầu:** FR-03, FR-05 (Transformation + Quality)  
**Files:**
- `dbt/models/staging/` — Staging models
- `dbt/models/marts/` — Fact + Dimension tables
- `dbt/models/schema.yml` — Tests (not_null, unique, relationships)
- `dbt/profiles.yml` — Database connection
- `docs/12_dbt/dbt_setup.md`

### PHASE 13 — Airflow
**Yêu cầu:** FR-04 (Pipeline orchestration)  
**Files:**
- `airflow/dags/fraud_pipeline.py`
- `airflow/Dockerfile`
- `docs/13_airflow/airflow_setup.md`

### PHASE 15 — Fraud Data Preparation
**Yêu cầu:** Feature engineering, imbalance handling  
**Files:**
- `ml/prepare_data.py` — EDA, feature engineering, train/val/test split
- `docs/15_fraud_detection/data_preparation.md`

### PHASE 16 — Machine Learning
**Yêu cầu:** FR-06 (Train 3 models)  
**Files:**
- `ml/train.py` — Train LR, RF, XGBoost
- `ml/evaluate.py` — Compare metrics
- `tests/test_ml.py`
- `docs/16_machine_learning/model_training.md`

### PHASE 17 — Model Evaluation
**Yêu cầu:** FR-06 (So sánh models)  
**Files:**
- `ml/comparison.py` — Metrics table
- `docs/17_model_evaluation/evaluation.md`

### PHASE 18 — SHAP
**Yêu cầu:** FR-09 (Explainability)  
**Files:**
- `ml/shap_explain.py`
- `docs/18_shap/shap_analysis.md`

### PHASE 19 — Model Integration
**Yêu cầu:** FR-08 (Lưu prediction vào DW)  
**Files:**
- `ml/predict.py`
- `docs/19_model_integration/prediction_integration.md`

### PHASE 20 — Metabase Dashboard
**Yêu cầu:** FR-10 (Dashboard)  
**Files:**
- `docker/metabase/` — Metabase config
- `docs/20_dashboard/dashboard_design.md`

### PHASE 21 — FastAPI
**Yêu cầu:** FR-11 (API)  
**Files:**
- `api/main.py` — FastAPI app
- `api/models/` — Pydantic models
- `tests/test_api.py`
- `docs/21_api/api_design.md`

### PHASE 22 — AI Assistant
**Yêu cầu:** FR-12, NFR-03 (Text-to-SQL)  
**Files:**
- `ai_assistant/nl_to_sql.py`
- `ai_assistant/sql_validator.py`
- `ai_assistant/nlp_response.py`
- `tests/test_ai_assistant.py`
- `docs/22_ai_assistant/ai_assistant.md`

### PHASE 23 — Docker Compose
**Yêu cầu:** NFR-04, NFR-01 (Containerization)  
**Files:**
- `docker-compose.yml` (cập nhật full services)
- `docker/airflow/Dockerfile`
- `docker/api/Dockerfile`
- `docs/23_docker/docker_setup.md`

---

## 2. PROJECT DIRECTORY STRUCTURE

```text
ecommerce-fraud-dw/
├── data/                    # Dataset (not committed)
│   └── raw/                 # CSV files IEEE-CIS
├── ingestion/               # Python ingestion scripts
│   ├── load_raw.py          # ✅ CSV → PostgreSQL RAW
│   └── __init__.py
├── dbt/                     # dbt project
│   ├── models/
│   │   ├── staging/         # stg_transactions.sql, stg_identity.sql
│   │   └── marts/           # fact_*.sql, dim_*.sql
│   ├── snapshots/
│   ├── tests/
│   ├── profiles.yml
│   └── dbt_project.yml
├── airflow/                 # Airflow project
│   ├── dags/
│   │   └── fraud_pipeline.py
│   ├── plugins/
│   └── Dockerfile
├── ml/                      # Machine Learning
│   ├── prepare_data.py      # Feature engineering, split
│   ├── train.py             # Train LR, RF, XGBoost
│   ├── evaluate.py          # Compare metrics
│   ├── shap_explain.py      # SHAP explanation
│   ├── predict.py           # Prediction + integration
│   └── saved_models/        # Model artifacts (.pkl, .joblib)
├── api/                     # FastAPI
│   ├── main.py              # FastAPI app + endpoints
│   ├── models/              # Pydantic models
│   └── __init__.py
├── ai_assistant/            # AI Assistant
│   ├── nl_to_sql.py         # LLM → SQL
│   ├── sql_validator.py     # SQL safety validation
│   ├── nlp_response.py      # SQL result → Natural language
│   └── __init__.py
├── tests/                   # Test suite
│   ├── test_ingestion.py
│   ├── test_ml.py
│   ├── test_api.py
│   └── test_ai_assistant.py
├── docker/                  # Docker configs
│   ├── airflow/
│   ├── api/
│   └── metabase/
├── docs/                    # Documentation (31 phases)
│   ├── 00_project/          # ✅ Complete
│   ├── 01_de_cuong_analysis/ # ✅ + 3 files to create
│   ├── 02_problem_analysis/  # ✅ Complete
│   ├── 03_environment/      # ✅ + 4 files to create
│   ├── 04_dataset/          # ✅ + 5 files to create
│   ├── 05_data_analysis/     # ✅ + 5 files to create
│   ├── 06_requirements/      # Will map from Phase 06
│   ├── 07_architecture/      # ✅ + 5 files to create
│   ├── 08_data_model/        # ✅ + 6 files to create
│   ├── 09_ingestion/         # To create
│   ├── 10_raw/               # To create
│   ├── 11_staging/           # To create
│   ├── 12_dbt/               # To create
│   ├── 13_airflow/           # To create
│   ├── 14_data_quality/      # To create
│   ├── 15_fraud_detection/   # To create
│   ├── 16_machine_learning/  # To create
│   ├── 17_model_evaluation/  # To create
│   ├── 18_shap/              # To create
│   ├── 19_model_integration/ # To create
│   ├── 20_dashboard/         # To create
│   ├── 21_api/               # To create
│   ├── 22_ai_assistant/      # To create
│   ├── 23_docker/            # To create
│   ├── 24_testing/           # To create
│   ├── 25_end_to_end/        # To create
│   ├── 26_troubleshooting/   # To create
│   ├── 27_reporting/         # To create
│   ├── 28_demo/              # To create
│   ├── 29_final/             # To create
│   └── 30_extension/         # To create
├── evidence/                # Evidence folder
│   ├── phase_01/
│   ├── phase_02/
│   └── ...
├── report/                  # Report files (docx)
├── docker-compose.yml       # ✅ (PostgreSQL only, will expand)
├── requirements.txt         # ✅
├── .env.example             # ✅
├── .gitignore               # ✅
├── README.md                # To create
└── AGENTS.md                # Kilo config (to create)
```

---

## 3. EXECUTION COMMANDS

```bash
# PHASE 09: Data Ingestion
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
docker compose up -d postgres
python ingestion/load_raw.py        # Chạy ingestion
python tests/test_ingestion.py      # Test ingestion

# PHASE 12: dbt
cd dbt && dbt run && dbt test && dbt docs generate

# PHASE 16: ML
python ml/train.py
python ml/evaluate.py

# PHASE 23: Docker
docker compose up -d
```

*Cập nhật: 02/09/2026 | Version: 1.0*
