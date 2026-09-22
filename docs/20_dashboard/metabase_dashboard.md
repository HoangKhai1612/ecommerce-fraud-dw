# PHASE 20 — Metabase Dashboard

## 1. MỤC TIÊU

Xây dựng dashboard trong Metabase để visualize:
- Tổng quan giao dịch (số lượng, số tiền)
- Rate gian lận theo thời gian
- Phân bố gian lận theo thiết bị
- Phân bố gian lận theo product
- Top dự đoán gian lận

---

## 2. CÀI ĐẶT

```yaml
# Thêm vào docker-compose.yml
  metabase:
    image: metabase/metabase:v0.49.0
    ports:
      - "3000:3000"
    environment:
      - MB_DB_TYPE=postgres
      - MB_DB_DBNAME=metabase_db
      - MB_DB_PORT=5432
      - MB_DB_USER=postgres
      - MB_DB_PASS=postgres
      - MB_DB_HOST=postgres
    depends_on:
      - postgres
    volumes:
      - metabase_data:/metabase-data
```

```bash
docker compose up -d metabase
# Truy cập: http://localhost:3000
```

---

## 3. DASHBOARD QUERIES

### 3.1 Overview metrics

```sql
-- Total transactions
SELECT COUNT(*) as total_transactions FROM marts.fact_transactions;

-- Total fraud
SELECT COUNT(*) as total_fraud FROM marts.fact_transactions WHERE is_fraud = 1;

-- Fraud rate
SELECT 
    ROUND(COUNT(CASE WHEN is_fraud = 1 THEN 1 END) * 100.0 / COUNT(*), 2) as fraud_rate_pct
FROM marts.fact_transactions;

-- Total transaction amount
SELECT SUM(transaction_amt) as total_amount FROM marts.fact_transactions;
```

### 3.2 Fraud rate over time

```sql
SELECT 
    DATE_TRUNC('day', transaction_date) as day,
    COUNT(*) as total,
    COUNT(CASE WHEN is_fraud = 1 THEN 1 END) as fraud_count,
    ROUND(COUNT(CASE WHEN is_fraud = 1 THEN 1 END) * 100.0 / COUNT(*), 2) as fraud_rate
FROM marts.fact_transactions f
LEFT JOIN marts.dim_date d ON f.transaction_dt = d.transaction_dt
GROUP BY day
ORDER BY day;
```

### 3.3 Fraud by device type

```sql
SELECT 
    COALESCE(device_type, 'Unknown') as device_type,
    COUNT(*) as total_transactions,
    COUNT(CASE WHEN is_fraud = 1 THEN 1 END) as fraud_count,
    ROUND(COUNT(CASE WHEN is_fraud = 1 THEN 1 END) * 100.0 / COUNT(*), 2) as fraud_rate
FROM marts.fact_transactions
GROUP BY device_type
ORDER BY fraud_rate DESC;
```

### 3.4 Fraud by product code

```sql
SELECT 
    product_cd,
    COUNT(*) as total_transactions,
    COUNT(CASE WHEN is_fraud = 1 THEN 1 END) as fraud_count,
    ROUND(COUNT(CASE WHEN is_fraud = 1 THEN 1 END) * 100.0 / COUNT(*), 2) as fraud_rate
FROM marts.fact_transactions
GROUP BY product_cd
ORDER BY fraud_rate DESC;
```

### 3.5 Top fraud predictions (from marts.predictions)

```sql
SELECT 
    transaction_id,
    is_fraud_actual,
    is_fraud_predicted,
    ROUND(fraud_probability * 100, 2) as fraud_probability_pct,
    transaction_amt
FROM marts.predictions
ORDER BY fraud_probability DESC
LIMIT 50;
```

---

## 4. DASHBOARD STRUCTURE

| Dashboard | Cards | Metrics |
|-----------|-------|---------|
| Overview | 4 | Total transactions, total fraud, fraud rate, total amount |
| Fraud Trend | 1 | Line chart: fraud rate over time |
| Device Analysis | 1 | Bar chart: fraud rate by device type |
| Product Analysis | 1 | Bar chart: fraud rate by product code |
| Prediction Results | 1 | Table: top 50 fraud predictions |

---

## 5. CHẠO

```bash
# 1. Start Metabase
docker compose up -d metabase

# 2. Setup database connection
# http://localhost:3000/setup
# Admin: admin@metabase.com / Admin123!

# 3. Add database
# Admin → Admin → Database → Add database
# Name: ecommerce_fraud_dw
# Engine: PostgreSQL
# Host: postgres
# Port: 5432
# Database: ecommerce_fraud_dw
# Username: postgres
# Password: postgres

# 4. Sync schema
# Click "Sync schema" → "Scan"
```

---

## 6. SUCCESS CRITERIA

```text
[✅] Metabase running (http://localhost:3000)
[✅] Database connected (ecommerce_fraud_dw)
[✅] SQL queries working
[✅] Dashboard: Overview (4 metrics)
[✅] Dashboard: Fraud Trend (line chart)
[✅] Dashboard: Device Analysis (bar chart)
[✅] Dashboard: Product Analysis (bar chart)
[✅] Dashboard: Prediction Results (table)
```

---

## 7. Liên hệ

- Trước: [PHASE 19 — Model Integration](../19_model_integration/model_integration.md)
- Sau: [PHASE 21 — FastAPI](../21_api/fastapi_api.md)

*Cập nhật: 02/09/2026 | Version: 1.0*
