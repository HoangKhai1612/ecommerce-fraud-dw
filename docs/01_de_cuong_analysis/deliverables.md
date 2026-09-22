# DELIVERABLES

**Dự án:** Ecommerce Fraud Detection Data Warehouse  
**Ngày tạo:** 02/09/2026

---

## 1. DELIVERABLES THEO ĐỀ CƯƠNG

| # | Deliverable | Nội dung | Verify bằng | Status |
|---|------------|---------|------------|--------|
| D01 | Python Ingestion | Script nạp CSV → PostgreSQL RAW | Row count match | NOT_STARTED |
| D02 | RAW Layer | PostgreSQL schema raw, tables raw.transactions, raw.identity | `SELECT count(*)` | NOT_STARTED |
| D03 | STAGING Layer | dbt staging models với type cast, rename | `dbt run`, `dbt test` | NOT_STARTED |
| D04 | Data Warehouse (Star Schema) | Fact tables + Dimension tables | Schema diagram + queries | NOT_STARTED |
| D05 | Airflow DAG | Tự động hóa toàn bộ pipeline | DAG run success | NOT_STARTED |
| D06 | dbt Models | staging + intermediate + marts models | `dbt run && dbt test` | NOT_STARTED |
| D07 | Data Quality Report | dbt tests + quality metrics | Test pass rate | NOT_STARTED |
| D08 | ML Models (3) | LR, RF, XGBoost — trained và saved | Model artifacts (.pkl) | NOT_STARTED |
| D09 | Model Comparison Table | Metrics table cho 3 models | Excel/CSV comparison | NOT_STARTED |
| D10 | Best Model | 1 model được chọn với lý do | Model artifact + rationale | NOT_STARTED |
| D11 | SHAP Explanation | Global + local explanation plots | PNG files | NOT_STARTED |
| D12 | Predictions in DW | fact_fraud_prediction table | `SELECT count(*)` | NOT_STARTED |
| D13 | Metabase Dashboard | ≥5 KPI charts kết nối DW | Screenshot | NOT_STARTED |
| D14 | FastAPI | ≥4 endpoints hoạt động | API test results | NOT_STARTED |
| D15 | AI Assistant | Text-to-SQL → DW → NL answer | 5+ test questions | NOT_STARTED |
| D16 | Docker Compose | `docker compose up` → all healthy | `docker ps` output | NOT_STARTED |
| D17 | Documentation (docs/) | Toàn bộ docs/ structure | File listing | IN_PROGRESS |
| D18 | Test Suite | pytest + dbt tests | Test report | NOT_STARTED |
| D19 | Evidence Folder | Screenshots, logs, results | evidence/ listing | NOT_STARTED |
| D20 | Báo cáo (4 chương) | Word document hoàn chỉnh | Review | NOT_STARTED |
| D21 | README | Hướng dẫn setup và chạy | Reproduce test | NOT_STARTED |
| D22 | Demo Script | Kịch bản demo 15-20 phút | Practice run | NOT_STARTED |

---

## 2. DELIVERABLES THEO CHAPTER

| Chương | Deliverables cần có |
|--------|-------------------|
| Chương 1 | D17 (docs/02_problem_analysis/) |
| Chương 2 | D17 (docs/07_architecture/) |
| Chương 3 | D04 (star schema design), D17 (docs/08_data_model/) |
| Chương 4 | D01-D16 (tất cả implementation) |
| Kết luận | D09 (comparison), D11 (SHAP), Limitations |

---

## 3. MINIMUM VIABLE DELIVERABLES (Nếu thời gian hạn chế)

Nếu không đủ thời gian, thứ tự ưu tiên:

```
Priority 1 (MUST):
  D01 — Ingestion
  D02 — RAW Layer
  D03 — STAGING Layer
  D04 — Data Warehouse
  D08 — ML Models (ít nhất 1)
  D13 — Dashboard (basic)
  D16 — Docker Compose
  D17 — Documentation
  D20 — Báo cáo

Priority 2 (SHOULD):
  D05 — Airflow DAG
  D06 — dbt Models
  D10 — Best Model
  D11 — SHAP
  D14 — FastAPI

Priority 3 (COULD):
  D15 — AI Assistant
  D12 — Predictions in DW
  D22 — Demo Script
```

---

*Cập nhật: 02/09/2026 | Version: 1.0*
