# DATA FLOW PIPELINE

**Dự án:** Ecommerce Fraud Detection Data Warehouse  
**Phase:** 07 — System Architecture  
**Ngày tạo:** 02/09/2026  

---

## 1. FULL DATA FLOW (END-TO-END)

```text
                    ┌──────────────────────────────────────┐
                    │        DATA SOURCE                   │
                    │  train_transaction.csv (590,540 rows) │
                    │  train_identity.csv (144,233 rows)    │
                    └───────────────────┬──────────────────┘
                                        │
                    ┌───────────────────▼──────────────────┐
                    │        PHASE 09: INGESTION           │
                    │        Python: ingestion/load_raw.py │
                    │       ┌─────────────────────────┐   │
                    │       │ 1. Load CSV (chunked)   │   │
                    │       │ 2. Create schema 'raw'  │   │
                    │       │ 3. to_sql → raw.*       │   │
                    │       └─────────────────────────┘   │
                    └───────────────────┬──────────────────┘
                                        │
                    ┌───────────────────▼──────────────────┐
                    │       PHASE 10: RAW LAYER            │
                    │       Schema: raw                  │
                    │       ├─ raw.transactions (590,540) │
                    │       └─ raw.identity (144,233)    │
                    └───────────────────┬──────────────────┘
                                        │
                    ┌───────────────────▼──────────────────┐
                    │    PHASE 11: STAGING (dbt)           │
                    │   Schema: staging                  │
                    │   ├─ staging.stg_transactions        │
                    │   └─ staging.stg_identity           │
                    │   Rename, cast, clean              │
                    └───────────────────┬──────────────────┘
                                        │
                    ┌───────────────────▼──────────────────┐
                    │   PHASE 12: DBT TRANSFORMATION      │
                    │   Schema: marts                    │
                    │   ├─ marts.fact_transaction         │
                    │   ├─ marts.fact_fraud_prediction    │
                    │   ├─ marts.dim_date                 │
                    │   ├─ marts.dim_product             │
                    │   ├─ marts.dim_card                │
                    │   ├─ marts.dim_device              │
                    │   └─ marts.dim_email               │
                    │   Star Schema, Surrogate Keys      │
                    └───────────────────┬──────────────────┘
                                        │
                    ┌───────────────────▼──────────────────┐
                    │    PHASE 15: ML PIPELINE             │
                    │   ├─ Feature Engineering            │
                    │   ├─ Train/Val/Test Split (70/15/15) │
                    │   ├─ SMOTE / class_weight          │
                    │   ├─ Train: LR, RF, XGBoost        │
                    │   └─ Evaluate: P/R/F1/ROC-AUC/PR-AUC │
                    └───────────────────┬──────────────────┘
                                        │
                    ┌───────────────────▼──────────────────┐
                    │    PHASE 18: SHAP EXPLAINABLE AI   │
                    │   ├─ Global explanation            │
                    │   ├─ Local explanation             │
                    │   └─ Feature importance            │
                    └───────────────────┬──────────────────┘
                                        │
                    ┌───────────────────▼──────────────────┐
                    │  PHASE 19: MODEL INTEGRATION          │
                    │   ├─ Load best model                │
                    │   ├─ Predict on all transactions    │
                    │   ├─ Save results to:               │
                    │   │   marts.fact_fraud_prediction    │
                    │   └─ risk_score, probability, label  │
                    └───────────────────┬──────────────────┘
                                        │
                    ┌─────────┬─────────┬─────────┬─────────┐
                    │         │         │         │         │
    ┌───────────────▼──┐  ┌───▼────────────┐  ┌───▼────────────┐  ┌───▼────────────┐
    │ Metabase Dash    │  │ FastAPI        │  │ AI Assistant   │  │ Data Quality   │
    │   Dashboard KPIs │  │   /api/*       │  │   NL→SQL→NL    │  │   dbt tests    │
    │                  │  │                │  │                │  │                │
    │ Reads: marts.*   │  │ Reads: marts.* │  │ Reads: marts.* │  │ Tests: all     │
    └──────────────────┘  └────────────────┘  └────────────────┘  └────────────────┘
                    │         │         │         │         │
                    ▼         ▼         ▼         ▼         ▼
              ┌──────────────────────────────────────────────┐
              │           AIRFLOW ORCHESTRATION              │
              │  fraud_pipeline DAG:                         │
              │  check_source → ingest → validate →          │
              │  staging → dbt_run → dbt_test →              │
              │  ml_train → ml_predict → quality_check       │
              └──────────────────────────────────────────────┘
```

---

## 2. PIPELINE FLOW CHI TIẾT

### Flow 1: Data Ingestion → RAW
```
CSV files (train_*)
    ↓
Python: pd.read_csv(chunksize=50000)
    ↓
SQLAlchemy engine → PostgreSQL
    ↓
schema: raw
    ├─ table: raw.transactions (590,540 rows, 394 cols)
    └─ table: raw.identity (144,233 rows, 41 cols)
```

### Flow 2: RAW → STAGING → MARTS (dbt)
```
raw.transactions
    ↓ (dbt source)
staging.stg_transactions (rename, cast, clean)
    ↓ (dbt model)
marts.fact_transaction (FK → dim_date, dim_product, dim_card, dim_device, dim_email)
    ↓ (dbt model)
marts.dim_date, dim_product, dim_card, dim_device, dim_email
```

### Flow 3: ML Pipeline
```
marts.fact_transaction + dim_* (JOIN all)
    ↓
Feature Engineering (prepare_data.py)
    ↓
Train/Val/Test Split (stratified, random_state=42)
    ↓
SMOTE (train only) / class_weight
    ↓
LR, RF, XGBoost
    ↓
Evaluation: Precision, Recall, F1, ROC-AUC, PR-AUC
    ↓
Select Best Model → save .pkl
```

### Flow 4: SHAP Explanation
```
Best Model + sample data (1000-5000 rows)
    ↓
SHAP TreeExplainer
    ↓
Global: summary_plot, bar_plot
Local: force_plot, waterfall_plot
    ↓
Save PNG files
```

### Flow 5: Prediction Integration
```
Best Model → predict on full dataset
    ↓
fraud_probability, predicted_label, risk_score, risk_level
    ↓
Save to: marts.fact_fraud_prediction
    ↓
transaction_id, prediction_key, predicted_at, model_version
```

### Flow 6: AI Assistant
```
User question (Vietnamese/English)
    ↓
LLM (Ollama/llama3) → generate SQL
    ↓
SQL Validation (chỉ SELECT, block DROP/DELETE/UPDATE/INSERT)
    ↓
Execute on PostgreSQL (read-only user)
    → Query Result
    ↓
LLM → Natural Language Answer
    ↓
Response to User
```

---

## 3. AIRFLOW DAG DEPENDENCY FLOW

```text
check_source ──→ ingest_raw ──→ validate_raw
                                      │
                                      ▼
                              dbt_run (staging → marts)
                                      │
                                      ▼
                              dbt_test (quality checks)
                                      │
                                      ▼
                            ml_train (LR, RF, XGBoost)
                                      │
                                      ▼
                              ml_predict (save to DW)
                                      │
                                      ▼
                              quality_check (final)
```

- **Retry**: 3 retries, 5-minute delay
- **Schedule**: @daily (manual trigger trong dev)
- **Logging**: stdout + file logging
- **Timeout**: 30 minutes per task

---

## 4. DATA FLOW TABLE

| Step | Source | Process | Target | Phase |
|------|--------|---------|--------|-------|
| 1 | CSV | Python ingestion | raw.* | P09 |
| 2 | raw.* | dbt staging | staging.* | P11 |
| 3 | staging.* | dbt models | marts.fact_*, dim_* | P12 |
| 4 | marts.* | ML feature eng + train | model artifacts | P15-16 |
| 5 | Best model | Predict + SHAP | prediction results | P18-19 |
| 6 | marts.* | Metabase queries | Dashboard | P20 |
| 7 | marts.* | FastAPI queries | API responses | P21 |
| 8 | marts.* | AI Assistant | NL answers | P22 |

*Cập nhật: 02/09/2026 | Version: 1.0*
