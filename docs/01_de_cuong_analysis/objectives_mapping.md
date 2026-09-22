# OBJECTIVES MAPPING

**Dự án:** Ecommerce Fraud Detection Data Warehouse  
**Phase:** 01 — Đề cương Analysis  
**Ngày tạo:** 02/09/2026  

---

## 1. MỤC TIÊU TỔNG QUÁT (THEO ĐỀ CƯƠNG)

> "Xây dựng hệ thống phân tích dữ liệu giao dịch thương mại điện tử, tích hợp Data Engineering, Data Warehouse, Machine Learning và Large Language Model (LLM), có khả năng tự động xử lý dữ liệu, phát hiện giao dịch có nguy cơ gian lận, trực quan hóa kết quả và hỗ trợ người dùng truy vấn dữ liệu bằng ngôn ngữ tự nhiên."

---

## 2. MỤC TIÊU CỤ THỂ → HỆ THỐNG PHẢN ỨNG

| Mục tiêu | Hệ thống/Thành phần | Thành công đo lường bằng |
|----------|---------------------|--------------------------|
| Xây dựng pipeline thu thập, xử lý dữ liệu | Python Ingestion + PostgreSQL RAW | CSV → DB, row count khớp |
| Pipeline có khả năng chạy tự động theo lịch | Apache Airflow DAG | DAG chạy thành công, có retry |
| Có cơ chế kiểm tra dữ liệu | Data Quality checks | dbt tests pass, quality report |
| Có khả năng retry khi task thất bại | Airflow retry config | Chứng minh bằng failure test |
| Data Warehouse theo Star Schema | PostgreSQL marts schema | Fact + Dimension tables tồn tại |
| Dữ liệu được phân chia RAW/STAGING/DW | PostgreSQL schemas | 3 schemas tồn tại |
| Feature Engineering + imbalance handling | ML pipeline | Features documented, SMOTE/class_weight |
| 3 models đã train và compare | scikit-learn, XGBoost | Metrics table cho 3 models |
| So sánh dựa trên Precision/Recall/F1/ROC-AUC/PR-AUC | 3 models | Bảng so sánh đầy đủ |
| SHAP explanation | SHAP library | PNG global + local plots |
| Lưu kết quả dự đoán, risk score vào DW | fact_fraud_prediction table | SELECT count(*) > 0 |
| Dashboard theo dõi giao dịch, fraud, risk | Metabase | ≥5 KPI charts |
| AI Assistant Text-to-SQL | LLM + FastAPI | Trả lời ≥80% câu hỏi đúng |
| Docker Compose khởi chạy được | docker-compose.yml | `docker compose up` success |

---

## 3. MỤC TIÊU HỌC THUẬT → KĨ NĂNG PHÁT TRIỂN

| Kỹ năng | Mục tiêu học được | Đánh giá bởi |
|--------|------------------|-------------|
| Data Engineering | Thiết kế ETL/ELT pipeline | Code pipeline chạy được |
| Data Warehouse | Dimensional Modeling, Star Schema | Schema diagram |
| SQL | Viết complex queries | SQL trong dbt models |
| Python | Data processing, ML pipeline | Code clean, modular |
| Airflow | Orchestrate pipelines | DAG có dependencies đúng |
| dbt | Transform + test data | dbt test pass rate |
| Machine Learning | Train, evaluate, compare models | Metrics table |
| Explainable AI | SHAP giải thích predictions | SHAP plots |
| API Development | FastAPI REST API | Endpoint test pass |
| LLM/AI | Text-to-SQL, prompt engineering | 5 test questions |
| Docker | Container hóa | `docker compose up` |
| Documentation | Technical documentation | Toàn bộ docs/ có nội dung |

---

## 4. ĐIỀU KIỆN THÀNH CÔNG (SUCCESS CRITERIA)

```text
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

*Cập nhật: 02/09/2026*
