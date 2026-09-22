# GLOSSARY — BẢNG THUẬT NGỮ

**Dự án:** Ecommerce Fraud Detection Data Warehouse  
**Ngày tạo:** 02/09/2026

---

## A

| Thuật ngữ | Viết tắt | Định nghĩa |
|-----------|---------|-----------|
| Accuracy | — | Tỷ lệ dự đoán đúng / tổng số dự đoán. Không dùng cho bài toán mất cân bằng |
| Apache Airflow | Airflow | Công cụ workflow orchestration, quản lý DAG và scheduling |
| AI Assistant | — | Trợ lý AI cho phép hỏi đáp bằng ngôn ngữ tự nhiên thông qua Text-to-SQL |
| AUC | — | Area Under Curve — diện tích dưới đường ROC hoặc PR |

## B

| Thuật ngữ | Viết tắt | Định nghĩa |
|-----------|---------|-----------|
| Batch Processing | — | Xử lý dữ liệu theo lô, không real-time |
| Binary Classification | — | Bài toán phân loại 2 nhãn: Fraud (1) hoặc Non-Fraud (0) |
| Business Intelligence | BI | Hệ thống phân tích và trực quan hóa dữ liệu kinh doanh |

## C

| Thuật ngữ | Viết tắt | Định nghĩa |
|-----------|---------|-----------|
| Confusion Matrix | — | Ma trận nhầm lẫn: TP, TN, FP, FN |
| CSV | — | Comma-Separated Values — định dạng file dữ liệu phổ biến |

## D

| Thuật ngữ | Viết tắt | Định nghĩa |
|-----------|---------|-----------|
| DAG | — | Directed Acyclic Graph — đồ thị có hướng không vòng lặp, dùng trong Airflow |
| Data Engineering | DE | Kỹ thuật xây dựng pipeline xử lý dữ liệu |
| Data Lineage | — | Theo dõi nguồn gốc và sự biến đổi của dữ liệu |
| Data Pipeline | — | Quy trình tự động hóa xử lý dữ liệu từ nguồn đến đích |
| Data Quality | DQ | Kiểm tra tính đúng đắn, đầy đủ và nhất quán của dữ liệu |
| Data Warehouse | DW | Hệ thống lưu trữ dữ liệu tích hợp phục vụ phân tích |
| dbt | dbt | Data Build Tool — công cụ biến đổi và kiểm tra dữ liệu |
| Dimension Table | Dim | Bảng chứa thuộc tính mô tả của Fact trong Star Schema |
| Dimensional Modeling | DM | Phương pháp thiết kế DW theo Kimball methodology |

## E

| Thuật ngữ | Viết tắt | Định nghĩa |
|-----------|---------|-----------|
| EDA | — | Exploratory Data Analysis — phân tích khám phá dữ liệu |
| ELT | — | Extract, Load, Transform — biến thể của ETL |
| ETL | — | Extract, Transform, Load — quy trình thu thập và xử lý dữ liệu |
| Explainable AI | XAI | AI có khả năng giải thích tại sao đưa ra kết quả đó |

## F

| Thuật ngữ | Viết tắt | Định nghĩa |
|-----------|---------|-----------|
| F1-score | — | Harmonic mean của Precision và Recall |
| Fact Table | Fact | Bảng trung tâm trong Star Schema, chứa measures |
| False Negative | FN | Model dự đoán là Non-Fraud nhưng thực tế là Fraud |
| False Positive | FP | Model dự đoán là Fraud nhưng thực tế là Non-Fraud |
| FastAPI | — | Framework Python để xây dựng REST API nhanh |
| Feature Engineering | FE | Tạo và lựa chọn các features phù hợp cho ML |
| Fraud | — | Giao dịch gian lận / lừa đảo |

## G

| Thuật ngữ | Viết tắt | Định nghĩa |
|-----------|---------|-----------|
| Grain | — | Mức độ chi tiết nhỏ nhất của một Fact Table |

## I

| Thuật ngữ | Viết tắt | Định nghĩa |
|-----------|---------|-----------|
| Identity Table | — | Bảng chứa thông tin định danh người dùng (IEEE-CIS dataset) |
| Imbalanced Dataset | — | Dataset có sự chênh lệch lớn giữa các nhãn (ít Fraud, nhiều Non-Fraud) |

## L

| Thuật ngữ | Viết tắt | Định nghĩa |
|-----------|---------|-----------|
| Large Language Model | LLM | Mô hình ngôn ngữ lớn (vd: GPT, Llama, Mistral) |
| Logistic Regression | LR | Thuật toán phân loại tuyến tính, dùng làm baseline |

## M

| Thuật ngữ | Viết tắt | Định nghĩa |
|-----------|---------|-----------|
| Metabase | — | Công cụ Business Intelligence mã nguồn mở |
| Model Artifact | — | File lưu model đã train (.pkl, .joblib) |

## O

| Thuật ngữ | Viết tắt | Định nghĩa |
|-----------|---------|-----------|
| OLAP | — | Online Analytical Processing — xử lý phân tích |
| OLTP | — | Online Transaction Processing — xử lý giao dịch |
| Ollama | — | Công cụ chạy LLM local trên máy tính |

## P

| Thuật ngữ | Viết tắt | Định nghĩa |
|-----------|---------|-----------|
| Pipeline | — | Quy trình xử lý dữ liệu/ML có thứ tự |
| PostgreSQL | PG | Hệ quản trị CSDL quan hệ mã nguồn mở |
| PR-AUC | — | Area Under Precision-Recall Curve — tốt hơn ROC-AUC cho imbalanced data |
| Precision | — | TP / (TP + FP) — trong số dự đoán Fraud, bao nhiêu đúng |

## R

| Thuật ngữ | Viết tắt | Định nghĩa |
|-----------|---------|-----------|
| Random Forest | RF | Thuật toán ensemble sử dụng nhiều Decision Trees |
| RAW Layer | RAW | Lớp dữ liệu nguồn, chưa biến đổi |
| Recall | — | TP / (TP + FN) — trong số Fraud thực, bao nhiêu được phát hiện |
| ROC-AUC | — | Receiver Operating Characteristic — Area Under Curve |

## S

| Thuật ngữ | Viết tắt | Định nghĩa |
|-----------|---------|-----------|
| SHAP | — | SHapley Additive exPlanations — phương pháp XAI |
| SMOTE | — | Synthetic Minority Over-sampling Technique |
| SQL | — | Structured Query Language |
| SQL Injection | — | Tấn công chèn SQL nguy hiểm |
| SQL Validation | — | Kiểm tra SQL trước khi thực thi |
| Star Schema | — | Mô hình DW với 1 Fact Table trung tâm và nhiều Dimension Tables |
| STAGING Layer | STG | Lớp dữ liệu đã được chuẩn hóa cơ bản |
| Surrogate Key | SK | Khóa nhân tạo thay thế natural key trong Dimension |

## T

| Thuật ngữ | Viết tắt | Định nghĩa |
|-----------|---------|-----------|
| Text-to-SQL | — | Chuyển câu hỏi ngôn ngữ tự nhiên thành câu lệnh SQL |
| True Negative | TN | Model dự đoán Non-Fraud, thực tế là Non-Fraud |
| True Positive | TP | Model dự đoán Fraud, thực tế là Fraud |

## X

| Thuật ngữ | Viết tắt | Định nghĩa |
|-----------|---------|-----------|
| XGBoost | XGB | eXtreme Gradient Boosting — thuật toán boosting mạnh |

---

*Cập nhật: 02/09/2026 | Version: 1.0*
