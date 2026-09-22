# TRACEABILITY MATRIX

**Dự án:** Ecommerce Fraud Detection Data Warehouse  
**Ngày tạo:** 02/09/2026

> Bảng này đảm bảo mọi yêu cầu đề cương đều được implement, test và báo cáo.  
> Cập nhật sau mỗi phase.

---

## FUNCTIONAL REQUIREMENTS

| FR-ID | Đề cương yêu cầu | Phase | Code/File | Test | Evidence | Chương BC | Status |
|-------|-----------------|-------|-----------|------|----------|-----------|--------|
| FR-01 | Nạp dữ liệu giao dịch (Python Ingestion) | P09, P10 | `ingestion/load_raw.py` | `tests/test_ingestion.py` | Row count log | Ch.4.2 | NOT_STARTED |
| FR-02 | Làm sạch và kiểm tra dữ liệu | P11, P14 | `dbt/models/staging/` | `dbt test` | dbt test results | Ch.4.4 | NOT_STARTED |
| FR-03 | Tự động hóa pipeline (Airflow) | P13 | `airflow/dags/fraud_pipeline.py` | DAG run test | Airflow UI screenshot | Ch.4.3 | NOT_STARTED |
| FR-04 | Lưu trữ dữ liệu trong DW (Star Schema) | P08, P12 | `dbt/models/marts/` | `dbt test` | Table count, schema | Ch.3.3, Ch.4.5 | NOT_STARTED |
| FR-05 | Chạy mô hình Fraud Detection | P16, P17 | `ml/train.py` | `tests/test_ml.py` | Metrics table | Ch.4.6 | NOT_STARTED |
| FR-06 | Lưu kết quả dự đoán vào DW | P19 | `ml/predict.py` | Row count in DW | SQL query result | Ch.4.7 | NOT_STARTED |
| FR-07 | Hiển thị dashboard | P20 | Metabase config | Visual check | Screenshot | Ch.4.8 | NOT_STARTED |
| FR-08 | Truy vấn bằng ngôn ngữ tự nhiên | P22 | `ai_assistant/` | 5 test questions | Query log | Ch.4.9 | NOT_STARTED |
| FR-09 | Trả về kết quả phân tích (NL answer) | P22 | `ai_assistant/nlp_response.py` | Response quality | Sample outputs | Ch.4.9 | NOT_STARTED |
| FR-10 | SHAP explanation | P18 | `ml/shap_explain.py` | Visual check | SHAP plots | Ch.4.7 | NOT_STARTED |
| FR-11 | FastAPI endpoints | P21 | `api/main.py` | `tests/test_api.py` | API test results | Ch.4.9 | NOT_STARTED |

---

## NON-FUNCTIONAL REQUIREMENTS

| NFR-ID | Đề cương yêu cầu | Phase | Implementation | Test | Status |
|--------|-----------------|-------|---------------|------|--------|
| NFR-01 | Tái chạy pipeline (Reproducibility) | P13, P23 | Idempotent tasks, Docker | Full pipeline rerun | NOT_STARTED |
| NFR-02 | Logging | P09-P14 | Python logging module | Log files exist | NOT_STARTED |
| NFR-03 | Data validation | P14 | dbt tests, Great Expectations | Test results | NOT_STARTED |
| NFR-04 | Khả năng mở rộng | P07 | Modular code, config-driven | Code review | NOT_STARTED |
| NFR-05 | Bảo mật cơ bản (.env, no commit secret) | P28 | .gitignore, .env.example | Git log check | NOT_STARTED |
| NFR-06 | AI chỉ SELECT (read-only) | P22 | SQL validator, ro user | SQL injection test | NOT_STARTED |
| NFR-07 | Docker deployment | P23 | docker-compose.yml | `docker compose up` | NOT_STARTED |
| NFR-08 | Retry khi task thất bại | P13 | Airflow retries config | Cố tình fail task | NOT_STARTED |

---

## TECHNOLOGY MAPPING

| Công nghệ | Đề cương yêu cầu | Dùng ở đâu | Status |
|-----------|-----------------|------------|--------|
| Python | ✅ Ngôn ngữ chính | Ingestion, ML, API | NOT_STARTED |
| PostgreSQL | ✅ Database | RAW, STG, DW | NOT_STARTED |
| Apache Airflow | ✅ Orchestration | Pipeline DAG | NOT_STARTED |
| dbt Core | ✅ Transformation | STG → DW | NOT_STARTED |
| Logistic Regression | ✅ ML model | Baseline | NOT_STARTED |
| Random Forest | ✅ ML model | Ensemble | NOT_STARTED |
| XGBoost | ✅ ML model | Boosting | NOT_STARTED |
| SHAP | ✅ XAI | Explanation | NOT_STARTED |
| FastAPI | ✅ API | REST endpoints | NOT_STARTED |
| Metabase | ✅ BI | Dashboard | NOT_STARTED |
| LLM | ✅ AI Assistant | Text-to-SQL | NOT_STARTED |
| Docker Compose | ✅ Deployment | All services | NOT_STARTED |
| Git | ✅ Source control | All code | IN_PROGRESS |

---

## CHAPTER MAPPING

| Phase | Thành phần | Chương báo cáo |
|-------|-----------|---------------|
| P00-P02 | Governance, Problem Analysis | Chương 1 (1.1, 1.2, 1.3, 1.4) |
| P03 | Environment Setup | Chương 2 (2.2) + Chương 4 (4.1) |
| P04-P05 | Dataset, EDA | Chương 2 + Chương 3 (3.1.2) |
| P06-P07 | Requirements, Architecture | Chương 3 (3.1.3, 3.2, 3.3) |
| P08 | Data Modeling | Chương 3 (3.3.2) |
| P09-P10 | Ingestion, RAW | Chương 4 (4.2) |
| P11-P12 | Staging, dbt | Chương 4 (4.3) |
| P13 | Airflow | Chương 4 (4.3) |
| P14 | Data Quality | Chương 4 (4.4) |
| P15-P17 | ML: Prep, Train, Evaluate | Chương 4 (4.6) |
| P18-P19 | SHAP, Integration | Chương 4 (4.7) |
| P20 | Dashboard | Chương 4 (4.8) |
| P21-P22 | API, AI Assistant | Chương 4 (4.9) |
| P23-P25 | Docker, E2E, Testing | Chương 4 (4.10) |
| P26-P29 | Failure, Perf, Security, Docs | Kết luận |

---

## STATUS LEGEND

```
NOT_STARTED  — Chưa bắt đầu
IN_PROGRESS  — Đang làm
PARTIAL      — Làm được một phần
PASSED ✅    — Đạt DoD hoàn toàn
FAILED ❌    — Thất bại, cần debug
BLOCKED      — Bị block
```

---

*Cập nhật: 02/09/2026 | Version: 1.0*
