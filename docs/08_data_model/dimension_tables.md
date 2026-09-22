# DIMENSION TABLES DESIGN

**Dự án:** Ecommerce Fraud Detection Data Warehouse  
**Phase:** 08 — Data Modeling  
**Ngày tạo:** 02/09/2026  

---

## 1. dim_date

### Mô tả:
Dimension thời gian, dựa trên TransactionDT (giây từ 28/09/2017).

| Column | Data Type | Key Type | Mô tả |
|--------|-----------|----------|-------|
| `date_key` | INT | PK | YYYYMMDD |
| `transaction_date` | DATE | NK | Ngày thực tế |
| `day_of_week` | VARCHAR(10) | Attribute | Thứ (Monday, Tuesday...) |
| `day_of_month` | SMALLINT | Attribute | Ngày trong tháng |
| `day_of_year` | SMALLINT | Attribute | Ngày trong năm |
| `week_of_year` | SMALLINT | Attribute | Tuần trong năm |
| `month` | SMALLINT | Attribute | Tháng (1-12) |
| `quarter` | SMALLINT | Attribute | Quý (1-4) |
| `year` | SMALLINT | Attribute | Năm |

### Source:
TransactionDT → convert thành datetime tại thời điểm 28/09/2017 00:00:00 UTC.

---

## 2. dim_product

### Mô tả:
Dimension chứa thông tin sản phẩm (ProductCD).

| Column | Data Type | Key Type | Mô tả |
|--------|-----------|----------|-------|
| `product_key` | SERIAL | PK (SK) | Surrogate key |
| `product_cd` | VARCHAR(1) | NK | W, H, C, S, R |
| `product_category_name` | VARCHAR(50) | Attribute | Tên danh mục |

### Values:
| product_cd | product_category_name |
|-----------|----------------------|
| W | Web |
| H | Host |
| C | Connect |
| S | Subscription |
| R | Re-authorization |

---

## 3. dim_card

### Mô tả:
Dimension chứa thông tin thẻ thanh toán.

| Column | Data Type | Key Type | Mô tả |
|--------|-----------|----------|-------|
| `card_key` | SERIAL | PK (SK) | Surrogate key |
| `card1` | VARCHAR(10) | NK | Loại thẻ (1-6) |
| `card2` | VARCHAR(10) | Attribute | Thương hiệu (Visa, Mastercard...) |
| `card3` | VARCHAR(10) | Attribute | Country code |
| `card4` | VARCHAR(20) | Attribute | visa/mastercard/... |
| `card5` | VARCHAR(20) | Attribute | card5 value |
| `card6` | VARCHAR(20) | Attribute | debit/credit |

---

## 4. dim_device

### Mô tả:
Dimension chứa thông tin thiết bị từ identity data.

| Column | Data Type | Key Type | Mô tả |
|--------|-----------|----------|-------|
| `device_key` | SERIAL | PK (SK) | Surrogate key |
| `device_type` | VARCHAR(20) | NK | desktop, mobile, Unknown |
| `device_info` | VARCHAR(255) | Attribute | Browser/OS info |

### Values:
| device_type | Mô tả |
|-------------|-------|
| desktop | Giao dịch trên máy tính để bàn |
| mobile | Giao dịch trên thiết bị di động |
| Unknown | Không có thông tin (transactions không có identity) |

---

## 5. dim_email

### Mô tả:
Dimension chứa thông tin email người mua và người nhận.

| Column | Data Type | Key Type | Mô tả |
|--------|-----------|----------|-------|
| `email_key` | SERIAL | PK (SK) | Surrogate key |
| `p_email_domain` | VARCHAR(255) | NK | Email domain người mua |
| `r_email_domain` | VARCHAR(255) | Attribute | Email domain người nhận |
| `is_free_email` | BOOLEAN | Attribute | Gmail/Yahoo/... (mail miễn phí) |

### Values (free email domains):
- gmail.com, yahoo.com, hotmail.com, aol.com, icloud.com, msn.com, outlook.com

---

## 6. DIMENSION TABLES SUMMARY

| Table | PK | NK | Rows (expected) | SCD Type |
|-------|----|-----|-----------------|----------|
| dim_date | date_key | transaction_date | ~30 | Static |
| dim_product | product_key | product_cd | 5 | Static |
| dim_card | card_key | card1 | Variable (~100+) | Static |
| dim_device | device_key | device_type | Variable (~50+) | Static |
| dim_email | email_key | p_email_domain | Variable (~50+) | Static |

> **Lưu ý:** Không có Slowly Changing Dimension (SCD) Type 2 vì:
> 1. Đây là dữ liệu batch tĩnh (IEEE-CIS 2019)
> 2. De cuoong không yêu cầu tracking historical changes
> 3. Phù hợp với quy mô đồ án đại học

*Cập nhật: 02/09/2026 | Version: 1.0*
