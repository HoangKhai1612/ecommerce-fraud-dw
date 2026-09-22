# SYSTEM REQUIREMENTS (FUNCTIONAL & NON-FUNCTIONAL)

**Dự án:** Ecommerce Fraud Detection Data Warehouse  
**Phase:** 02 — Problem Analysis  
**Ngày tạo:** 02/09/2026

---

## 1. YÊU CẦU CHỨC NĂNG (FUNCTIONAL REQUIREMENTS - FR)

| Requirement ID | Tên chức năng | Mô tả chi tiết | Component phụ trách |
|----------------|---------------|----------------|---------------------|
| **FR-01** | Data Ingestion | Đọc dữ liệu thô từ file CSV (IEEE-CIS) và nạp vào lớp `RAW` của PostgreSQL mà không biến đổi nghiệp vụ. | Python Ingestion |
| **FR-02** | Data Cleaning & Staging | Ép kiểu dữ liệu, đổi tên cột chuẩn hóa, xử lý missing/duplicate cơ bản từ lớp `RAW` sang lớp `STAGING`. | dbt / SQL |
| **FR-03** | Data Warehouse Transformation | Biến đổi dữ liệu từ `STAGING` thành các bảng Fact và Dimension theo mô hình Star Schema. | dbt Core |
| **FR-04** | Pipeline Orchestration | Lập lịch, điều phối và tự động hóa toàn bộ quy trình ETL/ELT từ Ingestion -> RAW -> STAGING -> DW. | Apache Airflow |
| **FR-05** | Data Quality Verification | Thực hiện các kiểm tra tính toàn vẹn (unique, not null, relationships, accepted values) trên DW. | dbt tests |
| **FR-06** | Machine Learning Training | Huấn luyện và so sánh 3 mô hình (Logistic Regression, Random Forest, XGBoost) trên tập dữ liệu đã chuẩn hóa. | Python ML (scikit-learn, XGBoost) |
| **FR-07** | Fraud Prediction & Scoring | Dự đoán nhãn gian lận (0/1), xác suất gian lận (probability) và tính toán điểm rủi ro (risk score). | Python ML |
| **FR-08** | Prediction Integration | Lưu kết quả dự đoán gian lận và risk score ngược trở lại Data Warehouse (`fact_fraud_prediction`). | Python / PostgreSQL |
| **FR-09** | Model Explainability | Giải thích các đặc trưng ảnh hưởng đến kết quả dự đoán mô hình gian lận bằng SHAP. | SHAP Library |
| **FR-10** | BI Dashboard Visualization | Hiển thị các chỉ số KPI, xu hướng gian lận, phân bố rủi ro theo thời gian, thiết bị, giá trị giao dịch. | Metabase |
| **FR-11** | REST API Service | Cung cấp API endpoints cho phép tra cứu giao dịch, dự đoán rủi ro gian lận và kiểm tra health check. | FastAPI |
| **FR-12** | AI Assistant (Text-to-SQL) | Chuyển câu hỏi ngôn ngữ tự nhiên thành SQL, kiểm tra an toàn và thực thi trên tài khoản Read-only của DW. | LLM / Ollama |

---

## 2. YÊU CẦU PHI CHỨC NĂNG (NON-FUNCTIONAL REQUIREMENTS - NFR)

| Requirement ID | Tiêu chí | Mô tả chi tiết |
|----------------|----------|----------------|
| **NFR-01** | Reusability & Idempotency | Các task trong pipeline có thể chạy lại nhiều lần (re-runnable) mà không gây trùng lặp dữ liệu hay hỏng state. |
| **NFR-02** | Fault Tolerance & Retry | Pipeline tự động thử lại (retry) khi gặp lỗi kết nối chốc tháp và ghi vết log đầy đủ. |
| **NFR-03** | Read-Only Security for AI | AI Assistant bắt buộc dùng tài khoản PostgreSQL chỉ có quyền `SELECT`. Chặn các câu lệnh sửa đổi dữ liệu (DROP, DELETE, UPDATE, INSERT). |
| **NFR-04** | Containerization | Toàn bộ các dịch vụ (PostgreSQL, Airflow, Metabase, API, AI Assistant) có thể đóng gói và khởi chạy qua Docker Compose. |
| **NFR-05** | Metric Reproducibility | Quá trình chia tập train/val/test và huấn luyện mô hình phải cố định random seed để kết quả có thể tái lập. |
| **NFR-06** | Document Traceability | Mọi yêu cầu từ đề cương phải được ánh xạ rõ ràng tới code, test case, bằng chứng và chương báo cáo tương ứng. |
