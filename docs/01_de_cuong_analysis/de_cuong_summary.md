# ĐỀ CƯƠNG SUMMARY

**Dự án:** Ecommerce Fraud Detection Data Warehouse  
**Ngày phân tích:** 02/09/2026  
**Nguồn:** `report/Đề cương 74DCTT22_12_...docx`

---

## 1. THÔNG TIN ĐỀ TÀI

| Mục | Nội dung |
|-----|---------|
| Tên đề tài | Xây dựng hệ thống Data Warehouse và phát hiện gian lận giao dịch thương mại điện tử tích hợp AI hỗ trợ phân tích |
| Học phần | Đồ án Xây dựng và Phát triển Phần mềm |
| Sinh viên | Hoàng Quốc Khải — MSSV: 74DCTT22568 — Lớp: 74DCTT22 |
| GVHD | Lê Trung Kiên |
| Trường | Đại học Công nghệ GTVT — Khoa CNTT |
| Thời gian | 24/08/2026 – 25/10/2026 |

---

## 2. TÓM TẮT MỤC TIÊU ĐỀ CƯƠNG

Đề cương yêu cầu xây dựng hệ thống tích hợp:

```
1. Data Engineering Pipeline (Python → Airflow → dbt)
2. Data Warehouse (PostgreSQL, Star Schema)
3. Fraud Detection ML (LR, RF, XGBoost)
4. Explainable AI (SHAP)
5. Dashboard (Metabase)
6. REST API (FastAPI)
7. AI Assistant (LLM + Text-to-SQL)
8. Deployment (Docker Compose)
```

---

## 3. CẤU TRÚC ĐỀ CƯƠNG (4 CHƯƠNG)

### Chương 1 — Giới thiệu tổng quan
- 1.1 Lý do chọn đề tài
- 1.2 Mục tiêu và Nhiệm vụ
  - 1.2.1 Mục tiêu
  - 1.2.2 Nhiệm vụ
- 1.3 Phạm vi nghiên cứu (Data, DE, ML, AI, Deployment)
- 1.4 Kết quả dự kiến

### Chương 2 — Kiến thức nền tảng
- 2.1 Cơ sở lý thuyết
  - Data Engineering, ETL/ELT, Batch Processing, Data Quality, Data Lineage
  - Data Warehouse, OLTP/OLAP, Dimensional Modeling, Star Schema, Surrogate Key, SCD
  - Workflow Orchestration, DAG, Scheduling
  - dbt
  - Fraud Detection, Imbalanced Dataset
  - Machine Learning: LR, RF, XGBoost, Hyperparameter Tuning
  - Đánh giá model: Confusion Matrix, Precision, Recall, F1, ROC-AUC, PR-AUC
  - Explainable AI, SHAP
  - LLM, Text-to-SQL, SQL Safety
  - BI, Dashboard, KPI
- 2.2 Công cụ sử dụng (Python, PostgreSQL, Airflow, dbt, scikit-learn, XGBoost, SHAP, FastAPI, Metabase, LLM, Docker, Git)

### Chương 3 — Phân tích Thiết kế
- 3.1 Khảo sát (bài toán, dữ liệu, yêu cầu)
- 3.2 Phân tích (quy trình dữ liệu, ML pipeline, AI Assistant)
- 3.3 Thiết kế (kiến trúc, DW, pipeline, ML pipeline, AI Assistant)

### Chương 4 — Xây dựng chương trình
- 4.1 Môi trường (Python, PostgreSQL, Docker, Airflow, dbt, Git)
- 4.2 Data Ingestion
- 4.3 Data Pipeline & Transformation (Airflow + dbt)
- 4.4 Data Quality
- 4.5 Data Warehouse (Fact + Dimension, Star Schema)
- 4.6 Fraud Detection Model (EDA, FE, imbalance, train, compare, evaluate)
- 4.7 SHAP + tích hợp model → DW
- 4.8 Dashboard (Metabase)
- 4.9 AI Assistant + FastAPI
- 4.10 Đóng gói + Kiểm thử (Docker, E2E testing)

### Kết luận
- Kết quả đã làm được
- Hạn chế
- Hướng phát triển

---

## 4. CÔNG NGHỆ THEO ĐỀ CƯƠNG

| Nhóm | Công nghệ | Version khuyến nghị |
|------|-----------|-------------------|
| Language | Python | 3.10+ |
| Database | PostgreSQL | 15+ |
| Orchestration | Apache Airflow | 2.8+ |
| Transformation | dbt Core | 1.7+ |
| ML | scikit-learn | 1.3+ |
| ML | XGBoost | 2.0+ |
| XAI | SHAP | 0.44+ |
| API | FastAPI | 0.110+ |
| Dashboard | Metabase | 0.49+ |
| LLM | Ollama / OpenAI API | — |
| Container | Docker + Docker Compose | 25+ |
| Source Control | Git / GitHub | — |

---

## 5. KẾT QUẢ DỰ KIẾN THEO ĐỀ CƯƠNG

| # | Deliverable | Tiêu chí thành công |
|---|------------|-------------------|
| 1 | Data Engineering Pipeline | Chạy tự động, có retry, có logging |
| 2 | Data Warehouse | RAW → STAGING → DIMENSION → FACT |
| 3 | Fraud Detection Model | So sánh LR/RF/XGBoost, chọn best |
| 4 | Explainable AI | SHAP explanation cho predictions |
| 5 | Dashboard | Theo dõi giao dịch, fraud, risk, trends |
| 6 | AI Assistant | NL → SQL → DW → NL, read-only |
| 7 | Docker Compose | Khởi chạy được trên local |

---

## 6. KẾ HOẠCH THỰC HIỆN THEO ĐỀ CƯƠNG

| TT | Nội dung | Thời gian | Chapters |
|----|---------|-----------|---------|
| 1 | Đề cương + Khảo sát | 24/08 – 30/08 | Ch.1 |
| 2 | Kiến thức nền tảng | 24/08 – 13/09 | Ch.2 |
| 3 | Khảo sát + Thiết kế kiến trúc | 31/08 – 13/09 | Ch.3 |
| 4 | Data Engineering + DW | 07/09 – 04/10 | Ch.3, Ch.4 |
| 5 | ML + SHAP | 28/09 – 18/10 | Ch.4 |
| 6 | Dashboard + AI Assistant | 12/10 – 25/10 | Ch.4 |
| 7 | Tích hợp + Kiểm thử + Hoàn thiện | 19/10 – 25/10 | Ch.4, Kết luận |

---

*Cập nhật: 02/09/2026 | Version: 1.0*
