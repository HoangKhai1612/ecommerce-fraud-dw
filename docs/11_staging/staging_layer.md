# PHASE 11 — STAGING Layer

## 1. MỤC TIÊU

Xây dựng STAGING Layer bằng dbt (data build tool) để:
- **Ép kiểu dữ liệu** từ TEXT (RAW) sang các kiểu PostgreSQL phù hợp
- **Chuẩn hóa tên cột** (snake_case thay vì PascalCase)
- **Thêm cột audit** `_loaded_at`
- **Tạo natural key** `transaction_id`

---

## 2. VÌ SAO DBT?

| Công cụ | Cách làm | Độ phức tạp |
|---------|----------|-------------|
| Python script | Viết SQL thủ công | Cao (duplicate logic) |
| **dbt** | Định nghĩa models dưới dạng SQL + YAML | Thấp (declarative) |
| Pandas | Transform in-memory | Rất cao (memory intensive) |

**Lý do chọn dbt:**
- Tích hợp sẵn với PostgreSQL
- Version control-friendly (SQL files)
- Tự động test, documentation
- Incremental models support

---

## 3. CÀI ĐẶT

```powershell
# Kích hoạt venv
.venv\Scripts\Activate.ps1

# Cài dbt
pip install dbt-core dbt-postgres

# (Nếu lỗi protobuf với Python 3.14)
pip install --upgrade protobuf
```

### Cấu trúc thư mục dbt

```
dbt/
├── dbt_project.yml           # Cấu hình project
├── profiles.yml              # Cấu hình kết nối DB
├── macros/
│   └── schema_override.sql   # Override schema naming macro
├── models/
│   ├── src/
│   │   └── raw_sources.yml   # Định nghĩa nguồn dữ liệu
│   └── staging/
│       ├── stg_transactions.sql
│       └── stg_identity.sql
|       |__staging.yml
├── tests/                     # dbt test files
├── target/                    # Output (auto-generated)
└── logs/                      # Logs (auto-generated)
```

---

## 4. CẤU HÌNH

### profiles.yml (`$HOME/.dbt/profiles.yml`)

```yaml
ecommerce_fraud_dw:
  target: dev
  outputs:
    dev:
      type: postgres
      host: localhost
      user: postgres
      password: postgres
      port: 5432
      dbname: ecommerce_fraud_dw
      schema: raw          # Default schema (for sources)
      threads: 4
```

### dbt_project.yml

```yaml
name: ecommerce_fraud_dw
version: "1.0"
config-version: 2
profile: ecommerce_fraud_dw
model-paths: ["models"]
macro-paths: ["macros"]
test-paths: ["tests"]
target-path: "target"
clean-targets: ["target", "dbt_packages"]

models:
  ecommerce_fraud_dw:
    staging:
      +schema: staging       # Override schema for staging models
      +materialized: view
    marts:
      +schema: marts
      +materialized: table

on-run-start:
  - "SELECT 1"
```

### Schema override macro (`macros/schema_override.sql`)

Vì dbt mặc định nối schema dạng `{target_schema}_{model_schema}` (ví dụ: `raw_staging`), ta cần override macro này để dùng tên schema trực tiếp.

```sql
{% macro default__generate_schema_name(custom_schema_name, node) -%}
    {%- if custom_schema_name is none -%}
        {{ return(target.schema) }}
    {%- else -%}
        {{ return(custom_schema_name) }}
    {%- endif -%}
{%- endmacro %}
```

---

## 5. SOURCE DEFINITIONS

File: `dbt/models/src/raw_sources.yml`

```yaml
version: 2

sources:
  - name: raw
    database: ecommerce_fraud_dw
    schema: raw
    description: "RAW layer — direct copy of CSV source data"
    tables:
      - name: transactions
        description: "IEEE-CIS transaction data (590,540 rows, 394 columns)"
      - name: identity
        description: "IEEE-CIS identity data (144,233 rows, 41 columns)"

models:
  - name: stg_transactions
    description: "Staging model for transaction data — type cast and renamed from raw.transactions"
    columns:
      - name: transaction_id
        description: "Unique transaction ID"
      - name: is_fraud
        description: "Fraud label (0 or 1)"
      - name: transaction_amt
        description: "Transaction amount in USD"
      - name: product_cd
        description: "Product code (W, H, C, S, R)"

  - name: stg_identity
    description: "Staging model for identity data — type cast from raw.identity"
    columns:
      - name: transaction_id
        description: "FK to stg_transactions"
      - name: device_type
        description: "Device type: desktop, mobile, or Unknown"
      - name: device_info
        description: "Device info string"
```

---

## 6. STAGING MODELS

### 6.1 stg_transactions.sql

File: `dbt/models/staging/stg_transactions.sql`

```sql
-- Staging model: transactions
-- Purpose: Convert raw.transactions TEXT columns to proper types
-- Output: staging.stg_transactions

{{ config(materialized='view', schema='staging') }}

with source as (
    select * from {{ source('raw', 'transactions') }}
),

renamed as (
    select
        "TransactionID"::bigint as transaction_id,
        "isFraud"::smallint as is_fraud,
        "TransactionDT"::bigint as transaction_dt,
        "TransactionAmt"::numeric(12,2) as transaction_amt,
        "ProductCD"::varchar(10) as product_cd,
        "card1"::integer as card1,
        "card2"::float as card2,
        "card3"::float as card3,
        "card4"::varchar(20) as card4,
        "card5"::float as card5,
        "card6"::varchar(20) as card6,
        "addr1"::integer as addr1,
        "addr2"::integer as addr2,
        "dist1"::float as dist1,
        "dist2"::float as dist2,
        "P_emaildomain"::varchar(255) as p_emaildomain,
        "R_emaildomain"::varchar(255) as r_emaildomain,

        -- Counting features C1-C14
        {% for i in range(1, 15) %}
        "C{{ i }}"::float as c{{ i }},
        {% endfor %}

        -- Timedelta features D1-D15
        {% for i in range(1, 16) %}
        "D{{ i }}"::float as d{{ i }},
        {% endfor %}

        -- Match features M1-M9
        {% for i in range(1, 10) %}
        "M{{ i }}"::varchar(10) as m{{ i }},
        {% endfor %}

        -- Vesta features V1-V339
        {% for i in range(1, 340) %}
        "V{{ i }}"::float as v{{ i }},
        {% endfor %}

        current_timestamp as _loaded_at

    from source
)

select * from renamed
```

### 6.2 stg_identity.sql

File: `dbt/models/staging/stg_identity.sql`

```sql
-- Staging model: identity
-- Purpose: Convert raw.identity TEXT columns to proper types
-- Output: staging.stg_identity

{{ config(materialized='view', schema='staging') }}

with source as (
    select * from {{ source('raw', 'identity') }}
),

renamed as (
    select
        "TransactionID"::bigint as transaction_id,

        -- Identity features id_01 - id_11 (numeric)
        {% for i in range(1, 12) %}
        "id_{{ '%02d' | format(i) }}"::float as id_{{ '%02d' | format(i) }},
        {% endfor %}

        -- Identity features id_12 - id_38 (mixed string/float)
        {% for i in range(12, 39) %}
        "id_{{ '%02d' | format(i) }}"::varchar(50) as id_{{ '%02d' | format(i) }},
        {% endfor %}

        "DeviceType"::varchar(20) as device_type,
        "DeviceInfo"::varchar(255) as device_info,

        current_timestamp as _loaded_at

    from source
)

select * from renamed
```

---

## 7. CHẠY VÀ KIỂM TRA

```bash
# 1. Kiểm tra cấu hình
dbt debug

# 2. Parse dự án
dbt parse

# 3. Chạy staging models
dbt run --select staging.*

# 4. Verify kết quả (trong psql hoặc python script)
psql -h localhost -U postgres -d ecommerce_fraud_dw -c "SELECT COUNT(*) FROM staging.stg_transactions;"
```

### Expected output:
```
Found 2 models, 1 operation, 2 sources, 429 macros
1 of 2 OK created sql view model staging.stg_identity  [CREATE VIEW in 0.12s]
2 of 2 OK created sql view model staging.stg_transactions [CREATE VIEW in 0.13s]
```

---

## 8. KẾT QUả

| Model | Rows | Columns | Status |
|-------|------|---------|--------|
| stg_transactions | 590,540 | 395 (incl. _loaded_at) | ✅ PASS |
| stg_identity | 144,233 | 41 (incl. _loaded_at) | ✅ PASS |

### Data types chuyển đổi:

| Column | RAW type | Staging type |
|--------|----------|-------------|
| TransactionID | TEXT | bigint |
| isFraud | TEXT | smallint |
| TransactionAmt | TEXT | numeric(12,2) |
| ProductCD | TEXT | varchar(10) |
| C1-C14 | TEXT | float |
| D1-D15 | TEXT | float |
| M1-M9 | TEXT | varchar(10) |
| V1-V339 | TEXT | float |
| id_01-id_11 | TEXT | float |
| id_12-id_38 | TEXT | varchar(50) |

---

## 9. SUCCESS CRITERIA

```text
[✅] dbt-core + dbt-postgres installed
[✅] dbt_project.yml + profiles.yml configured
[✅] Schema override macro working
[✅] Source definitions for raw.transactions, raw.identity
[✅] stg_transactions model created (staging schema)
[✅] stg_identity model created (staging schema)
[✅] Row counts match RAW layer
[✅] Data types properly cast
[✅] Column names standardized (snake_case)
[✅] Documentation (this file + evidence)
```

---

## 10. ISSUES & TROUBLESHOOTING

| Issue | Fix |
|-------|-----|
| Schema shows `raw_staging` | Override `default__generate_schema_name` macro |
| protobuf error with Python 3.14 | `pip install --upgrade protobuf` |
| Git not found error | Install Git hoặc bỏ qua (dbt vẫn chạy được) |
| Connection refused | `docker compose up -d postgres` |

---

## 11. Liên hệ

- Trước: [PHASE 10 — RAW Layer](../10_raw/raw_layer.md)
- Sau: [PHASE 12 — dbt Star Schema Models](../12_dbt_models/dbt_models.md)
- Chapter 4.3 in đề cương

*Cập nhật: 02/09/2026 | Version: 1.0*
