# DATASET DICTIONARY

**Nguồn:** IEEE-CIS Fraud Detection  
**Ngày tạo:** 02/09/2026  
**Status:** ✅ Đã xác minh cột (394 transaction + 41 identity)

---

## 1. train_transaction.csv — COLUMNS (394)

### Nhóm 1: Transaction Info (5 cột)

| Column | Type | Mô tả |
|--------|------|-------|
| `TransactionID` | int64 | **Primary Key** — ID duy nhất cho mỗi giao dịch |
| `isFraud` | int64 | **Target variable**: 0 = Non-Fraud, 1 = Fraud |
| `TransactionDT` | int64 | Thời gian giao dịch (giây kể từ 00:00 28/09/2017) |
| `TransactionAmt` | float64 | Số tiền giao dịch (USD) |
| `ProductCD` | string | Mã sản phẩm: W (web), H (host), C (connect), S (subscription), R (re-authorization) |

### Nhóm 2: Card Info (6 cột)

| Column | Type | Mô tả |
|--------|------|-------|
| `card1` | int64 | Loại thẻ (1-6 tương ứng với các loại thẻ khác nhau) |
| `card2` | float64 | Thương hiệu thẻ (Visa, Mastercard...) |
| `card3` | float64 | Country code của thẻ |
| `card4` | string | Loại thẻ (debit/credit) |
| `card5` | float64 | Loại thẻ |
| `card6` | string | Loại tài khoản (debit/credit) |

### Nhóm 3: Address (4 cột)

| Column | Type | Mô tả |
|--------|------|-------|
| `addr1` | float64 | Mã vùng 1 (billing address region) |
| `addr2` | float64 | Mã vùng 2 (billing address postal code) |
| `dist1` | float64 | Khoảng cách địa lý giữa billing và shipping |
| `dist2` | float64 | Khoảng cách địa lý khác |

### Nhóm 4: Email (2 cột)

| Column | Type | Mô tả |
|--------|------|-------|
| `P_emaildomain` | string | Tên miền email người mua (P = Payment) |
| `R_emaildomain` | string | Tên miền email người nhận (R = Recipient) |

### Nhóm 5: Counting Features (14 cột)

| Column | Type | Mô tả |
|--------|------|-------|
| `C1`–`C14` | float64 | Các đặc trưng đếm số lần xuất hiện của các thuộc tính khác nhau trong 1 tuần trước |

### Nhóm 6: Timedelta Features (15 cột)

| Column | Type | Mô tả |
|--------|------|-------|
| `D1`–`D15` | float64 | Các đặc trưng thời gian (ngày từ lần giao dịch trước, tuần, tháng...) |

### Nhóm 7: Match Features (9 cột)

| Column | Type | Mô tả |
|--------|------|-------|
| `M1`–`M9` | string | Các đặc trưng trùng khớp (T, F, hoặc NaN) |

### Nhóm 8: Vesta Engineered Features (339 cột)

| Column | Type | Mô tả |
|--------|------|-------|
| `V1`–`V339` | float64 | Các đặc trưng được Vesta engine tạo ra (đã ẩn danh). Chứa thông tin về thiết bị, địa chỉ, hành vi người dùng... |

> **Lưu ý:** Các cột V1-V339 đã được ẩn danh — không biết chính xác là đặc trưng gì. Đây là các đặc trưng được sinh từ PCA hoặc feature engineering của Vesta.

---

## 2. train_identity.csv — COLUMNS (41)

### Nhóm 1: ID Features (41 cột)

| Column | Type | Mô tả |
|--------|------|-------|
| `TransactionID` | int64 | **Foreign Key** — kết nối với train_transaction |
| `id_01`–`id_11` | float64 | Các đặc trưng số (thời gian, device match scores...) |
| `id_12`–`id_38` | string/float | Các đặc trưng hỗn hợp (DeviceType, DeviceInfo, browser info...) |
| `DeviceType` | string | Loại thiết bị: `desktop` / `mobile` |
| `DeviceInfo` | string | Thông tin thiết bị (browser, OS, model...) |

### Chi tiết id_01–id_38:

| Column | Type | Mô tả |
|--------|------|-------|
| `id_01` | float | Idle duration (giây) |
| `id_02` | float | Thời gian chờ tương đối |
| `id_03`, `id_04` | float | Thông tin độ trễ (latency) |
| `id_05`, `id_06` | float | Số lần scroll |
| `id_07`, `id_08` | float | Thời gian hoạt động |
| `id_09`, `id_10` | float | Thời gian không hoạt động |
| `id_11` | float | Thời gian session |
| `id_12`–`id_15` | string | Thông tin browser, OS, màn hình |
| `id_16`–`id_21` | float/string | Các đặc trưng device khác |
| `id_22`–`id_28` | float | Thông tin độ phân giải màn hình |
| `id_29` | string | Có flash hay không |
| `id_30`–`id_38` | string | Thông tin browser, version |
| `DeviceType` | string | `desktop` / `mobile` |
| `DeviceInfo` | string | Tên thiết bị (ví dụ: iOS, Android, Windows...) |

---

## 3. JOIN CHIẾN LƯỢC

```sql
-- LEFT JOIN: giữ tất cả transactions, identity có thể NULL
-- TransactionID là natural key để join
SELECT 
    t.TransactionID,
    t.TransactionAmt,
    t.isFraud,
    i.DeviceType,
    i.DeviceInfo
FROM train_transaction t
LEFT JOIN train_identity i 
    ON t.TransactionID = i.TransactionID
```

---

## 4. COLUMN GROUPING CHO DATA WAREHOUSE

| Data Warehouse Column | Nguồn CSV | Loại |
|----------------------|-----------|------|
| `TransactionID` | train_transaction | Natural Key |
| `isFraud` | train_transaction | Label / Measure |
| `TransactionDT` | train_transaction | Time attribute |
| `TransactionAmt` | train_transaction | Measure |
| `ProductCD` | train_transaction | Dimension |
| `card1`–`card6` | train_transaction | Dimension (card) |
| `addr1`, `addr2`, `dist1`, `dist2` | train_transaction | Dimension (address) |
| `P_emaildomain`, `R_emaildomain` | train_transaction | Dimension (email) |
| `C1`–`C14` | train_transaction | Measures (counting) |
| `D1`–`D15` | train_transaction | Measures (timedelta) |
| `M1`–`M9` | train_transaction | Attributes (match) |
| `V1`–`V339` | train_transaction | Measures (Vesta) |
| `id_01`–`id_38` | train_identity | Measures (identity) |
| `DeviceType` | train_identity | Dimension (device) |
| `DeviceInfo` | train_identity | Dimension (device) |

*Cập nhật: 02/09/2026 | Version: 1.0*
