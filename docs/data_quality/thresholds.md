# Data Quality Thresholds

## 1. Mục đích

Threshold là các ngưỡng được sử dụng để xác định dữ liệu có đáp ứng
yêu cầu chất lượng hay không.

Baseline mô tả trạng thái dữ liệu thực tế tại thời điểm kiểm tra,
trong khi threshold mô tả giới hạn mà hệ thống sử dụng để đánh giá.

---

## 2. Quality Rules

| Rule | Threshold | Current result | Status |
|---|---:|---:|---|
| Fraud ratio | 2% – 5% | 3.4990% | PASS |
| Negative transaction amount | = 0 | 0 | PASS |
| Non-positive transaction amount | = 0 | 0 | PASS |
| NULL transaction_id | = 0 | 0 | PASS |
| Duplicate transaction_id | = 0 | 0 | PASS |
| Orphan transaction | = 0 | 0 | PASS |
| Invalid is_fraud | = 0 | 0 | PASS |
| Missing device_type | <= 30% | 2.3732% | PASS |
| Empty fact table | = 0 rows | 590,540 rows | PASS |
| Empty staging table | = 0 rows | 590,540 rows | PASS |

---

## 3. Fraud Ratio

Fraud ratio được kiểm soát trong khoảng:

**2% – 5%**

Công thức:

```text
fraud_ratio =
fraud_transactions / total_transactions × 100

Baseline hiện tại:

20,663 / 590,540 × 100 = 3.4990%

Do đó dữ liệu hiện tại nằm trong khoảng threshold.

4. Missing Device Type

Missing device_type được giới hạn ở mức:

<= 30%

Baseline:

3,423 / 144,233 × 100 = 2.3732%

Giá trị hiện tại thấp hơn threshold.

5. Zero-Tolerance Integrity Rules

Các quy tắc sau sử dụng zero tolerance:

NULL transaction_id = 0
Duplicate transaction_id = 0
Orphan transaction = 0
Negative transaction amount = 0
Non-positive transaction amount = 0
Invalid fraud flag = 0

Nếu một trong các điều kiện này không đạt, Data Quality Gate phải
được xem là FAILED.