# DATA WAREHOUSE PHYSICAL MODEL (STAR SCHEMA)

**Dự án:** Ecommerce Fraud Detection Data Warehouse  
**Phase:** 08 — Data Modeling  
**Ngày tạo:** 02/09/2026

---

## 1. MỨC ĐỘ CHI TIẾT (GRAIN DEFINITION)

- **`fact_transaction`**: Mỗi dòng đại diện cho một giao dịch thương mại điện tử thực tế được xác định bởi `transaction_id`.
- **`fact_fraud_prediction`**: Mỗi dòng đại diện cho kết quả dự đoán và điểm đánh giá rủi ro từ mô hình Machine Learning cho một giao dịch.

---

## 2. BẢNG FACT (FACT TABLES)

### 2.1. `marts.fact_transaction`
| Column Name | Data Type | Key Type | Mô tả |
|-------------|-----------|----------|-------|
| `transaction_key` | BIGINT / SERIAL | Primary Key (SK) | Khóa thay thế của Fact Transaction |
| `transaction_id` | BIGINT | Natural Key | Mã giao dịch gốc |
| `date_key` | INT | Foreign Key | Tham chiếu tới `dim_date` |
| `product_key` | INT | Foreign Key | Tham chiếu tới `dim_product` |
| `card_key` | INT | Foreign Key | Tham chiếu tới `dim_card` |
| `device_key` | INT | Foreign Key | Tham chiếu tới `dim_device` |
| `email_key` | INT | Foreign Key | Tham chiếu tới `dim_email` |
| `transaction_amt` | NUMERIC(12,2) | Measure | Giá trị tiền giao dịch ($) |
| `is_fraud` | INT | Measure/Label | 0: Hop le, 1: Gian lan |

### 2.2. `marts.fact_fraud_prediction`
| Column Name | Data Type | Key Type | Mô tả |
|-------------|-----------|----------|-------|
| `prediction_key` | BIGINT / SERIAL | Primary Key (SK) | Khóa chính của bảng dự đoán |
| `transaction_id` | BIGINT | Foreign Key / NK | Mã giao dịch liên kết |
| `fraud_probability` | NUMERIC(5,4) | Measure | Xác suất gian lận (0.0000 - 1.0000) |
| `predicted_label` | INT | Measure | Nhãn dự đoán (0 hoặc 1) |
| `risk_score` | INT | Measure | Thang điểm rủi ro (0 - 100) |
| `risk_level` | VARCHAR(20) | Attribute | Mức độ rủi ro: LOW, MEDIUM, HIGH, CRITICAL |
| `model_version` | VARCHAR(50) | Attribute | Phiên bản mô hình (vd: `XGBoost_v1.0`) |
| `predicted_at` | TIMESTAMP | Attribute | Thời gian thực hiện dự đoán |

---

## 3. BẢNG DIMENSION (DIMENSION TABLES)

### 3.1. `marts.dim_product`
- `product_key` (PK), `product_cd`, `product_category_name`.

### 3.2. `marts.dim_card`
- `card_key` (PK), `card1`, `card2`, `card3`, `card4` (Visa/Mastercard), `card5`, `card6` (Credit/Debit).

### 3.3. `marts.dim_device`
- `device_key` (PK), `device_type` (desktop/mobile/Unknown), `device_info`.

### 3.4. `marts.dim_email`
- `email_key` (PK), `p_email_domain`, `r_email_domain`, `is_free_email`.

### 3.5. `marts.dim_date`
- `date_key` (PK - YYYYMMDD), `full_date`, `day_of_week`, `day_of_month`, `month`, `quarter`, `year`.
