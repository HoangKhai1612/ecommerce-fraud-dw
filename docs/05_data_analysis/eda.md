# EDA — EXPLORATORY DATA ANALYSIS

**Dự án:** Ecommerce Fraud Detection Data Warehouse  
**Phase:** 05 — Data Profiling & EDA  
**Ngày thực hiện:** 02/09/2026  

---

## 1. MỤC TIÊU

Khám phá dữ liệu IEEE-CIS để:
- Hiểu phân phối giao dịch và fraud
- Xác định missing values và anomalies
- Tìm features tiềm năng cho ML
- Xác định data quality issues

---

## 2. THỐNG KÊ TỔNG QUAN

| Thống kê | Transaction (10K sample) | Identity (10K sample) |
|----------|-------------------------|----------------------|
| Số bản ghi | 10,000 | 10,000 |
| Số cột | 394 | 41 |
| Dtypes | 376 float, 14 str, 4 int | Mixed (float, string) |

### Full dataset:
| File | Rows | Columns |
|------|------|---------|
| train_transaction.csv | 590,540 | 394 |
| train_identity.csv | 144,233 | 41 |

---

## 3. TARGET VARIABLE: isFraud

| Label | Count | Ratio |
|-------|-------|-------|
| 0 (Non-Fraud) | 569,877 | 96.50% |
| 1 (Fraud) | 20,663 | 3.50% |

> **Extreme imbalance**: 1:27.6 — dùng F1/PR-AUC thay vì Accuracy.

---

## 4. PHÂN PHỐI THEO PRODUCTCD

| ProductCD | Total | Fraud | Fraud Rate | Ghi chú |
|-----------|-------|-------|------------|---------|
| C | 68,519 | 8,008 | **11.69%** ⚠️ | Cao nhất |
| S | 11,628 | 686 | 5.90% | Trung bình |
| H | 33,024 | 1,574 | 4.77% | Trung bình |
| R | 37,699 | 1,426 | 3.78% | Thấp |
| W | 439,670 | 8,969 | 2.04% | Thấp nhất |

> **Insight:** ProductCD = C có fraud rate gấp ~6x ProductCD = W.

---

## 5. PHÂN PHỐI THEO DEVICETYPE

| DeviceType | Total | Fraud | Fraud Rate |
|------------|-------|-------|------------|
| Unknown (no identity) | ~449,730 | ~9,452 | **2.10%** |
| desktop | 85,165 | 5,554 | **6.52%** |
| mobile | 55,645 | 5,657 | **10.17%** ⚠️ |

> **Insight:** Mobile có fraud rate cao hơn desktop. Transactions không có identity (76% tổng số) có fraud rate thấp.

---

## 6. TRANSACTION AMOUNT ANALYSIS

| Thống kê | Giá trị |
|----------|---------|
| Count | 590,540 |
| Mean | $142.75 |
| Std | $215.45 |
| Min | $1.896 |
| 25% | $44.00 |
| 50% (Median) | $75.00 |
| 75% | $120.00 |
| Max | $3,247.91 |

### Outliers (IQR method):
- Upper threshold: $237.00
- Số outlier: ~11% tổng số giao dịch

### Fraud rate theo amount bins:
- Giao dịch $<483: 2.69% fraud rate
- Giao dịch $483-966: 3.87% fraud rate
- Giao dịch cao: 0-4% (ít hơn do số lượng nhỏ)

---

## 7. EMAIL DOMAIN ANALYSIS

Top email domains (P_emaildomain):
1. gmail.com: 17,909 (36.6%)
2. yahoo.com: 8,360 (17.1%)
3. hotmail.com: 3,728 (7.6%)
4. anonymous.com: 3,466 (7.1%)
5. aol.com: 2,443 (5.0%)

> **Insight:** Các email anonymous.com hoặc không xác định có thể là dấu hiệu gian lận.

---

## 8. CARD ANALYSIS

### card4 (Visa/Mastercard/etc):
| card4 | Count |
|-------|-------|
| visa | 32,561 |
| mastercard | 15,696 |
| american express | 1,083 |
| discover | 654 |
| NaN | ~306 |

### card6 (Debit/Credit):
| card6 | Count |
|-------|-------|
| debit | 34,205 |
| credit | 15,786 |
| debit or credit | 3 |
| charge card | 3 |

---

## 9. FEATURE CORRELATION VỚI isFraud

Top 10 features có correlation cao nhất:
| Feature | Correlation |
|---------|-------------|
| V201 | 0.336 |
| V189 | 0.300 |
| V200 | 0.292 |
| V198 | 0.264 |
| V156 | 0.262 |
| V257 | 0.258 |
| V158 | 0.248 |
| V188 | 0.247 |
| V155 | 0.246 |
| V45 | 0.243 |

> **Insight:** Các Vesta features (V201, V189, V200...) có correlation mạnh với fraud. Đây là đặc trưng quan trọng.

---

## 10. KEY FINDINGS

1. **Severe imbalance**: Chỉ 3.5% là fraud → không dùng Accuracy, dùng PR-AUC, F1
2. **ProductCD=C**: Tỷ lệ fraud 11.69% — đặc trưng quan trọng
3. **Mobile device**: Tỷ lệ fraud 10.17% > desktop 6.52%
4. **V features**: V201, V189, V200 có correlation cao nhất với fraud
5. **Missing data**: 84% V columns, 93% D columns có missing → cần imputation strategy
6. **Identity sparsity**: 76% transactions không có identity data → dùng LEFT JOIN

*Cập nhật: 02/09/2026 | Version: 1.0*
