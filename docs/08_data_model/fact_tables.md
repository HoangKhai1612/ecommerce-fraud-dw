# FACT TABLES DESIGN

**Dự án:** Ecommerce Fraud Detection Data Warehouse  
**Phase:** 08 — Data Modeling  
**Ngày tạo:** 02/09/2026  

---

## 1. fact_transaction

### 1.1. Mô tả
Bảng Fact chính chứa thông tin giao dịch và nhãn fraud. Là trung tâm của Star Schema.

### 1.2. Schema

| Column | Data Type | Key Type | Nullable | Mô tả |
|--------|-----------|----------|----------|-------|
| `transaction_key` | BIGSERIAL | PK (SK) | NOT NULL | Surrogate key |
| `transaction_id` | BIGINT | NK | NOT NULL | TransactionID gốc |
| `date_key` | INT | FK → dim_date | NOT NULL | DDMMYYYY |
| `product_key` | INT | FK → dim_product | NOT NULL | ProductCD |
| `card_key` | INT | FK → dim_card | YES | Thẻ |
| `device_key` | INT | FK → dim_device | YES (LEFT JOIN) | Thiết bị |
| `email_key` | INT | FK → dim_email | YES | Email |
| `transaction_amt` | NUMERIC(12,2) | Measure | NOT NULL | Số tiền ($) |
| `is_fraud` | SMALLINT | Measure | NOT NULL | 0/1 |
| `created_at` | TIMESTAMP | Attribute | NOT NULL | Thời gian load |

### 1.3. Indexes

```sql
CREATE INDEX idx_fact_trans_trans_id ON marts.fact_transaction(transaction_id);
CREATE INDEX idx_fact_trans_is_fraud ON marts.fact_transaction(is_fraud);
CREATE INDEX idx_fact_trans_product  ON marts.fact_transaction(product_key);
CREATE INDEX idx_fact_trans_date     ON marts.fact_transaction(date_key);
```

### 1.4. Tests (dbt)

| Test | Column | Mô tả |
|------|--------|-------|
| not_null | transaction_key, transaction_id | PK + NK không null |
| unique | transaction_key | SK unique |
| unique | transaction_id | Mỗi transaction 1 lần |
| relationships | date_key → dim_date | FK hợp lệ |
| relationships | product_key → dim_product | FK hợp lệ |

---

## 2. fact_fraud_prediction

### 2.1. Mô tả
Bảng Fact lưu kết quả dự đoán fraud của model. Mỗi transaction có thể có nhiều dòng nếu chạy model khác nhau.

### 2.2. Schema

| Column | Data Type | Key Type | Nullable | Mô tả |
|--------|-----------|----------|----------|-------|
| `prediction_key` | BIGSERIAL | PK (SK) | NOT NULL | Surrogate key |
| `transaction_id` | BIGINT | FK → fact_transaction | NOT NULL | Giao dịch |
| `fraud_probability` | NUMERIC(5,4) | Measure | NOT NULL | Xác suất 0-1 |
| `predicted_label` | SMALLINT | Measure | NOT NULL | 0/1 |
| `risk_score` | SMALLINT | Measure | NOT NULL | 0-100 |
| `risk_level` | VARCHAR(20) | Attribute | NOT NULL | LOW/MEDIUM/HIGH/CRITICAL |
| `model_version` | VARCHAR(50) | Attribute | NOT NULL | Ví dụ: XGBoost_v1.0 |
| `predicted_at` | TIMESTAMP | Attribute | NOT NULL | Thời gian chạy |

### 2.3. Risk Score Definition

| Risk Level | Score Range | Ý nghĩa |
|------------|-------------|----------|
| LOW | 0-25 | Giao dịch bình thường |
| MEDIUM | 26-50 | Cần kiểm tra |
| HIGH | 51-75 | Có dấu hiệu gian lận |
| CRITICAL | 76-100 | Rất có khả năng gian lận |

**Công thức:**
```python
risk_score = int(fraud_probability * 100)
risk_level = 'LOW' if score <= 25 else 'MEDIUM' if score <= 50 else 'HIGH' if score <= 75 else 'CRITICAL'
```

### 2.4. Tests (dbt)

| Test | Column | Mô tả |
|------|--------|-------|
| not_null | prediction_key, transaction_id | PK + FK không null |
| unique | prediction_key | SK unique |
| relationships | transaction_id → fact_transaction | FK hợp lệ |
| accepted_values | predicted_label | Chỉ được 0 hoặc 1 |
| accepted_values | risk_level | LOW/MEDIUM/HIGH/CRITICAL |

---

## 3. SUMMARY

| Fact Table | Grain | Rows (expected) | Dimensions |
|-----------|-------|-----------------|------------|
| fact_transaction | 1 row per transaction | 590,540 | date, product, card, device, email |
| fact_fraud_prediction | 1 row per (transaction, model) | 590,540 | transaction |

*Cập nhật: 02/09/2026 | Version: 1.0*
