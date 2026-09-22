# GRAIN DEFINITION

**Dự án:** Ecommerce Fraud Detection Data Warehouse  
**Phase:** 08 — Data Modeling  
**Ngày tạo:** 02/09/2026  

---

## 1. GRAIN (ĐỘ CHI TIẾT) CỦA FACT TABLES

### 1.1. `fact_transaction` — Grain

> **Mỗi dòng trong `fact_transaction` đại diện cho một giao dịch thương mại điện tử duy nhất, được xác định bởi `TransactionID`.**

#### Điều kiện:
- Một transaction_id xuất hiện **đúng 1 lần** trong fact_transaction
- Tương ứng với **1 bản ghi** trong raw.transactions
- Có thể có **0 hoặc 1** bản ghi trong raw.identity (LEFT JOIN)

#### Ví dụ:
```sql
-- Query kiểm tra grain
SELECT transaction_id, COUNT(*) as cnt
FROM marts.fact_transaction
GROUP BY transaction_id
HAVING COUNT(*) > 1;
-- Kết quả: 0 rows (mỗi transaction_id xuất hiện đúng 1 lần)
```

---

### 1.2. `fact_fraud_prediction` — Grain

> **Mỗi dòng trong `fact_fraud_prediction` đại diện cho một kết quả dự đoán fraud của một giao dịch, do một model version thực hiện.**

#### Điều kiện:
- Một transaction_id có thể xuất hiện **nhiều lần** nếu chạy model khác nhau
- Mỗi dòng = 1 transaction + 1 model_version
- Grain phụ thuộc: `(transaction_id, model_version)`

#### Ví dụ:
```sql
-- Query kiểm tra grain
SELECT transaction_id, model_version, COUNT(*) as cnt
FROM marts.fact_fraud_prediction
GROUP BY transaction_id, model_version
HAVING COUNT(*) > 1;
-- Kết quả: 0 rows
```

---

## 2. GRAIN CHECK VERIFICATION

### fact_transaction:
| Check | Expected | Test Query |
|-------|----------|------------|
| Total rows | 590,540 | `SELECT COUNT(*) FROM fact_transaction` |
| Unique transaction_id | 590,540 | `SELECT COUNT(DISTINCT transaction_id) FROM fact_transaction` |
| Duplicates | 0 | GROUP BY + HAVING COUNT > 1 = 0 rows |

### fact_fraud_prediction:
| Check | Expected | Test Query |
|-------|----------|------------|
| Total rows | 590,540 | `SELECT COUNT(*) FROM fact_fraud_prediction` |
| Unique (transaction_id, model_version) | 590,540 | COUNT(DISTINCT composite key) |

---

## 3. GRAIN SUMMARY TABLE

| Table | Grain | Primary Key | Row Count (expected) |
|-------|-------|-------------|---------------------|
| `fact_transaction` | One row per transaction | transaction_key (SK) | 590,540 |
| `fact_fraud_prediction` | One row per (transaction, model) | prediction_key (SK) | 590,540 |
| `dim_date` | One row per day | date_key (YYYYMMDD) | ~30 (30 ngày data) |
| `dim_product` | One row per product code | product_key (SK) | 5 (W, H, C, S, R) |
| `dim_card` | One row per unique card combo | card_key (SK) | Variable |
| `dim_device` | One row per unique device | device_key (SK) | Variable |
| `dim_email` | One row per email domain pair | email_key (SK) | Variable |

---

## 4. CHANGE LOG

| Date | Change |
|------|--------|
| 02/09/2026 | Created grain definition |

*Cập nhật: 02/09/2026 | Version: 1.0*
