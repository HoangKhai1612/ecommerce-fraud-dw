# LOGICAL MODEL

**Dự án:** Ecommerce Fraud Detection Data Warehouse  
**Phase:** 08 — Data Modeling  
**Ngày tạo:** 02/09/2026  

---

## 1. MỤC TIÊU

Thiết kế **Logical Data Model** chi tiết các bảng, cột, kiểu dữ liệu, khóa chính, khóa ngoại ở mức logic (trước khi chuyển thành SQL).

---

## 2. LOGICAL TABLE DESIGN

### 2.1. Fact Tables

#### `fact_transaction`
| Column | Data Type | Key Type | Mô tả |
|--------|-----------|----------|-------|
| transaction_key | BIGINT (IDENTITY) | Primary Key (SK) | Surrogate key |
| transaction_id | BIGINT | Natural Key | Mã giao dịch (TransactionID) |
| date_key | INT | Foreign Key | Tham chiếu dim_date |
| product_key | INT | Foreign Key | Tham chiếu dim_product |
| card_key | INT | Foreign Key | Tham chiếu dim_card |
| device_key | INT | Foreign Key | Tham chiếu dim_device |
| email_key | INT | Foreign Key | Tham chiếu dim_email |
| transaction_amt | NUMERIC(12,2) | Measure | Giá trị giao dịch |
| is_fraud | SMALLINT | Measure/Label | 0=Non-Fraud, 1=Fraud |

#### `fact_fraud_prediction`
| Column | Data Type | Key Type | Mô tả |
|--------|-----------|----------|-------|
| prediction_key | BIGINT (IDENTITY) | Primary Key (SK) | Surrogate key |
| transaction_id | BIGINT | Foreign Key | Mã giao dịch |
| fraud_probability | NUMERIC(5,4) | Measure | Xác suất fraud (0-1) |
| predicted_label | SMALLINT | Measure | Nhãn dự đoán (0/1) |
| risk_score | SMALLINT | Measure | Điểm rủi ro (0-100) |
| risk_level | VARCHAR(20) | Attribute | LOW/MEDIUM/HIGH/CRITICAL |
| model_version | VARCHAR(50) | Attribute | Phiên bản model |
| predicted_at | TIMESTAMP | Attribute | Thời gian dự đoán |

### 2.2. Dimension Tables

#### `dim_date`
| Column | Data Type | Key Type | Mô tả |
|--------|-----------|----------|-------|
| date_key | INT | Primary Key | YYYYMMDD |
| full_date | DATE | Natural Key | Ngày tháng |
| day_of_week | VARCHAR(10) | Attribute | Thứ trong tuần |
| day_of_month | SMALLINT | Attribute | Ngày trong tháng |
| month | SMALLINT | Attribute | Tháng |
| quarter | SMALLINT | Attribute | Quý |
| year | SMALLINT | Attribute | Năm |

#### `dim_product`
| Column | Data Type | Key Type | Mô tả |
|--------|-----------|----------|-------|
| product_key | SERIAL | Primary Key (SK) | Surrogate key |
| product_cd | VARCHAR(1) | Natural Key | W, H, C, S, R |
| product_category_name | VARCHAR(50) | Attribute | Tên danh mục |

#### `dim_card`
| Column | Data Type | Key Type | Mô tả |
|--------|-----------|----------|-------|
| card_key | SERIAL | Primary Key (SK) | Surrogate key |
| card1 | VARCHAR(10) | Natural Key | Loại thẻ |
| card2 | VARCHAR(10) | Attribute | Thương hiệu |
| card3 | VARCHAR(10) | Attribute | Country code |
| card4 | VARCHAR(20) | Attribute | Visa/Mastercard/... |
| card5 | VARCHAR(20) | Attribute | Loại thẻ |
| card6 | VARCHAR(20) | Attribute | Debit/Credit |

#### `dim_device`
| Column | Data Type | Key Type | Mô tả |
|--------|-----------|----------|-------|
| device_key | SERIAL | Primary Key (SK) | Surrogate key |
| device_type | VARCHAR(20) | Natural Key | desktop/mobile/Unknown |
| device_info | VARCHAR(255) | Attribute | Thông tin thiết bị |

#### `dim_email`
| Column | Data Type | Key Type | Mô tả |
|--------|-----------|----------|-------|
| email_key | SERIAL | Primary Key (SK) | Surrogate key |
| p_email_domain | VARCHAR(255) | Natural Key | Email người mua |
| r_email_domain | VARCHAR(255) | Attribute | Email người nhận |
| is_free_email | BOOLEAN | Attribute | Gmail/Yahoo = free |

---

## 3. JOIN PATHS

```sql
-- Fact transaction → all dimensions
SELECT 
    f.transaction_id,
    f.transaction_amt,
    f.is_fraud,
    d.full_date,
    p.product_cd,
    c.card4,
    dev.device_type,
    e.p_email_domain
FROM marts.fact_transaction f
JOIN marts.dim_date d      ON f.date_key = d.date_key
JOIN marts.dim_product p   ON f.product_key = p.product_key
JOIN marts.dim_card c      ON f.card_key = c.card_key
JOIN marts.dim_device dev  ON f.device_key = dev.device_key
JOIN marts.dim_email e     ON f.email_key = e.email_key
```

---

## 4. DATA TYPES MAPPING (PostgreSQL)

| Logical Type | PostgreSQL Type | Notes |
|--------------|----------------|-------|
| BIGINT (IDENTITY) | BIGSERIAL | Auto-increment surrogate key |
| INT | INTEGER | For surrogate keys of small dimensions |
| NUMERIC(12,2) | NUMERIC(12,2) | Money amounts |
| NUMERIC(5,4) | NUMERIC(5,4) | Probabilities (0.0000-1.0000) |
| VARCHAR(n) | VARCHAR(n) | String attributes |
| BOOLEAN | BOOLEAN | Flags |
| TIMESTAMP | TIMESTAMP | DateTime |
| DATE | DATE | Date |
| SMALLINT | SMALLINT | 0/1 labels, small numbers |

*Cập nhật: 02/09/2026 | Version: 1.0*
