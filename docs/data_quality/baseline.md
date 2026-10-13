# Data Quality Baseline

## 1. Mục đích

Tài liệu này ghi nhận trạng thái chất lượng dữ liệu của hệ thống
Data Warehouse tại thời điểm hoàn thành Phase 14.

Các giá trị trong tài liệu được lấy từ dữ liệu thực tế đang được lưu
trong PostgreSQL và kết quả thực thi các truy vấn Data Quality.

---

## 2. Dataset và số lượng bản ghi

| Dataset/Table | Row count |
|---|---:|
| staging.stg_transactions | 590,540 |
| staging.stg_identity | 144,233 |
| marts.fact_transactions | 590,540 |

---

## 3. Transaction Integrity

### 3.1 Transaction ID

| Check | Result |
|---|---:|
| Total transactions | 590,540 |
| Distinct transaction_id | 590,540 |
| NULL transaction_id | 0 |
| Duplicate transaction_id | 0 |
| Orphan transaction | 0 |

Kết quả cho thấy bảng fact hiện tại không xuất hiện transaction_id bị
NULL, trùng lặp hoặc không tồn tại trong staging transaction source.

---

## 4. Fraud Distribution

| is_fraud | Row count |
|---:|---:|
| 0 | 569,877 |
| 1 | 20,663 |
| Total | 590,540 |

Tỷ lệ giao dịch được gắn nhãn fraud:

**3.4990%**

Trong đó:

- Non-fraud: 569,877
- Fraud: 20,663

---

## 5. Transaction Amount

| Metric | Value |
|---|---:|
| Total rows | 590,540 |
| Minimum amount | 0.25 |
| Maximum amount | 31,937.39 |
| Average amount | 135.0272299420869035 |
| Negative amount | 0 |
| Non-positive amount | 0 |

---

## 6. Device Type Completeness

Bảng `staging.stg_identity` có:

| Metric | Value |
|---|---:|
| Total rows | 144,233 |
| Missing device_type | 3,423 |
| Missing percentage | 2.3732% |

Các giá trị device_type có dữ liệu:

| device_type | Row count |
|---|---:|
| desktop | 85,165 |
| mobile | 55,645 |

Ngoài ra có 3,423 bản ghi không có giá trị device_type.

---

## 7. Fact Table Structure

Bảng `marts.fact_transactions` hiện có:

**438 columns**

Cấu trúc bao gồm:

- Transaction information
- Fraud label
- Product information
- Device information
- Card information
- Address information
- Email information
- C-series transaction features
- D-series transaction features
- M-series transaction features
- V-series transaction features
- Identity information
- Device information
- Loading metadata

---

## 8. Data Quality Test Result

Kết quả cuối cùng của `dbt build`:

```text
PASS=44
WARN=0
ERROR=0
SKIP=0
TOTAL=44
Trong đó hệ thống thực hiện:

1 project hook
4 table models
2 view models
38 data quality tests

Tất cả các data quality tests đều PASS.

9. Conclusion

Tại thời điểm hoàn thành Phase 14, dữ liệu trong Data Warehouse
đáp ứng toàn bộ các quy tắc Data Quality đã được định nghĩa.

Không phát hiện:

NULL transaction_id
Duplicate transaction_id
Orphan transaction
Negative transaction amount
Invalid fraud flag
Empty fact transaction table
Empty staging transaction table

Các kiểm tra về tính đầy đủ, tính duy nhất, tính hợp lệ và tính toàn
vẹn tham chiếu đều đạt yêu cầu.