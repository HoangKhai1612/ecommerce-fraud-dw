# DATASET SOURCE

**Nguồn:** IEEE-CIS Fraud Detection  
**Verify date:** 02/09/2026  
**Status:** ✅ ĐÃ CÓ TRONG `data/raw/`

---

## 1. NGUỒN DỮ LIỆU

| Thông tin | Giá trị |
|----------|---------|
| Tên dataset | IEEE-CIS Fraud Detection |
| Nền tảng | Kaggle (https://www.kaggle.com/datasets) |
| Competition | IEEE-CIS Fraud Detection (2019) |
| Nhà cung cấp | IEEE Computational Intelligence Society & Vesta Corporation |
| License | CC0 1.0 Universal (Public Domain) |

---

## 2. MÔ TẢ DATASET

Bộ dữ liệu IEEE-CIS Fraud Detection được sử dụng để đánh giá khả năng phát hiện gian lận trong giao dịch thanh toán điện tử của Vesta (một nền tảm thanh toán điện tử lớn tại châu Á). Bộ dữ liệu này mô phỏng môi trường thực tế của các hệ thống phát hiện gian lận thẻ tín dụng.

### Cấu trúc:
- **`train_transaction.csv`**: Thông tin giao dịch (590,540 bản ghi, 394 cột)
- **`train_identity.csv`**: Thông tin định danh khách hàng (144,233 bản ghi, 41 cột)
- **`test_transaction.csv`**: Dữ liệu test (506,691 bản ghi, 393 cột — không có `isFraud`)
- **`test_identity.csv`**: Identity test (khoảng 146,133 bản ghi, 41 cột)
- **`sample_submission.csv`**: Mẫu submission (TransactionID + isFraud)

---

## 3. CÁCH LIÊN KẾT

Hai bảng được liên kết thông qua cột `TransactionID`:

```sql
-- train_transaction.TransactionID = train_identity.TransactionID
SELECT t.TransactionID, t.isFraud, i.DeviceType
FROM train_transaction t
LEFT JOIN train_identity i ON t.TransactionID = i.TransactionID
LIMIT 5;
```

---

## 4. ĐIỀU KHOẢN SỬ DỤNG

- **License**: CC0 1.0 — có thể sử dụng cho nghiên cứu và thương mại mà không cần trích dẫn
- **Mục đích sử dụng trong đồ án**: Nghiên cứu học thuật, xây dựng hệ thống phát hiện gian lận
- **Không chứa dữ liệu cá nhân thực sự**: Tất cả đã được xử lý ẩn danh (anonymized)

---

## 5. TẢI Ở ĐÂU

- **Kaggle**: https://www.kaggle.com/competitions/ieee-fraud-detection/data
- Yêu cầu đăng ký Kaggle tài khoản miễn phí
- Nhấn "Download" để tải file ZIP

> **Lưu ý**: Dataset đã có sẵn trong `data/raw/` — không cần tải lại.

---

## 6. TÀI LIỆU THAM KHẢO

- Kaggle competition page: https://www.kaggle.com/competitions/ieee-fraud-detection
- IEEE-CIS Fraud Detection Dataset documentation
- Vesta Corporation transaction data (anonymized)

*Cập nhật: 02/09/2026 | Version: 1.0*
