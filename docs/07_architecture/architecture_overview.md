# SYSTEM ARCHITECTURE OVERVIEW

**Dự án:** Ecommerce Fraud Detection Data Warehouse  
**Phase:** 07 — System Architecture  
**Ngày tạo:** 02/09/2026

---

## 1. KẾT CẤU KIẾN TRÚC TỔNG THỂ (HIGH-LEVEL ARCHITECTURE)

Hệ thống được thiết kế theo mô hình xử lý theo lô (Batch Processing Pipeline) gồm 5 tầng chính:

```text
  [ LAYER 1: DATA SOURCE ]
         │
         ├── train_transaction.csv (IEEE-CIS)
         └── train_identity.csv    (IEEE-CIS)
         │
         ▼
  [ LAYER 2: INGESTION & STORAGE ]
         │
         ├── Python Ingestion Script (ingestion/load_raw.py)
         └── PostgreSQL Database:
                ├── Schema: raw      (raw.transactions, raw.identity)
                ├── Schema: staging  (stg_transactions, stg_identity)
                └── Schema: marts    (fact_*, dim_*)
         │
         ▼
  [ LAYER 3: ORCHESTRATION & TRANSFORMATION ]
         │
         ├── Apache Airflow (Workflow Orchestration DAG)
         └── dbt Core       (Data Transformation, Quality Testing, Lineage)
         │
         ▼
  [ LAYER 4: MACHINE LEARNING & EXPLAINABLE AI ]
         │
         ├── Feature Engineering & Dataset Split
         ├── Model Training & Evaluation (LR, RF, XGBoost)
         ├── Model Selection & Artifact Saving (saved_models/)
         ├── SHAP Explainability Generation
         └── Scoring & Integration -> marts.fact_fraud_prediction
         │
         ▼
  [ LAYER 5: ANALYTICS & INTERACTION ]
         │
         ├── Metabase Dashboard (Visual KPIs, Fraud Monitoring)
         ├── FastAPI Service    (REST Endpoints for Scoring & Predictions)
         └── AI Assistant       (Text-to-SQL + LLM Prompt + Read-only DB)
```

---

## 2. QUY TRÌNH DỮ LIỆU (DATA FLOW PIPELINE)

1. **Ingestion:** Script Python đọc CSV dữ liệu thô, nạp trực tiếp vào schema `raw` của PostgreSQL.
2. **Staging:** dbt thực hiện chuyển từ `raw` sang `staging` (ép kiểu dữ liệu, làm sạch tên cột, tạo natural key).
3. **Marts (Data Warehouse):** dbt xây dựng các bảng **Dimension** và **Fact** theo mô hình **Star Schema** tại schema `marts`.
4. **Machine Learning:** Script ML lấy dữ liệu từ `marts.fact_transaction` kết hợp các bảng `dim_*`, tạo đặc trưng, thực hiện dự đoán rủi ro gian lận và tính SHAP value.
5. **Prediction Integration:** Lưu kết quả dự đoán (xác suất gian lận, nhãn dự đoán, risk score) vào `marts.fact_fraud_prediction`.
6. **Visualization & AI:** Metabase đọc schema `marts` để hiển thị dashboard; AI Assistant nhận câu hỏi tự nhiên, sinh SQL chỉ đọc (`SELECT`), thực thi trên DW và trả lời người dùng bằng ngôn ngữ tự nhiên.
