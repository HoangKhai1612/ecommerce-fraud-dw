# DATA PROFILING REPORT

**Dự án:** Ecommerce Fraud Detection Data Warehouse  
**Phase:** 05 — Data Profiling & EDA  
**Ngày thực hiện:** 02/09/2026

---

## 1. THỐNG KÊ TỔNG QUAN (DATASET OVERVIEW)

- **Số lượng giao dịch:** 590,540 bản ghi (`train_transaction.csv`).
- **Số lượng thuộc tính giao dịch:** 394 thuộc tính.
- **Số lượng bản ghi định danh (Identity):** 144,233 bản ghi (`train_identity.csv`) ghép khớp được 140,810 giao dịch (chín tỷ lệ 23.84%).

---

## 2. PHÂN TÍCH NHÃN MỤC TIÊU (TARGET VARIABLE - isFraud)

| Nhãn (`isFraud`) | Số lượng bản ghi | Tỷ lệ % | Ý nghĩa |
|-------------------|------------------|---------|---------|
| **0 (Non-Fraud)** | 569,877 | 96.50% | Giao dịch hợp lệ |
| **1 (Fraud)** | 20,663 | 3.50% | Giao dịch gian lận |

> **Kết luận:** Dữ liệu thể hiện sự **mất cân bằng nghiêm trọng (Severe Class Imbalance)** với tỷ lệ 1:27.6. Đánh giá mô hình bắt buộc sử dụng **F1-score**, **Precision-Recall AUC (PR-AUC)** và **ROC-AUC**, không sử dụng Accuracy.

---

## 3. PHÂN TÍCH THEO SẢN PHẨM & THẺ (PRODUCT & CARD BREAKDOWN)

### 3.1. Phân bố theo Mã sản phẩm (`ProductCD`)

| ProductCD | Tổng số giao dịch | Số lượng Fraud | Tỷ lệ Fraud (%) |
|-----------|-------------------|----------------|-----------------|
| **C** | 68,519 | 8,008 | **11.69%** ⚠️ |
| **S** | 11,628 | 686 | **5.90%** |
| **H** | 33,024 | 1,574 | **4.77%** |
| **R** | 37,699 | 1,426 | **3.78%** |
| **W** | 439,670 | 8,969 | **2.04%** |

### 3.2. Phân bố theo Loại thiết bị (`DeviceType`)

| DeviceType | Tổng số giao dịch | Số lượng Fraud | Tỷ lệ Fraud (%) |
|------------|-------------------|----------------|-----------------|
| **mobile** | 55,645 | 5,657 | **10.17%** ⚠️ |
| **desktop** | 85,165 | 5,554 | **6.52%** |
| **NaN (No Identity)** | 449,730 | 9,452 | **2.10%** |
