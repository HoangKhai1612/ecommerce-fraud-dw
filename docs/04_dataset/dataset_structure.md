# DATASET STRUCTURE

**Nguồn:** IEEE-CIS Fraud Detection (Kaggle)  
**Verify date:** 02/09/2026  
**Status:** ✅ ĐỌC ĐƯỢC — Không có lỗi encoding

---

## 1. FILES OVERVIEW

| File | Size | Rows | Columns | Mô tả |
|------|------|------|---------|-------|
| `train_transaction.csv` | 652.3 MB | 590,540 | 394 | Dữ liệu giao dịch train |
| `train_identity.csv` | 25.4 MB | ~144,233 | 41 | Thông tin định danh train |
| `test_transaction.csv` | 585.3 MB | ~506,691 | 393 | Dữ liệu giao dịch test (không có isFraud) |
| `test_identity.csv` | 24.7 MB | — | 41 | Thông tin định danh test |
| `sample_submission.csv` | 6.3 MB | — | 2 | TransactionID + isFraud (0/1) |

> **Lưu ý:** test_* không có cột `isFraud` — chỉ dùng train_* cho toàn bộ dự án.

---

## 2. train_transaction.csv — COLUMNS (394 columns)

### Key Columns
| Column | Type | Mô tả |
|--------|------|-------|
| `TransactionID` | int64 | Primary key — join với identity |
| `isFraud` | int64 | **Target variable**: 0=Non-Fraud, 1=Fraud |
| `TransactionDT` | int64 | Timedelta (giây) từ reference point |
| `TransactionAmt` | float64 | Giá trị giao dịch (USD) |
| `ProductCD` | string | Mã sản phẩm: W, H, C, S, R |
| `card1`–`card6` | numeric/string | Thông tin thẻ tín dụng (đã ẩn) |
| `addr1`, `addr2` | numeric | Mã vùng billing address |
| `dist1`, `dist2` | float | Khoảng cách địa lý |
| `P_emaildomain` | string | Email domain người mua |
| `R_emaildomain` | string | Email domain người nhận |
| `C1`–`C14` | numeric | Counting features (đã ẩn danh) |
| `D1`–`D15` | numeric | Timedelta features |
| `M1`–`M9` | string | Match features (T/F/Unknown) |
| `V1`–`V339` | numeric | Vesta engineered features (ẩn danh) |

### Column Groups
```
Transaction info:  TransactionID, isFraud, TransactionDT, TransactionAmt, ProductCD
Card info:         card1, card2, card3, card4, card5, card6
Address:           addr1, addr2, dist1, dist2
Email:             P_emaildomain, R_emaildomain
Counting:          C1-C14
Timedelta:         D1-D15
Match:             M1-M9
Vesta features:    V1-V339 (339 columns!)
```

---

## 3. train_identity.csv — COLUMNS (41 columns)

| Column | Type | Mô tả |
|--------|------|-------|
| `TransactionID` | int64 | Foreign key → train_transaction |
| `id_01`–`id_11` | float | Numeric identity features |
| `id_12`–`id_38` | string/float | Mixed identity features |
| `DeviceType` | string | mobile / desktop |
| `DeviceInfo` | string | Device info string |

> **Quan trọng:** Không phải tất cả giao dịch đều có identity data.  
> train_transaction: 590,540 rows  
> train_identity: ~144,233 rows (chỉ ~24% có identity data)

---

## 4. JOIN RELATIONSHIP

```sql
-- Left join: giữ tất cả transactions, identity có thể null
SELECT t.*, i.*
FROM train_transaction t
LEFT JOIN train_identity i ON t.TransactionID = i.TransactionID
```

---

## 5. TARGET VARIABLE DISTRIBUTION (Ước tính)

> Dựa trên đặc điểm nổi tiếng của dataset này:

| isFraud | Approximate Count | Ratio |
|---------|------------------|-------|
| 0 (Non-Fraud) | ~556,000 | ~94.2% |
| 1 (Fraud) | ~34,000 | ~5.8% |

→ **Imbalanced dataset** → Không dùng Accuracy làm metric chính!

---

## 6. POTENTIAL ISSUES

| Issue | Mô tả | Xử lý |
|-------|-------|-------|
| Missing values | V1-V339 có rất nhiều NaN | Imputation / drop |
| Ẩn danh features | V columns không có tên thật | Feature engineering |
| Large size | 652 MB RAM consumption | Read chunks hoặc sample |
| Identity không đủ | 76% transactions không có identity | LEFT JOIN |
| TransactionDT | Không phải timestamp thật | Feature engineering |

---

*Verify: 02/09/2026 | Status: ✅ READABLE*
