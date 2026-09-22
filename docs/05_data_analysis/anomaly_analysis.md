# ANOMALY ANALYSIS

**Dự án:** Ecommerce Fraud Detection Data Warehouse  
**Phase:** 05 — Data Profiling & EDA  
**Ngày thực hiện:** 02/09/2026  

---

## 1. LOẠI ANOMALY TRONG DATASET

### 1.1. TransactionAmt Anomalies

| Thống kê | Giá trị |
|----------|---------|
| Min | $1.896 |
| Max | $3,247.91 (trên 50K sample: $4,829.95) |
| Mean | ~$142 |
| Median | ~$75 |
| IQR upper bound | $237.00 |
| Outliers (IQR) | ~11% tổng số giao dịch |

**Phân tích:**
- Giao dịch giá trị rất thấp (<$5) thường gặp — card testing behavior
- Giao dịch giá trị rất cao (> $1000) — potential fraud pattern
- 11% outliers — nên kiểm tra correlation với fraud

### 1.2. TransactionDT Anomalies
- TransactionDT là số giây từ reference point (00:00:00 UTC, September 28, 2017)
- Giá trị max ~2,437,078 (giây) = ~28.2 ngày
- **Insight**: Dữ liệu được thu thập trong 30 ngày

---

## 2. DEVICE INFO ANOMALIES

### DeviceType:
| Type | Count (10K) |
|------|-------------|
| desktop | 3,234 |
| mobile | 1,633 |
| Unknown | ~5,133 |

### DeviceInfo:
- Nhiều giá trị unique (>100) — browser/OS combinations
- Một số giá trị lỗi: "SAMSUNG", "samsung", "Samsung" — cần chuẩn hóa
- Thiết bị không xác định (missing DeviceInfo) thường có fraud rate thấp hơn

---

## 3. EMAIL DOMAIN ANOMALIES

### Anomalous domains:
| Domain | Count | Notes |
|--------|-------|-------|
| gmail.com | 17,909 | Normal |
| yahoo.com | 8,360 | Normal |
| hotmail.com | 3,728 | Normal |
| anonymous.com | 3,466 | ⚠️ Suspicious |
| aol.com | 2,443 | Normal |

- `anonymous.com`: Không phải email thực — dấu hiệu fraud tiềm năng
- Các domain không xác định (missing): ~30% tổng số

---

## 4. CARD ANOMALIES

### card4:
| card4 | Count | Notes |
|-------|-------|-------|
| visa | 32,561 | Normal |
| mastercard | 15,696 | Normal |
| american express | 1,083 | High-value cards |
| discover | 654 | Low volume |

### card6:
- "debit or credit" (3 records) — dữ liệu lỗi, cần chuẩn hóa
- "charge card" (3 records) — hiếm, giữ nguyên

---

## 5. FEATURE ANOMALIES (V columns)

- V201, V189, V200 có correlation cao nhất với isFraud (>0.29)
- Nhiều V columns có missing >85% — cần drop hoặc impute
- V columns có giá trị ngoại lệ: một số V có giá trị âm (-1, -2...) — là sentinel values cho missing

---

## 6. DEVICE + FRAUD PATTERN

| DeviceType | Identity Available | Fraud Rate |
|------------|-------------------|------------|
| Unknown (no identity) | No | 2.05% |
| desktop | Yes | 3.14% |
| mobile | Yes | 6.16% ⚠️ |

> **Anomaly:** Mobile fraud rate ca gấp ~3x so với non-mobile transactions.

---

## 7. TIME-BASED ANOMALIES

- TransactionDT được đo bằng giây từ 28/09/2017
- Cần convert sang ngày/giờ để phân tích xu hướng thời gian
- Một số TransactionDT bị missing (0.1%) — cần forward-fill hoặc drop

---

## 8. HANDLING STRATEGY

| Anomaly Type | Strategy |
|-------------|----------|
| TransactionAmt outliers | Keep (có thể là fraud signals); log-transform nếu dùng trong ML |
| DeviceInfo normalization | Chuẩn hóa case (SAMSUNG → samsung) |
| Email domain missing | Fill "Unknown" |
| V columns sentinel (-1, -2) | Replace bằng NaN, sau đó impute |
| Card anomalies | Fill mode hoặc "Unknown" |
| M columns missing | Fill "Unknown" (T/F) |

---

## 9. EDA CHECKLIST

- [x] TransactionAmt distribution analyzed
- [x] ProductCD fraud rates calculated
- [x] DeviceType fraud rates calculated
- [x] Email domain top values identified
- [x] Card4/card6 distributions analyzed
- [x] Missing data patterns identified
- [x] Top correlated features with fraud found
- [x] Identity sparsity quantified (~76%)

*Cập nhật: 02/09/2026 | Version: 1.0*
