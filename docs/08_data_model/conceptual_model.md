# CONCEPTUAL MODEL

**Dự án:** Ecommerce Fraud Detection Data Warehouse  
**Phase:** 08 — Data Modeling  
**Ngày tạo:** 02/09/2026  

---

## 1. MỤC TIÊU

Thiết kế **Conceptual Data Model** mô tả các thực thể và mối quan hệ ở mức trừu tượng, không quan tâm đến cách lưu trữ vật lý.

---

## 2. CÁC THỰC THỂ (ENTITIES)

| Entity | Mô tả | Chính tả |
|--------|-------|----------|
| **Transaction** | Một giao dịch thương mại điện tử | Giao dịch thanh toán bằng thẻ |
| **Identity** | Thông tin định danh người thực hiện giao dịch | Browser, thiết bị, OS |
| **Product** | Loại sản phẩm giao dịch (W, H, C, S, R) | Mã sản phẩm |
| **Card** | Thông tin thẻ thanh toán | Thẻ tín dụng/debit |
| **Device** | Thiết bị thực hiện giao dịch | Desktop, mobile, browser info |
| **Email** | Thông tin email người mua và người nhận | Email domain |
| **Address** | Thông tin địa chỉ thanh toán/giao hàng | Billing/shipping address |
| **Date** | Thời gian giao dịch | Ngày/giờ |
| **FraudPrediction** | Kết quả dự đoán fraud | Xác suất, risk score |
| **VestaFeatures** | Các đặc trưng kỹ thuật số ẩn danh từ Vesta | V1-V339 |

---

## 3. MÔ HÌNH THỰC THỂ

```
[Transaction]
  - transaction_id (PK)
  - is_fraud (label)
  - transaction_amt
  - transaction_dt
  - product_id (FK → Product)
  - card_id (FK → Card)
  - device_id (FK → Device)
  - email_id (FK → Email)
  - address_id (FK → Address)
  - date_id (FK → Date)
  - ... (Vesta features V1-V339, C1-C14, D1-D15, M1-M9)

[Identity]
  - identity_id (PK)
  - transaction_id (FK → Transaction)
  - ... (id_01 - id_38)

[Product]
  - product_id (PK)
  - product_cd
  - product_category

[Card]
  - card_id (PK)
  - card1, card2, card3, card4, card5, card6

[Device]
  - device_id (PK)
  - device_type
  - device_info

[Email]
  - email_id (PK)
  - p_email_domain
  - r_email_domain

[Address]
  - address_id (PK)
  - addr1, addr2, dist1, dist2

[Date]
  - date_id (PK)
  - full_date
  - day_of_week, month, quarter, year

[FraudPrediction]
  - prediction_id (PK)
  - transaction_id (FK → Transaction)
  - fraud_probability
  - predicted_label
  - risk_score
  - risk_level
  - model_version
  - predicted_at
```

---

## 4. MỐI QUAN HỆ

```text
Transaction (1) ───(1:1)─── Identity
     │
     ├── (N:1) → Product
     ├── (N:1) → Card
     ├── (N:1) → Device
     ├── (N:1) → Email
     ├── (N:1) → Address
     ├── (N:1) → Date
     └── (1:1) → FraudPrediction
```

- **Transaction → Identity**: 1 Transaction có thể có 0 hoặc 1 Identity (LEFT JOIN)
- **Transaction → Product/Card/Device/Email/Address/Date**: N Transaction → 1 Dimension (many-to-one)
- **Transaction → FraudPrediction**: 1 Transaction → 1 Prediction (one-to-one)

---

## 5. STAR SCHEMA (CONCEPTUAL)

```
                    [dim_date]
                        │
                    [fact_transaction]
                   ┌───┬───┬───┬───┐
                   │   │   │   │   │
             [dim_  [dim_ [dim_ [dim_
             product card  device email]
                   │   │   │   │   │
                   └───┴───┴───┴───┘
                   
                    [fact_fraud_prediction]
                        │
                   (FK to fact_transaction)
```

*Cập nhật: 02/09/2026 | Version: 1.0*
