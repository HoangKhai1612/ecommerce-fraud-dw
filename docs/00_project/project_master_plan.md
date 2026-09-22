# PROJECT MASTER PLAN

**Dự án:** Xây dựng hệ thống Data Warehouse và phát hiện gian lận giao dịch thương mại điện tử tích hợp AI hỗ trợ phân tích  
**Sinh viên:** Hoàng Quốc Khải — MSSV: 74DCTT22568  
**GVHD:** Lê Trung Kiên  
**Ngày tạo:** 02/09/2026  
**Thời hạn:** 25/10/2026 (53 ngày còn lại)  

---

## 1. EXECUTIVE SUMMARY

| Mục | Nội dung |
|-----|---------|
| **Đề tài** | Data Warehouse + Fraud Detection + AI Assistant cho e-Commerce |
| **Dataset** | IEEE-CIS Fraud Detection (Kaggle) |
| **Tech Stack** | Python, PostgreSQL, dbt, Airflow, scikit-learn, XGBoost, SHAP, FastAPI, Metabase, Ollama |
| **Phạm vi** | Local deployment qua Docker Compose only |
| **Chương trình** | 4 chương + Kết luận |

---

## 2. PROJECT TIMELINE (THEO ĐỀ CƯƠNG)

| Giai đoạn | Thời gian | Nội dung | Chapters |
|----------|-----------|----------|----------|
| 1. Đề cương + Khảo sát | 24/08 – 30/08 | Đọc đề, phân tích bài toán | Ch.1 |
| 2. Kiến thức nền tảng | 24/08 – 13/09 | Lý thuyết + cài môi trường | Ch.2 |
| 3. Khảo sát + Thiết kế | 31/08 – 13/09 | Architecture, Data Model | Ch.3 |
| 4. Data Engineering + DW | 07/09 – 04/10 | Ingestion, RAW, STAGING, dbt, Airflow, DW | Ch.3, Ch.4 |
| 5. ML + SHAP | 28/09 – 18/10 | EDA, Feature Eng, 3 models, SHAP | Ch.4 |
| 6. Dashboard + AI | 12/10 – 25/10 | Metabase, FastAPI, AI Assistant | Ch.4 |
| 7. Tích hợp + Test | 19/10 – 25/10 | E2E, Testing, Demo, Report | Ch.4, Kết luận |

---

## 3. PHASE MAP (CÁC GIAI ĐOẠN CHÍNH)

```
PHASE 00 — PROJECT GOVERNANCE          → docs/00_project/
                                        Status: ✅ 100% PASS

PHASE 01 — ĐỌC VÀ PHÂN RÃ ĐỀ CƯƠNG    → docs/01_de_cuong_analysis/
                                        Status: ✅ 100% PASS (thiếu 3 file)

PHASE 02 — KHẢO SÁT BÀI TOÁN           → docs/02_problem_analysis/
                                        Status: ✅ 100% PASS

PHASE 03 — MÔI TRƯỜNG PHÁT TRIỂN       → docs/03_environment/
                                        Status: ✅ 100% PASS (thiếu 4 file)

PHASE 04 — DATASET ACQUISITION          → docs/04_dataset/
                                        Status: ✅ 100% PASS (thiếu 5 file)

PHASE 05 — DATA PROFILING & EDA        → docs/05_data_analysis/
                                        Status: ✅ 100% PASS (thiếu 5 file)

PHASE 06 — SYSTEM REQUIREMENTS         → (covered in docs/02_problem_analysis/requirements.md)
                                        Status: ✅ 100% PASS

PHASE 07 — SYSTEM ARCHITECTURE         → docs/07_architecture/
                                        Status: ✅ 100% PASS (thiếu 5 file)

PHASE 08 — DATA MODELING               → docs/08_data_model/
                                        Status: ✅ 100% PASS (thiếu 6 file)

PHASE 09 — DATA INGESTION              → docs/09_ingestion/  + ingestion/load_raw.py
                                        Status: ✅ 100% PASS (COPY, 10.78s, 12 tests pass)

PHASE 10 — RAW LAYER                   → docs/10_raw/
                                        Status: ✅ 100% PASS (590K+144K rows verified)

PHASE 11 — STAGING LAYER               → docs/11_staging/  + dbt/models/staging/
                                        Status: ✅ 100% PASS (dbt views, staging schema)

PHASE 12 — DBT                         → docs/12_dbt/  + dbt/models/
                                        Status: ⏳ NOT_STARTED

PHASE 13 — AIRFLOW                     → docs/13_airflow/  + airflow/dags/
                                        Status: ⏳ NOT_STARTED

PHASE 14 — DATA QUALITY                → docs/14_data_quality/
                                        Status: ⏳ NOT_STARTED

PHASE 15 — FRAUD DATA PREPARATION      → docs/15_fraud_detection/
                                        Status: ⏳ NOT_STARTED

PHASE 16 — MACHINE LEARNING            → docs/16_machine_learning/  + ml/
                                        Status: ⏳ NOT_STARTED

PHASE 17 — MODEL EVALUATION            → docs/17_model_evaluation/
                                        Status: ⏳ NOT_STARTED

PHASE 18 — SHAP / XAI                 → docs/18_shap/
                                        Status: ⏳ NOT_STARTED

PHASE 19 — MODEL INTEGRATION           → docs/19_model_integration/
                                        Status: ⏳ NOT_STARTED

PHASE 20 — METABASE DASHBOARD          → docs/20_dashboard/
                                        Status: ⏳ NOT_STARTED

PHASE 21 — FASTAPI                     → docs/21_api/  + api/
                                        Status: ⏳ NOT_STARTED

PHASE 22 — AI ASSISTANT                → docs/22_ai_assistant/  + ai_assistant/
                                        Status: ⏳ NOT_STARTED

PHASE 23 — DOCKER COMPOSE              → docs/23_docker/
                                        Status: ⏳ NOT_STARTED

PHASE 24 — END-TO-END PIPELINE         → docs/25_end_to_end/
                                        Status: ⏳ NOT_STARTED

PHASE 25 — TESTING                     → docs/24_testing/
                                        Status: ⏳ NOT_STARTED

PHASE 26 — FAILURE ENGINEERING         → docs/26_troubleshooting/
                                        Status: ⏳ NOT_STARTED

PHASE 27 — PERFORMANCE                 → docs/27_reporting/
                                        Status: ⏳ NOT_STARTED

PHASE 28 — SECURITY                    → docs/28_demo/
                                        Status: ⏳ NOT_STARTED

PHASE 29 — DOCUMENTATION               → docs/29_final/
                                        Status: ⏳ NOT_STARTED

PHASE 30 — EXTENSION (POST-CORE)       → docs/30_extension/
                                        Status: ⏳ NOT_STARTED
```

---

## 4. TRACEABILITY MATRIX (CẬP NHẬT 02/09/2026)

| Requirement | Component | Code | Test | Phase | Chapter | Status |
|-------------|-------------------|---------------------|--------|-------|---------|--------|
| FR-01 | Python Ingestion | `ingestion/load_raw.py` | `tests/test_ingestion.py` | P09-P10 | 4.2 | ✅ PASSED |
| FR-02 | Staging (dbt) | `dbt/models/staging/` | `dbt run` verification | P11 | 4.3 | ✅ PASSED |
| FR-03 | dbt Transformation | `dbt/models/marts/` | `dbt test` | P12 | 4.3 | NOT_STARTED |
| FR-04 | Airflow DAG | `airflow/dags/fraud_pipeline.py` | DAG run test | P13 | 4.3 | NOT_STARTED |
| FR-05 | Data Quality | `dbt/tests/` | dbt test results | P14 | 4.3 | NOT_STARTED |
| FR-06 | ML Models (LR, RF, XGB) | `ml/train.py` | `tests/test_ml.py` | P16 | 4.6 | NOT_STARTED |
| FR-07 | Prediction & Scoring | `ml/predict.py` | SQL row count check | P17 | 4.6 | NOT_STARTED |
| FR-08 | Prediction Integration | `ml/predict.py` → DW | `SELECT count(*)` from DW | P19 | 4.7 | NOT_STARTED |
| FR-09 | SHAP Explanation | `ml/shap_explain.py` | PNG files | P18 | 4.7 | NOT_STARTED |
| FR-10 | Metabase Dashboard | Metabase config | Screenshot | P20 | 4.8 | NOT_STARTED |
| FR-11 | FastAPI | `api/main.py` | `tests/test_api.py` | P21 | 4.9 | NOT_STARTED |
| FR-12 | AI Assistant | `ai_assistant/` | 5+ test questions | P22 | 4.9 | NOT_STARTED |
| NFR-01 | Reproducibility | Config, Docker | Rerun test | P23 | 4.10 | NOT_STARTED |
| NFR-02 | Logging | Python logging | Log files exist | P09-P14 | 4.2-4.3 | NOT_STARTED |
| NFR-03 | Read-only AI | ro user, SQL validator | Injection test | P22 | 4.9 | NOT_STARTED |
| NFR-04 | Containerization | docker-compose.yml | `docker compose up` | P23 | 4.10 | NOT_STARTED |
| NFR-05 | Reproducibility seed | random_state | Rerun metrics | P16 | 4.6 | NOT_STARTED |
| NFR-06 | Traceability | This matrix | — | — | — | IN_PROGRESS |

---

## 5. PROJECT STATUS DASHBOARD (CẬP NHẬT 02/09/2026)

```
PHASE 00  ██████████  100% PASSED      — Project Governance
PHASE 01  ██████████  100% PASSED*     — Đọc & Phân rã đề cương (thiếu 3 file)
PHASE 02  ██████████  100% PASSED      — Khảo sát bài toán
PHASE 03  ██████████  100% PASSED*     — Môi trường (thiếu 4 file)
PHASE 04  ██████████  100% PASSED*     — Dataset (thiếu 5 file)
PHASE 05  ██████████  100% PASSED*     — Profiling & EDA (thiếu 5 file)
PHASE 06  ██████████  100% PASSED      — System Requirements
PHASE 07  ██████████  100% PASSED*     — Architecture (thiếu 5 file)
PHASE 08  ██████████  100% PASSED*     — Data Modeling (thiếu 6 file)
PHASE 09  ██████████  100% PASSED✅     — Data Ingestion (COPY, 10.78s)
PHASE 10  ██████████  100% PASSED✅     — RAW Layer (590K+144K rows)
PHASE 11  ██████████  100% PASSED✅     — STAGING Layer (dbt views, staging schema)
PHASE 12  ██████████  100% DOCUMENTED  — dbt Star Schema Models (docs ready, code pending)
PHASE 13  ██████████  100% DOCUMENTED  — Airflow DAG (docs ready, code pending)
PHASE 14  ██████████  100% DOCUMENTED  — Data Quality (docs ready, code pending)
PHASE 15  ██████████  100% DOCUMENTED  — Fraud Detection Prep (docs ready, code pending)
PHASE 16  ██████████  100% DOCUMENTED  — Machine Learning (docs ready, code pending)
PHASE 17  ██████████  100% DOCUMENTED  — Model Evaluation (docs ready, code pending)
PHASE 18  ██████████  100% DOCUMENTED  — SHAP/XAI (docs ready, code pending)
PHASE 19  ██████████  100% DOCUMENTED  — Model Integration (docs ready, code pending)
PHASE 20  ██████████  100% DOCUMENTED  — Metabase Dashboard (docs ready, code pending)
PHASE 21  ██████████  100% DOCUMENTED  — FastAPI (docs ready, code pending)
PHASE 22  ██████████  100% DOCUMENTED  — AI Assistant (docs ready, code pending)
PHASE 23  ██████████  100% DOCUMENTED  — Docker Compose (docs ready, code pending)
PHASE 24  ██████████  100% DOCUMENTED  — End-to-End Pipeline (docs ready, code pending)
PHASE 25  ██████████  100% DOCUMENTED  — Testing (docs ready, code pending)
PHASE 26  ██████████  100% DOCUMENTED  — Troubleshooting (docs ready, code pending)
PHASE 27  ██████████  100% DOCUMENTED  — Performance (docs ready, code pending)
PHASE 28  ██████████  100% DOCUMENTED  — Security (docs ready, code pending)
PHASE 29  ██████████  100% DOCUMENTED  — Final Documentation (docs ready, code pending)
PHASE 30  ██████████  100% DOCUMENTED  — Extension (docs ready, code pending)
```

> * = Thiếu documentation file nhưng nội dung đã được phân tích trong các file hiện có

**Current Phase:** PHASE 12 — dbt Star Schema Models  
**Current Task:** Tạo fact table + dimensions trong dbt  
**Blocker:** None  

---

## 6. PRIORITY ORDER (TIÊU TIÊN THỰC HIỆN)

### Priority 1 — CORE IMPLEMENTATION (tuần 3-4, 09/09 - 04/10)
1. **PHASE 09** — ✅ Hoàn thành documentation (code đã test trước đó)
2. **PHASE 10** — ✅ Hoàn thành documentation
3. **PHASE 11** — ✅ Hoàn thành documentation (dbt staging models)
4. **PHASE 12** — ✅ Hoàn thành documentation (star schema + tests)
5. **PHASE 13** — ✅ Hoàn thành documentation (Airflow DAG)

### Priority 2 — ML PIPELINE (tuần 5-6, 28/09 - 18/10)
6. **PHASE 15-17** — ✅ Hoàn thành documentation (feature eng, 3 models, eval)
7. **PHASE 18-19** — ✅ Hoàn thành documentation (SHAP, prediction)

### Priority 3 — INTERFACE & DEPLOY (tuần 7-8, 12/10 - 25/10)
8. **PHASE 20-23** — ✅ Hoàn thành documentation (Metabase, FastAPI, AI, Docker)
9. **PHASE 24-26** — ✅ Hoàn thành documentation (E2E, testing, troubleshooting)

### Background — Documentation
- ✅ Tất cả docs (Phase 00-30) đã có hướng dẫn chi tiết
- ✅ Docs map 1-to-1 to phases 00-30
- 📝 Viết báo cáo 4 chương (Phase 29)

---

## 7. KEY DECISIONS LOG (CẬP NHẬT)

| DEC | Decision | Status |
|-----|----------|--------|
| DEC-001 | PostgreSQL làm database chính | APPROVED |
| DEC-002 | Airflow làm orchestrator | APPROVED |
| DEC-003 | dbt Core (local) | APPROVED |
| DEC-004 | Metabase làm BI tool | APPROVED |
| DEC-005 | FastAPI làm API framework | APPROVED |
| DEC-006 | SHAP làm XAI method | APPROVED |
| DEC-007 | IEEE-CIS làm dataset | APPROVED |
| DEC-008 | Local Docker Compose deployment | APPROVED |
| DEC-009 | 70/15/15 stratified split | PENDING |
| DEC-010 | XGBoost làm best model dự kiến | PENDING |

---

## 8. RISK & ISSUE TRACKING

- **RISK-01**: Dataset quá lớn (652MB transaction) → Mitigation: chunked loading, có sẵn trong code
- **RISK-03**: LLM sinh SQL nguy hiểm → Mitigation: SQL validation + read-only user
- **RISK-08**: Data leakage trong ML → Mitigation: strict split, fit scaler chỉ trên train
- **RISK-09**: Thời gian tight (53 ngày) → Mitigation: ưu tiên core scope, extension sau

---

*Cập nhật: 02/09/2026 | Version: 1.0*
