# RAW LAYER

**Dự án:** Ecommerce Fraud Detection Data Warehouse  
**Phase:** 10 — RAW Layer  
**Ngày thực hiện:** 02/09/2026  
**Status:** ✅ PASSED

---

## 1. MỤC TIÊU

Xây dựng và xác minh RAW layer — lớp dữ liệu nguồn được nạp trực tiếp từ CSV mà **không có bất kỳ biến đổi nà**.

Nguyên tắc:
- Phản ánh dữ liệu nguồn gần nhất có thể
- Không xử lý nghiệp vụ (cleaning, transformation, type casting)
- Giữ nguyên schema gốc 100%
- Ghi thêm metadata nếu cần (sẽ làm ở staging)

---

## 2. SCHEMA STRUCTURE

```sql
-- RAW schema contains 2 tables
schema: raw
├── raw.transactions  (590,540 rows × 394 columns)
└── raw.identity      (144,233 rows × 41 columns)
```

---

## 3. TABLE SPECIFICATIONS

### `raw.transactions`

| Thuộc tính | Giá trị |
|-----------|---------|
| **Source** | `data/raw/train_transaction.csv` |
| **Row count** | 590,540 |
| **Column count** | 394 |
| **Data types** | TEXT (tất cả — giữ nguyên format gốc CSV) |
| **Primary key** | TransactionID (natural, not enforced as PK constraint at RAW level) |
| **Encoding** | UTF-8 |
| **Schema** | raw |

#### Column naming convention:
- Tên cột giống hệt CSV gốc (có dấu cách, đặc biệt được quote)
- Ví dụ: `"TransactionID"`, `"isFraud"`, `"V1"`, `"V339"`, `"M1"`...

### `raw.identity`

| Thuộng tính | Giá trị |
|------------|---------|
| **Source** | `data/raw/train_identity.csv` |
| **Row count** | 144,233 |
| **Column count** | 41 |
| **Data types** | TEXT |
| **Join key** | TransactionID (FK tới raw.transactions) |

---

## 4. RAW LAYER TESTS

### 4.1. Row Count Verification

| Table | CSV rows | DB rows | Match? |
|-------|----------|---------|--------|
| raw.transactions | 590,540 | 590,540 | ✅ |
| raw.identity | 144,233 | 144,233 | ✅ |

### 4.2. Schema Verification

| Table | CSV columns | DB columns | Match? |
|-------|-------------|------------|--------|
| raw.transactions | 394 | 394 | ✅ |
| raw.identity | 41 | 41 | ✅ |

### 4.3. Data Integrity

| Check | Result |
|-------|--------|
| Null TransactionID in raw.transactions | 0 ✅ |
| Duplicate TransactionID in raw.transactions | 0 ✅ |
| Data types (all TEXT) | ✅ |
| Encoding (UTF-8) | ✅ |

---

## 5. DATA SAMPLE

### raw.transactions (first 5 rows):

| TransactionID | isFraud | TransactionDT | TransactionAmt | ProductCD |
|--------------|---------|---------------|----------------|-----------|
| 2987000 | 0 | 86400 | 68.5 | W |
| 2987001 | 0 | 86401 | 29.0 | W |
| 2987002 | 0 | 86469 | 59.0 | W |
| 2987003 | 0 | 86499 | 34.03 | W |
| 2987004 | 0 | 86506 | 59.0 | W |

### raw.identity (first 5 rows):

| TransactionID | id_01 | id_02 | DeviceType | DeviceInfo |
|--------------|-------|-------|------------|------------|
| 2987000 | 0.0 | 1849.0 | mobile | SAMSUNG SM-G892A... |
| 2987001 | 0.0 | 4123.0 | desktop | Windows |
| 2987002 | 0.0 | 1537.0 | desktop | Windows |
| 2987003 | 0.0 | 5165.0 | mobile | iOS Device |
| 2987004 | 0.0 | 5925.0 | desktop | Windows |

---

## 6. JOIN RELATIONSHIP

```sql
-- 23.84% transactions có identity data
SELECT 
    COUNT(t."TransactionID") as total_transactions,
    COUNT(i."TransactionID") as transactions_with_identity,
    ROUND(COUNT(i."TransactionID")::DECIMAL / COUNT(t."TransactionID")::DECIMAL * 100, 2) as identity_pct
FROM raw."transactions" t
LEFT JOIN raw."identity" i ON t."TransactionID" = i."TransactionID";
```

**Result:**
- Total transactions: 590540
- Transactions with identity: 144233
- Identity coverage: 24.42

---

## 7. FRAUD DISTRIBUTION IN RAW

```sql
SELECT 
    "isFraud",
    COUNT(*) as count,
    ROUND(COUNT(*)::DECIMAL / (SELECT COUNT(*) FROM raw."transactions") * 100, 2) as pct
FROM raw."transactions"
GROUP BY "isFraud"
ORDER BY "isFraud";
```

| isFraud | Count | Ratio |
|---------|-------|-------|
| 0 (Non-Fraud) | 569,877 | 96.50% |
| 1 (Fraud) | 20,663 | 3.50% |

---

## 8. RAW LAYER DO'S AND DON'TS

### ✅ DO:
- Giữ nguyên mọi giá trị như CSV (kể cả NaN, empty string)
- Sử dụng TEXT type cho tất cả columns
- Tạo schema `raw` riêng biệt
- Chỉ có 1 lệnh: load CSV vào table
- Log số lượng rows loaded

### ❌ DON'T:
- Đổi tên cột
- Ép kiểu dữ liệu (casting)
- Xử lý missing values
- Loại bỏ duplicate
- Thêm bất kỳ logic nào

---

## 9. SUCCESS CRITERIA

```text
[✅] Schema 'raw' tồn tại
[✅] Table 'raw.transactions' tồn tại (590,540 rows, 394 cols)
[✅] Table 'raw.identity' tồn tại (144,233 rows, 41 cols)
[✅] Row count khớp CSV 100%
[✅] Column count khớp CSV
[✅] TransactionID không null
[✅] TransactionID không duplicate
[✅] Tất cả columns đều TEXT type (RAW không transform types)
[✅] Có logging
[✅] Tests PASS (12/12)
```

---

## 10. EVIDENCE

- Terminal output: `python ingestion/load_raw.py` → 10.78s, all row counts verified
- SQL queries: `SELECT COUNT(*)` từ raw.transactions và raw.identity
- Test results: `pytest tests/test_ingestion.py -v` → 12 passed
- Schema dump: `SELECT column_name, data_type FROM information_schema.columns`

*Xem thêm: `evidence/phase_09/` và `evidence/phase_10/`*

*Cập nhật: 02/09/2026 | Version: 1.0*
