# EDA FINDINGS & INSIGHTS

**Dự án:** Ecommerce Fraud Detection Data Warehouse  
**Phase:** 05 — Data Profiling & EDA  
**Ngày tạo:** 02/09/2026

---

## 1. PHÁT HIỆN CHÍNH NGHỆP VỤ (KEY BUSINESS FINDINGS)

1. **Rủi ro cao ở nhóm sản phẩm C (Code C):**
   - Mã sản phẩm `C` có tỷ lệ gian lận lên tới **11.69%**, gấp gần 6 lần so với mã `W` (2.04%).
   - *Chiến lược:* Cần chú ý đặc biệt các tính năng liên quan đến `ProductCD = C` trong quá trình Feature Engineering.

2. **Giao dịch thiết bị di động (Mobile Devices) có nguy cơ gian lận cao hơn:**
   - Người dùng thực hiện giao dịch trên thiết bị `mobile` có tỷ lệ gian lận **10.17%** so với `desktop` (**6.52%**).
   - *Chiến lược:* Giữ lại thuộc tính `DeviceType` và `DeviceInfo` trong Data Warehouse và ML Features.

3. **Hiện tượng lệch về thông tin định danh (Identity Coverage Sparsity):**
   - 76.16% số giao dịch không có bản ghi `identity` tương ứng.
   - *Chiến lược:* Dùng `LEFT JOIN` khi kết nối `train_transaction` và `train_identity` trong Data Warehouse, xử lý giá trị khuyết `NaN` như một danh mục riêng (`Unknown`).

---

## 2. QUYẾT ĐỊNH KỸ THUẬT CHO DATA WAREHOUSE & MACHINE LEARNING

1. **Thiết kế Dimension Table:**
   - Dựng `dim_product` (chứa ProductCD).
   - Dựng `dim_device` (chứa DeviceType, DeviceInfo).
   - Dựng `dim_card` (chứa card1-card6, card4 provider).
   - Dựng `fact_transaction` chứa các giá trị đo lường (`TransactionAmt`, `TransactionDT`) và tham chiếu khóa ngoại.

2. **Chiến lược huấn luyện ML:**
   - Sử dụng kỹ thuật xử lý dữ liệu mất cân bằng: `class_weight='balanced'` hoặc `SMOTE`.
   - Đánh giá bằng **PR-AUC** và **F1-Score**.
