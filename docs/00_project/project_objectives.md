# PROJECT OBJECTIVES

**Dự án:** Ecommerce Fraud Detection Data Warehouse  
**Ngày tạo:** 02/09/2026

---

## 1. MỤC TIÊU TỔNG QUÁT

Xây dựng một hệ thống phân tích dữ liệu giao dịch thương mại điện tử, tích hợp đầy đủ:
- Data Engineering Pipeline
- Data Warehouse
- Machine Learning cho Fraud Detection
- Explainable AI (SHAP)
- Business Intelligence Dashboard
- AI Assistant (Text-to-SQL)
- REST API

---

## 2. MỤC TIÊU CỤ THỂ

### M1 — Data Engineering Pipeline
**Mục tiêu:** Xây dựng pipeline tự động hóa từ nguồn dữ liệu đến Data Warehouse  
**Đo lường:** Pipeline chạy được end-to-end, có retry, có logging  
**Công nghệ:** Python, Apache Airflow, dbt

### M2 — Data Warehouse
**Mục tiêu:** Thiết kế và triển khai Data Warehouse theo Dimensional Modeling  
**Đo lường:** Star Schema với ≥2 Fact Tables và ≥5 Dimension Tables  
**Công nghệ:** PostgreSQL, dbt

### M3 — Data Quality
**Mục tiêu:** Đảm bảo dữ liệu trong DW đáng tin cậy  
**Đo lường:** ≥10 data quality tests, 0 critical failures  
**Công nghệ:** dbt tests, Python validation

### M4 — Fraud Detection Model
**Mục tiêu:** So sánh 3 models và chọn best model  
**Đo lường:** F1-score ≥ 0.7 trên test set (với class fraud)  
**Công nghệ:** scikit-learn, XGBoost

### M5 — Explainable AI
**Mục tiêu:** Giải thích tại sao model đánh giá giao dịch là fraud  
**Đo lường:** SHAP global + local explanation được tạo ra  
**Công nghệ:** SHAP library

### M6 — Dashboard
**Mục tiêu:** Trực quan hóa dữ liệu giao dịch và kết quả fraud detection  
**Đo lường:** ≥5 KPI charts, dữ liệu cập nhật từ DW  
**Công nghệ:** Metabase

### M7 — API
**Mục tiêu:** Cung cấp REST API cho hệ thống  
**Đo lường:** ≥4 endpoints hoạt động, có documentation  
**Công nghệ:** FastAPI

### M8 — AI Assistant
**Mục tiêu:** Cho phép truy vấn DW bằng ngôn ngữ tự nhiên  
**Đo lường:** Trả lời đúng ≥80% câu hỏi test, không có SQL nguy hiểm  
**Công nghệ:** LLM, Text-to-SQL, SQL Validation

### M9 — Deployment
**Mục tiêu:** Hệ thống khởi chạy được bằng Docker Compose  
**Đo lường:** `docker compose up` hoạt động, tất cả service healthy  
**Công nghệ:** Docker, Docker Compose

### M10 — Testing & Documentation
**Mục tiêu:** Hệ thống được kiểm thử đầy đủ và có documentation  
**Đo lường:** Unit + Integration + E2E tests, toàn bộ docs/ được viết  
**Công nghệ:** pytest, Markdown

---

## 3. MỤC TIÊU HỌC THUẬT

Sau khi hoàn thành đồ án, sinh viên phải có khả năng:

| Kỹ năng | Mô tả |
|---------|-------|
| Data Engineering | Thiết kế và triển khai ETL/ELT pipeline |
| Data Warehouse | Dimensional Modeling, Star Schema |
| SQL | Viết complex queries trên PostgreSQL |
| Python | Data processing, ML pipeline |
| Airflow | Orchestrate data pipelines |
| dbt | Transform và test data |
| Machine Learning | Train, evaluate, compare models |
| Explainable AI | Giải thích kết quả ML bằng SHAP |
| API Development | FastAPI REST API |
| LLM/AI | Text-to-SQL, prompt engineering |
| Docker | Container hóa ứng dụng |
| Documentation | Viết technical documentation |

---

## 4. TIÊU CHÍ THÀNH CÔNG (SUCCESS CRITERIA)

```
[ ] Pipeline chạy end-to-end không lỗi
[ ] DW có đủ Fact + Dimension theo Star Schema
[ ] 3 models đã train, compare, chọn được best model
[ ] SHAP explanation được tạo ra
[ ] Dashboard có ≥5 KPI
[ ] API /predict hoạt động
[ ] AI Assistant trả lời câu hỏi bằng tiếng Việt
[ ] Docker Compose up thành công
[ ] Báo cáo 4 chương hoàn chỉnh
[ ] Demo chạy được
```

---

*Cập nhật: 02/09/2026 | Version: 1.0*
