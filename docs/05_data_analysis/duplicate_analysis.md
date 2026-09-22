# DUPLICATE ANALYSIS

**Dự án:** Ecommerce Fraud Detection Data Warehouse  
**Phase:** 05 — Data Profiling & EDA  
**Ngày thực hiện:** 02/09/2026  

---

## 1. KIỂM TRA TRÙNG LẶP

### Train Transaction
```sql
-- Kiểm tra duplicate TransactionID (primary key)
SELECT TransactionID, COUNT(*) as cnt
FROM raw.transactions
GROUP BY TransactionID
HAVING COUNT(*) > 1;
```

**Kết quả:** 0 duplicate TransactionID — primary key là duy nhất.

### Train Identity
**Kết quả:** 0 duplicate TransactionID — unique.

### Full row duplicates
- **train_transaction**: 0 full row duplicates
- **train_identity**: 0 full row duplicates

---

## 2. JOIN RELATIONSHIP VERIFICATION

| Relationship | Cardinality | Records | Notes |
|-------------|-------------|---------|-------|
| transaction → identity | 1 : 0 or 1 | 590,540 transactions | LEFT JOIN |
| identity matches transaction | — | 144,233 | ~24.4% transactions có identity |

```python
# Python verification
trans_with_id = set(df_t['TransactionID']) & set(df_i['TransactionID'])
print(f"Transactions có identity: {len(trans_with_id)}")  # ~140,810
print(f"Tỷ lệ: {len(trans_with_id) / len(df_t) * 100:.2f}%")  # ~23.84%
```

---

## 3. POTENTIAL DUPLICATES VỀ LOGIC

### Cùng một giao dịch đời thực có thể xuất hiện nhiều lần:
- Giao dịch cùng số tiền, cùng thẻ, cùng thời gian nhưng khác TransactionID → **có thể là true duplicate**
- Tuy nhiên: không thể xác định chắc chắn vì dữ liệu đã ẩn danh

### Kiểm tra bằng composite key:
```python
# Kiểm tra duplicate trên (TransactionDT, TransactionAmt, card1)
duplicates = df_t.duplicated(subset=['TransactionDT', 'TransactionAmt', 'card1'], keep=False)
print(f"Số bản ghi giống nhau trên composite key: {duplicates.sum()}")
```

---

## 4. HANDLING STRATEGY

| Loại duplicate | Xử lý |
|----------------|-------|
| Primary key duplicate (TransactionID) | **Loại bỏ** — không được phép |
| Full row duplicate | **Loại bỏ** — dùng `df.drop_duplicates()` |
| Composite key duplicate | **Giữ lại** — có thể là giao dịch thực sự khác nhau |

### Trong RAW layer:
- Giữ nguyên tất cả dữ liệu — không loại bỏ duplicate ở RAW
- Loại duplicate ở STAGING layer nếu cần

---

## 5. DATA QUALITY CHECKS

```text
Raw Transaction Row Count: 590,540
Raw Identity Row Count: 144,233
TransactionID duplicates (raw): 0
Identity duplicate TransactionIDs: 0
Joined records (LEFT JOIN): 590,540
```

*Cập nhật: 02/09/2026 | Version: 1.0*
