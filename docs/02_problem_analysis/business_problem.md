# BUSINESS PROBLEM & FRAUD ANALYSIS

**Dự án:** Ecommerce Fraud Detection Data Warehouse  
**Phase:** 02 — Problem Analysis  
**Ngày tạo:** 02/09/2026

---

## 1. BỐI CẢNH NGHỆP VỤ (BUSINESS CONTEXT)

Thương mại điện tử (e-Commerce) phát triển bùng nổ kéo theo sự gia tăng về số lượng và phương thức gian lận thanh toán trực tuyến (Card-Not-Present Fraud).

Các thách thức chính của doanh nghiệp e-Commerce:
1. **Thiệt hại tài chính trực tiếp:** Chargeback fees, bồi hoàn tiền cho chủ thẻ bị lừa.
2. **Tổn hại uy tín:** Khách hàng mất niềm tin khi tài khoản/thẻ bị lừa đảo trên nền tảng.
3. **Trải nghiệm khách hàng:** Nếu kiểm soát quá gắt gao sẽ chặn nhầm giao dịch hợp lệ (False Positive), làm mất khách hàng.

---

## 2. PHÂN TÍCH HÌNH THỨC GIAN LẬN (FRAUD PATTERNS)

Trong bộ dữ liệu IEEE-CIS, các hành vi gian lận thường thể hiện qua:
- **Card Testing / Account Takeover:** Thực hiện nhiều giao dịch giá trị nhỏ liên tiếp để thử thẻ, sau đó giao dịch lớn.
- **Device Anomaly:** Sử dụng emulator, thiết bị lạ, địa chỉ IP proxy/VPN hoặc đổi User-Agent liên tục.
- **Email Domain Discrepancy:** Email người mua (`P_emaildomain`) và email người nhận (`R_emaildomain`) bất thường hoặc thuộc các nhà cung cấp email ảo.
- **Address & Distance Mismatch:** Bất hợp lý giữa khoảng cách địa lý đăng ký thẻ và địa chỉ giao hàng.

---

## 3. THÁCH THỨC ĐẶC THÙ CỦA DỮ LIỆU FRAUD

1. **Cực kỳ mất cân bằng (Extreme Class Imbalance):** Tỷ lệ gian lận thực tế chỉ chiếm ~3.5% - 5.8%. Nếu mô hình dự đoán tất cả là Non-Fraud thì Accuracy vẫn đạt 95%, nhưng hoàn toàn vô dụng.
2. **Missing Data lớn:** Nhiều thuộc tính thiết bị (`identity`) hoặc thông tin ẩn danh (`V1-V339`) bị thiếu do khách hàng không dùng thiết bị hỗ trợ tracking hoặc ẩn thông tin.
3. **Concept Drift:** Phương thức gian lận thay đổi liên tục theo thời gian.

---

## 4. CÂU HỎI PHÂN TÍCH NGHỆP VỤ (ANALYTICAL QUESTIONS)

Hệ thống Data Warehouse & BI Dashboard cần trả lời được các câu hỏi:
- Tỷ lệ gian lận tổng thể và theo thời gian (giờ/ngày/tuần) là bao nhiêu?
- Loại sản phẩm (`ProductCD`) nào có tỷ lệ gian lận cao nhất?
- Tỷ lệ gian lận phân bố như thế nào theo loại thiết bị (`DeviceType`) và hệ điều hành (`DeviceInfo`)?
- Các giao dịch rủi ro cao tập trung ở khoảng giá trị giao dịch (`TransactionAmt`) nào?
- Những đặc trưng (features) nào đóng vai trò quan trọng nhất trong việc phát hiện gian lận?
