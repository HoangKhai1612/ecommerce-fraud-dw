# DATASET QUALITY

**Nguồn:** IEEE-CIS Fraud Detection  
**Ngày kiểm tra:** 02/09/2026  
**Status:** CẦN CẢI THIỆN — nhiều missing values và data quality issues

---

## 1. DATASET OVERVIEW

| Thống kê | Train Transaction | Train Identity |
|----------|-------------------|----------------|
| Total rows | 590,540 | 144,233 |
| Total columns | 394 | 41 |
| Columns with missing values | 287 | 38 |
| Duplicate TransactionIDs | 0 | 0 |

---

## 2. TARGET VARIABLE QUALITY

| Label | Count | Ratio |
|-------|-------|-------|
| 0 (Non-Fraud) | 569,877 | 96.50% |
| 1 (Fraud) | 20,663 | 3.50% |

> **Finding:** Severe class imbalance (1:27.6). Không dùng Accuracy để đánh giá model.

---

## 3. MISSING DATA ANALYSIS

### Train Transaction (287/394 columns có missing)

| Severity | Columns with high missing >95% | Số lượng |
|----------|-------------------------------|----------|
| **Critical (>95%)** | D7, D13, dist2, D12, D14, D6, D9, D8, V156, V157, ... | ~100+ columns |
| **High (80-95%)** | D10, D15, D4, D11, D5, V158, V159, ... | ~50+ columns |
| **Medium (20-80%)** | addr2, D1, D2, D3, C3, C5, C6, C7, C8, C9, C10, C12, R_emaildomain | ~30+ columns |
| **Low (<20%)** | card2, card3, card5, dist1, P_emaildomain, M columns | ~20+ columns |

### Train Identity (38/41 columns có missing)

| Severity | Columns | Số lượng |
|----------|---------|----------|
| **Critical (>95%)** | id_24, id_21, id_25, id_08, id_07, id_22, id_26, id_27, id_23 | 9 |
| **High (50-95%)** | id_18, id_28 | 2 |
| **Medium (20-50%)** | id_20, id_29, id_31, id_33, id_34, id_35, id_38 | 7 |
| **Low (<20%)** | id_01, id_02, id_03, id_04, id_05, id_06, id_09, id_10, id_11, id_12, id_13, id_14, id_15, id_16, id_17, id_19, DeviceType, DeviceInfo | ~20 |

### Chiến lược xử lý missing:

| Loại missing | Chiến lược xử lý |
|--------------|-----------------|
| V columns (V1-V339) missing >95% | Drop hoặc impute bằng 0 |
| D columns missing >95% | Impute bằng 0 hoặc median |
| id_24, id_21, id_25... | Impute bằng -999 (outlier marker) |
| Email domain missing | Fill bằng "Unknown" |
| DeviceType/DeviceInfo missing | Fill bằng "Unknown" |
| M columns (M1-M9) missing | Fill bằng "Unknown" |

---

## 4. DUPLICATE ANALYSIS

- **TransactionID**: 0 duplicates — đây là primary key
- **Identity TransactionID**: 0 duplicates — unique
- **Join cardinality**: 1 transaction → 0 or 1 identity (LEFT JOIN)

---

## 5. ANOMALY DETECTION

### TransactionAmt anomalies:
- Min: $1.896
- Max: $3,247.91
- Mean: ~$142
- Median: ~$75
- **Outliers**: Có số lượng giao dịch có giá trị rất lớn (> $1000) — có thể là fraud pattern

### TransactionDT:
- Giá trị là số giây từ reference point (28/09/2017)
- Cần convert thành thời gian thực để phân tích thời gian

### DeviceInfo:
- Nhiều giá trị unique (browser/OS combinations)
- Một số giá trị lỗi (samsung, SAMSUNG, etc.) — cần chuẩn hóa

---

## 6. DATA QUALITY SUMMARY

| Dimension | Quality | Notes |
|-----------|---------|-------|
| Completeness | ⚠️ WEAK | 287/394 transaction columns có missing |
| Validity | ⚠️ WEAK | Nhiều NaN values |
| Uniqueness | ✅ GOOD | TransactionID unique |
| Consistency | ✅ GOOD | Định dạng CSV đồng nhất |
| Accuracy | ✅ OK | Dữ liệu được xác minh với profiling |
| Timeliness | ✅ OK | Dataset tĩnh, single snapshot |

---

## 7. IMPACT TO PIPELINE

| Issue | Ảnh hưởng | Giải pháp |
|-------|-----------|-----------|
| Missing values trong V columns | ML model có thể bị noise | Drop hoặc impute |
| Missing values trong D columns | Mất thông tin thời gian | Impute bằng median |
| Identity missing (76%) | Mất DeviceType, DeviceInfo | LEFT JOIN, fill Unknown |
| Extreme class imbalance | Model thiên về Non-Fraud | SMOTE, class_weight, stratified split |

*Cập nhật: 02/09/2026 | Version: 1.0*
