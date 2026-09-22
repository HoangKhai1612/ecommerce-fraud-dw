PHASE 12 — XÂY DỰNG STAR SCHEMA DATA WAREHOUSE

Dựa trên những gì em đã thực sự làm, thầy viết lại Phase 12 theo đúng trạng thái hiện tại, không ghi những phần chưa hoàn thành thành đã hoàn thành.

12.1. Mục tiêu của Phase 12

Mục tiêu của Phase 12 là chuyển dữ liệu từ lớp STAGING sang mô hình Star Schema trong Data Warehouse.

Kiến trúc mục tiêu gồm:

                    ┌─────────────────┐
                    │    dim_date     │
                    │─────────────────│
                    │ date_key        │
                    │ transaction_day │
                    │ day_of_week     │
                    │ week_number     │
                    └────────┬────────┘
                             │
                             │
┌─────────────────┐          │          ┌─────────────────┐
│   dim_product   │          │          │    dim_device   │
│─────────────────│          │          │─────────────────│
│ product_key     │          │          │ device_key      │
│ product_cd      │          │          │ device_type     │
│ card4           │          │          │ device_info     │
└────────┬────────┘          │          └────────┬────────┘
         │                   │                   │
         │                   ▼                   │
         └──────────────► FACT ◄────────────────┘
                       TRANSACTIONS
                 ┌─────────────────────┐
                 │ transaction_key     │
                 │ transaction_id      │
                 │ is_fraud            │
                 │ transaction_dt      │
                 │ transaction_amt     │
                 │ product_key         │
                 │ device_key          │
                 │ C1-C14              │
                 │ D1-D15              │
                 │ M1-M9               │
                 │ V1-V339             │
                 │ ID_01-ID_38         │
                 └─────────────────────┘
12.2. Xác định grain của Fact

Đây là quyết định quan trọng nhất trước khi xây dựng fact_transactions.

Grain được xác định là:

Một dòng trong fact_transactions tương ứng với đúng một giao dịch trong dataset IEEE-CIS.

Khóa nghiệp vụ:

transaction_id

Khóa thay thế của Data Warehouse:

transaction_key

Hai khái niệm này được tách biệt.

transaction_id là ID gốc từ dataset, trong khi transaction_key là surrogate key được tạo trong Data Warehouse.

12.3. Kiểm tra tính duy nhất của Transaction

Trước khi JOIN các bảng, đã kiểm tra:

SELECT
    COUNT(*) AS total_rows,
    COUNT(DISTINCT transaction_id) AS distinct_transaction_ids
FROM staging.stg_transactions;

Kết quả:

total_rows              = 590540
distinct_transaction_ids = 590540

Điều này xác nhận:

1 transaction_id = 1 transaction

Không có duplicate transaction trong stg_transactions.

12.4. Kiểm tra bảng Identity

Đã kiểm tra:

SELECT
    COUNT(*) AS total_rows,
    COUNT(DISTINCT transaction_id) AS distinct_transaction_ids
FROM staging.stg_identity;

Kết quả:

total_rows              = 144233
distinct_transaction_ids = 144233

Đồng thời kiểm tra duplicate:

duplicate transaction_id = 0

Điều này rất quan trọng bởi vì nếu stg_identity có nhiều dòng cho cùng một transaction_id, phép:

LEFT JOIN identity
    ON t.transaction_id = i.transaction_id

có thể làm nhân bản số dòng của fact.

Kết quả kiểm tra cho thấy điều đó không xảy ra.

12.5. Xử lý TransactionDT

TransactionDT của IEEE-CIS không được coi trực tiếp là Unix timestamp.

Dữ liệu đã kiểm tra có:

MIN(TransactionDT) = 86400
MAX(TransactionDT) = 15811131

Tương ứng:

MIN / 86400 ≈ 1 ngày
MAX / 86400 ≈ 183 ngày

Do đó Phase 12 không tự ý chuyển TransactionDT thành ngày lịch thực tế.

Thay vào đó xây dựng dim_date theo ngày tương đối của dataset.

12.6. Xây dựng dim_date

Model:

models/marts/dim_date.sql

Grain:

Một dòng tương ứng với một ngày tương đối trong dataset.

Các trường:

Cột	Ý nghĩa
date_key	Khóa ngày
transaction_day	Ngày tương đối
day_of_week	Chỉ số thứ trong tuần
week_number	Tuần tương đối

Hiện tại dimension được xây dựng cho:

1 → 183

tương ứng với khoảng thời gian tương đối của TransactionDT.

Không bịa ngày lịch thực tế khi chưa có reference date đáng tin cậy.

12.7. Xây dựng dim_product

Model:

models/marts/dim_product.sql

Grain:

(product_cd, card4)

Không sử dụng product_cd đơn độc làm grain vì cùng một product_cd có thể xuất hiện với nhiều card4.

Dimension gồm:

product_key
product_cd
card4

Trong đó:

product_key

là surrogate key.

Kết quả build trước đó:

dim_product = 22 rows
12.8. Xây dựng dim_device

Model:

models/marts/dim_device.sql

Grain:

(device_type, device_info)

Dimension gồm:

device_key
device_type
device_info

Trong đó:

device_key

là surrogate key.

Kết quả build trước đó:

dim_device = 1939 rows
12.9. Xây dựng fact_transactions

Model:

models/marts/fact_transactions.sql

Fact được xây dựng từ:

stg_transactions
        +
stg_identity
        +
dim_product
        +
dim_device

Quan hệ JOIN chính:

transaction_id
product_cd + card4
device_type + device_info

Fact giữ lại:

Transaction attributes
transaction_id
is_fraud
transaction_dt
transaction_amt
product_cd
Product/Card
card1 - card6
Address/Distance
addr1
addr2
dist1
dist2
Email
p_emaildomain
r_emaildomain
C features
C1 - C14
D features
D1 - D15
M features
M1 - M9
V features
V1 - V339
Identity features
id_01 - id_38
Device
device_type
device_info

và các surrogate key:

transaction_key
product_key
device_key
12.10. Xử lý lỗi kiểu dữ liệu trong STAGING

Trong quá trình build Phase 12 đã phát hiện lỗi:

invalid input syntax for type integer: "315.0"

Nguyên nhân là một số trường được khai báo integer trong staging nhưng dữ liệu RAW có thể xuất hiện dưới dạng số thập phân như:

315.0

Đã xử lý lại logic cast đối với các trường:

card1
addr1
addr2

theo hướng kiểm tra định dạng trước khi chuyển kiểu.

Sau đó chạy lại:

dbt build --select staging

và hiện tại:

PASS=11
WARN=0
ERROR=0

Do đó lỗi staging này đã được xử lý thành công.

12.11. Data Quality Tests của STAGING

Hiện tại đã có các kiểm tra:

stg_transactions
transaction_id
    → not_null
    → unique

is_fraud
    → not_null
    → accepted_values [0, 1]

transaction_amt
    → not_null

product_cd
    → not_null
stg_identity
transaction_id
    → not_null
    → unique

transaction_id
    → relationships
       → stg_transactions.transaction_id

Kết quả thực tế mới nhất:

8 data tests
8 PASS
0 ERROR
0 WARN
12.12. Trạng thái Phase 12 hiện tại

Thầy chia rõ thành đã hoàn thành và chưa hoàn thành để mình không tự đánh dấu sai tiến độ.

Hạng mục	Trạng thái
Xác định grain fact	✅ Hoàn thành
Kiểm tra uniqueness transaction	✅ Hoàn thành
Kiểm tra uniqueness identity	✅ Hoàn thành
Kiểm tra khả năng nhân bản JOIN	✅ Hoàn thành
Phân tích TransactionDT	✅ Hoàn thành
Tạo dim_date	✅ Đã tạo
Tạo dim_product	✅ Đã tạo
Tạo dim_device	✅ Đã tạo
Tạo fact_transactions	⚠️ Đã viết, cần build/validate cuối
Staging data quality	✅ PASS
schema.yml	✅ Đã sửa
dbt parse	✅ PASS
dbt build --select staging	✅ PASS
Build toàn bộ marts	⏳ Chưa chốt
Validate số dòng fact	⏳ Chưa chốt
Validate duplicate fact	⏳ Chưa chốt
Validate FK	⏳ Chưa chốt
Validate fraud distribution	⏳ Chưa chốt
Validate tổng transaction amount	⏳ Chưa chốt
Xác nhận Star Schema cuối cùng	⏳ Chưa chốt
12.13. Trạng thái hiện tại của em

Có thể ghi ngắn gọn trong project log:

PHASE 12 STATUS: IN PROGRESS

STAGING:
    PASS

DIM_DATE:
    CREATED

DIM_PRODUCT:
    CREATED

DIM_DEVICE:
    CREATED

FACT_TRANSACTIONS:
    MODEL CREATED
    FINAL BUILD VALIDATION PENDING

DATA QUALITY:
    PASS

CURRENT NEXT STEP:
    dbt build --select marts

FOLLOWING VALIDATION:
    - Fact row count
    - Distinct transaction_id
    - Duplicate transaction check
    - Foreign-key integrity
    - NULL analysis
    - Fraud distribution

Điểm quan trọng: đừng ghi PHASE 12 = COMPLETED ngay lúc này. Phần STAGING đã 100% PASS, còn Phase 12 cần build marts và kiểm chứng fact_transactions có đúng 590.540 dòng / 590.540 transaction duy nhất hay không. Khi qua được bộ validation đó, lúc ấy mới khóa Phase 12 là hoàn thành.