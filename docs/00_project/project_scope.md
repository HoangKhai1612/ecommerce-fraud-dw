# PROJECT SCOPE

**Dự án:** Xây dựng hệ thống Data Warehouse và phát hiện gian lận giao dịch thương mại điện tử tích hợp AI hỗ trợ phân tích  
**Sinh viên:** Hoàng Quốc Khải — MSSV: 74DCTT22568  
**GVHD:** Lê Trung Kiên  
**Ngày tạo:** 02/09/2026  
**Phiên bản:** 1.0

---

## 1. PHẠM VI TRONG SCOPE (IN SCOPE)

### 1.1 Data Engineering

| Thành phần | Mô tả |
|-----------|-------|
| Python Ingestion | Đọc CSV dataset, validate, nạp vào PostgreSQL RAW layer |
| RAW Layer | Lưu dữ liệu nguồn gần nhất có thể, không biến đổi nghiệp vụ |
| STAGING Layer | Rename, cast type, standardize, clean cơ bản |
| dbt Core | Biến đổi, mô hình hóa, kiểm tra chất lượng dữ liệu |
| Apache Airflow | Điều phối pipeline, scheduling, retry, logging |
| Data Quality | Kiểm tra completeness, validity, uniqueness, consistency |

### 1.2 Data Warehouse

| Thành phần | Mô tả |
|-----------|-------|
| PostgreSQL | Cơ sở dữ liệu chính |
| Dimensional Modeling | Star Schema với Fact và Dimension tables |
| Fact Tables | Giao dịch và kết quả fraud detection |
| Dimension Tables | Thời gian, địa điểm, thiết bị, thẻ, email... |
| Surrogate Keys | SK cho các dimension tables |

### 1.3 Machine Learning

| Thành phần | Mô tả |
|-----------|-------|
| EDA | Exploratory Data Analysis |
| Feature Engineering | Tạo và lựa chọn features phù hợp |
| Imbalance Handling | SMOTE hoặc class_weight |
| Logistic Regression | Baseline model |
| Random Forest | Ensemble model |
| XGBoost | Boosting model |
| Model Evaluation | Precision, Recall, F1, ROC-AUC, PR-AUC |
| Model Selection | So sánh và chọn best model |

### 1.4 Explainable AI

| Thành phần | Mô tả |
|-----------|-------|
| SHAP | Global + local explanation |
| Feature Importance | Top features ảnh hưởng đến prediction |

### 1.5 Analytics & Visualization

| Thành phần | Mô tả |
|-----------|-------|
| Metabase | Dashboard theo dõi giao dịch và gian lận |
| KPI | Fraud rate, transaction count, risk distribution |

### 1.6 API & AI

| Thành phần | Mô tả |
|-----------|-------|
| FastAPI | REST API cho các chức năng hệ thống |
| AI Assistant | LLM + Text-to-SQL (NL → SQL → DW → NL) |
| SQL Validation | Chỉ cho phép SELECT queries |
| Read-only DB | AI chỉ được đọc, không được ghi |

### 1.7 Deployment

| Thành phần | Mô tả |
|-----------|-------|
| Docker Compose | Đóng gói và chạy local |
| Environment Variables | Cấu hình qua .env |
| Git | Quản lý source code |

---

## 2. NGOÀI PHẠM VI (OUT OF SCOPE)

| Thành phần | Lý do loại trừ |
|-----------|---------------|
| Apache Spark / Hadoop | Không cần cho quy mô nghiên cứu |
| Kafka / Streaming | Đề cương chỉ yêu cầu batch processing |
| Kubernetes / Cloud | Local deployment là đủ |
| Deep Learning | Đề cương chỉ chỉ định LR, RF, XGBoost |
| Delta Lake / Lakehouse | Vượt phạm vi |
| Microservices phức tạp | Không cần thiết |
| Frontend (React/Vue) | Metabase đã đủ cho dashboard |
| Real-time prediction | Batch là đủ |
| Dữ liệu production thực | Chỉ dùng dataset nghiên cứu công khai |
| Auto-retraining / MLOps | Extension nếu có thời gian |
| Authentication/Authorization đầy đủ | Chỉ basic security |

---

## 3. ĐIỀU KIỆN BIÊN (BOUNDARY CONDITIONS)

- Hệ thống chạy trên môi trường **local/development**
- Dataset: **IEEE-CIS Fraud Detection** (Kaggle public dataset)
- AI Assistant: chỉ **SELECT** queries, không có quyền ghi
- LLM: Ollama (local) hoặc API-based (tùy cấu hình)
- Không deploy lên cloud trong phạm vi đồ án

---

## 4. DELIVERABLES CUỐI CÙNG

| # | Deliverable | Mô tả |
|---|------------|-------|
| D1 | Source code | Toàn bộ code trên GitHub |
| D2 | Docker Compose | Hệ thống khởi chạy được bằng 1 lệnh |
| D3 | Data Pipeline | Airflow DAG chạy end-to-end |
| D4 | Data Warehouse | Star Schema trên PostgreSQL |
| D5 | ML Models | 3 models đã train và compare |
| D6 | SHAP Reports | Explanation cho best model |
| D7 | Dashboard | Metabase với các KPI |
| D8 | API | FastAPI với endpoints hoạt động |
| D9 | AI Assistant | Text-to-SQL hoạt động |
| D10 | Documentation | Toàn bộ docs/ structure |
| D11 | Báo cáo | 4 chương + kết luận |
| D12 | Evidence | Screenshot, log, test results |

---

## 5. DEFINITION OF SCOPE CONTROL

Bất kỳ thay đổi scope nào cần:
1. Được ghi vào `decision_log.md`
2. Không vượt phạm vi đề cương
3. Nếu là ý tưởng mở rộng → ghi vào `extension_backlog.md`
4. Chỉ thực hiện extension sau khi CORE = 100%

---

*Cập nhật: 02/09/2026 | Version: 1.0*
