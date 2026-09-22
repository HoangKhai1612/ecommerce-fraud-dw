# MISSING DATA ANALYSIS

**Dự án:** Ecommerce Fraud Detection Data Warehouse  
**Phase:** 05 — Data Profiling & EDA  
**Ngày thực hiện:** 02/09/2026  

---

## 1. TỔNG QUAN

Tổng cộng **287/394** cột trong `train_transaction.csv` có giá trị thiếu.  
Tất cả **38/41** cột (trừ 3 cột đầu) trong `train_identity.csv` có giá trị thiếu.

---

## 2. MISSING DATA TRONG TRAIN_TRANSACTION

### Phân loại theo mức độ missing:

| Mức độ | Tỷ lệ missing | Số cột | Ví dụ | Chiến lược xử lý |
|--------|---------------|--------|-------|-----------------|
| **Critical (>95%)** | 95-100% | ~100+ | D7, D13, dist2, V156, V157... | Drop hoặc impute = 0 |
| **High (80-95%)** | 80-95% | ~50 | D10, D15, D4, D11, V158... | Impute bằng median hoặc 0 |
| **Medium (20-80%)** | 20-80% | ~30 | addr2, D1, D2, C3, C5... | Impute bằng median |
| **Low (<20%)** | 0-20% | ~20 | card2, card3, card5, dist1, emaildomain... | Impute bằng mode/median |

### Chi tiết nhóm cột:

#### D columns (D1-D15) — 93% records có missing
```
D7      : 9,777/10,000 missing (97.77%)
D13     : 9,720/10,000 missing (97.20%)
D12     : 9,594/10,000 missing (95.94%)
D14     : 9,550/10,000 missing (95.50%)
D6      : 9,509/10,000 missing (95.09%)
D9      : 8,900/10,000 missing (89.00%)
D8      : 8,900/10,000 missing (89.00%)
```

#### V columns (V1-V339) — 84% columns có missing
```
V156    : 8,618/10,000 missing (86.18%)
V157    : 8,618/10,000 missing (86.18%)
V158    : 8,618/10,000 missing (86.18%)
...
```
Trung bình mỗi V column có ~21,632 records missing trên 50,000 sample.

#### M columns (M1-M9) — 100% columns có missing
```
M1-M9   : Toàn bộ 9 cột đều có ~32,957/50,000 missing (66%)
```

#### Email domain — ~30% missing
```
P_emaildomain: ~14,000/50,000 missing
R_emaildomain: ~26,000/50,000 missing
```

---

## 3. MISSING DATA TRONG TRAIN_IDENTITY

### Critical (>95%):
| Column | Missing |
|--------|---------|
| id_24 | 9,668/10,000 (96.68%) |
| id_21 | 9,644/10,000 (96.44%) |
| id_25 | 9,641/10,000 (96.41%) |
| id_08 | 9,641/10,000 (96.41%) |
| id_07 | 9,641/10,000 (96.41%) |
| id_22 | 9,640/10,000 (96.40%) |
| id_26 | 9,640/10,000 (96.40%) |
| id_27 | 9,640/10,000 (96.40%) |
| id_23 | 9,640/10,000 (96.40%) |

### Medium (20-50%):
| Column | Missing |
|--------|---------|
| id_18 | 7,083/10,000 (70.83%) |
| id_20 | ~3,000/10,000 (30%) |
| id_28 | ~2,800/10,000 (28%) |
| id_31 | ~2,500/10,000 (25%) |

---

## 4. CHIẾN LƯỢC XỬ LÝ MISSING DATA

### 4.1. Drop columns (missing > 95%)
- Tất cả V columns có >95% missing
- Tất cả D columns có >95% missing
- Tất cả id columns có >95% missing

```python
# Pseudocode
cols_to_drop = [c for c in df.columns if df[c].isnull().sum() / len(df) > 0.95]
df = df.drop(columns=cols_to_drop)
```

### 4.2. Impute numeric columns (missing 5-95%)
- Impute bằng **median** (robust với outliers)
- Hoặc impute bằng **0** (đối với V columns, 0 có nghĩa là "not present")

### 4.3. Impute categorical columns
- Impute bằng **"Unknown"** (tạo thành một category riêng)
- Đặc biệt: P_emaildomain, R_emaildomain, DeviceInfo, M columns

### 4.4. Special case: Identity missing (76% transactions)
- 76% giao dịch không có identity data
- Khi JOIN: dùng LEFT JOIN, fill null identity features với "Unknown"

---

## 5. IMPACT ON ML

| Issue | Solution |
|-------|----------|
| V columns >95% missing | Drop tính năng, dùng các V còn lại |
| D columns >95% missing | Drop, dùng TransactionDT để tạo features thời gian |
| M columns missing | Fill "Unknown" hoặc impute mode |
| Email domain missing | Fill "unknown.com" |
| id_01-id_38 missing | Fill median (numeric) hoặc "Unknown" (categorical) |
| DeviceType/DeviceInfo missing | Fill "Unknown" |

---

## 6. TESTING CHECKLIST

- [ ] Count total missing per column
- [ ] Percentile of missing distribution
- [ ] Columns with >95% missing → drop list
- [ ] Columns with 5-95% missing → impute strategy
- [ ] Columns with <5% missing → impute median/mode
- [ ] Verify after imputation: 0 missing

*Cập nhật: 02/09/2026 | Version: 1.0*
