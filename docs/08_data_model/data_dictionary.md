# DATA DICTIONARY

**Dự án:** Ecommerce Fraud Detection Data Warehouse  
**Phase:** 08 — Data Modeling  
**Ngày tạo:** 02/09/2026  

---

## 1. STAR SCHEMA DATA DICTIONARY

### Schema: `marts`

---

## 2. FACT TABLES

### `marts.fact_transaction`

| Column | Data Type | Key Type | Description |
|--------|-----------|----------|-------------|
| `transaction_key` | BIGSERIAL | PK (SK) | Surrogate key for fact_transaction |
| `transaction_id` | BIGINT | NK | Original TransactionID from source |
| `date_key` | INT | FK → dim_date | Date key (YYYYMMDD) |
| `product_key` | INT | FK → dim_product | Product code dimension |
| `card_key` | INT | FK → dim_card | Card information dimension |
| `device_key` | INT | FK → dim_device | Device information dimension |
| `email_key` | INT | FK → dim_email | Email domain dimension |
| `transaction_amt` | NUMERIC(12,2) | Measure | Transaction amount in USD |
| `is_fraud` | SMALLINT | Measure/Label | 0=Non-Fraud, 1=Fraud |
| `created_at` | TIMESTAMP | Attribute | Timestamp when record was loaded |

### `marts.fact_fraud_prediction`

| Column | Data Type | Key Type | Description |
|--------|-----------|----------|-------------|
| `prediction_key` | BIGSERIAL | PK (SK) | Surrogate key for prediction record |
| `transaction_id` | BIGINT | FK → fact_transaction | Links to transaction |
| `fraud_probability` | NUMERIC(5,4) | Measure | Fraud probability (0.0000 - 1.0000) |
| `predicted_label` | SMALLINT | Measure | Predicted label (0 or 1) |
| `risk_score` | SMALLINT | Measure | Risk score (0 - 100) |
| `risk_level` | VARCHAR(20) | Attribute | LOW, MEDIUM, HIGH, CRITICAL |
| `model_version` | VARCHAR(50) | Attribute | Model identifier (e.g., XGBoost_v1.0) |
| `predicted_at` | TIMESTAMP | Attribute | When prediction was made |

---

## 3. DIMENSION TABLES

### `marts.dim_date`

| Column | Data Type | Key Type | Description |
|--------|-----------|----------|-------------|
| `date_key` | INT | PK | Date key in YYYYMMDD format |
| `transaction_date` | DATE | NK | Full date |
| `day_of_week` | VARCHAR(10) | Attribute | Day name (Monday, etc.) |
| `day_of_month` | SMALLINT | Attribute | Day of month (1-31) |
| `day_of_year` | SMALLINT | Attribute | Day of year (1-365) |
| `week_of_year` | SMALLINT | Attribute | ISO week number |
| `month` | SMALLINT | Attribute | Month (1-12) |
| `quarter` | SMALLINT | Attribute | Quarter (1-4) |
| `year` | SMALLINT | Attribute | Year (e.g., 2017) |

### `marts.dim_product`

| Column | Data Type | Key Type | Description |
|--------|-----------|----------|-------------|
| `product_key` | SERIAL | PK (SK) | Surrogate key |
| `product_cd` | VARCHAR(1) | NK | W, H, C, S, R |
| `product_category_name` | VARCHAR(50) | Attribute | Product category name |

### `marts.dim_card`

| Column | Data Type | Key Type | Description |
|--------|-----------|----------|-------------|
| `card_key` | SERIAL | PK (SK) | Surrogate key |
| `card1` | VARCHAR(10) | NK | Card type 1 (1-6) |
| `card2` | VARCHAR(10) | Attribute | Card brand |
| `card3` | VARCHAR(10) | Attribute | Country code |
| `card4` | VARCHAR(20) | Attribute | visa, mastercard, etc. |
| `card5` | VARCHAR(20) | Attribute | Card brand name |
| `card6` | VARCHAR(20) | Attribute | debit, credit |

### `marts.dim_device`

| Column | Data Type | Key Type | Description |
|--------|-----------|----------|-------------|
| `device_key` | SERIAL | PK (SK) | Surrogate key |
| `device_type` | VARCHAR(20) | NK | desktop, mobile, Unknown |
| `device_info` | VARCHAR(255) | Attribute | Device/browser info |

### `marts.dim_email`

| Column | Data Type | Key Type | Description |
|--------|-----------|----------|-------------|
| `email_key` | SERIAL | PK (SK) | Surrogate key |
| `p_email_domain` | VARCHAR(255) | NK | Buyer email domain |
| `r_email_domain` | VARCHAR(255) | Attribute | Recipient email domain |
| `is_free_email` | BOOLEAN | Attribute | True if Gmail/Yahoo/etc. |

---

## 4. RAW + STAGING TABLES

### `raw.transactions`
- **Source**: `data/raw/train_transaction.csv`
- **Columns**: 394 (TransactionID, isFraud, ..., V339)
- **Grain**: 1 row per transaction
- **Rows**: 590,540

### `raw.identity`
- **Source**: `data/raw/train_identity.csv`
- **Columns**: 41 (TransactionID, id_01, ..., DeviceInfo)
- **Grain**: 1 row per identity
- **Rows**: 144,233

### `staging.stg_transactions`
- **Source**: `raw.transactions`
- **Transformation**: Rename columns, cast types

### `staging.stg_identity`
- **Source**: `raw.identity`
- **Transformation**: Rename columns, cast types

---

## 5. COLUMN MAPPING (RAW → STAR SCHEMA)

| Raw Column | Staging Column | DW Column |
|-----------|----------------|-----------|
| `TransactionID` | `transaction_id` | `transaction_id` |
| `isFraud` | `is_fraud` | `is_fraud` |
| `TransactionDT` | `transaction_dt` | `date_key` (converted) |
| `TransactionAmt` | `transaction_amt` | `transaction_amt` |
| `ProductCD` | `product_cd` | `dim_product.product_cd` |
| `card1`...`card6` | `card1`...`card6` | `dim_card.card1`...`card6` |
| `DeviceType` | `device_type` | `dim_device.device_type` |
| `DeviceInfo` | `device_info` | `dim_device.device_info` |
| `P_emaildomain` | `p_emaildomain` | `dim_email.p_email_domain` |
| `R_emaildomain` | `r_emaildomain` | `dim_email.r_email_domain` |

*Cập nhật: 02/09/2026 | Version: 1.0*
