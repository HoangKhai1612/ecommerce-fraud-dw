# Sơ đồ Mermaid và hướng dẫn chụp ảnh minh chứng

Tài liệu này đi kèm báo cáo. Mermaid phù hợp để vẽ **sơ đồ khái niệm/kiến trúc**. Ảnh chụp màn hình chứng minh **phần mềm đã chạy thật**; không dùng sơ đồ Mermaid thay cho ảnh chụp giao diện.

## 1. Sơ đồ kiến trúc tổng thể

Có thể đặt ở phần kiến trúc hệ thống (Chương 3). Rà lại tên module với phiên bản triển khai cuối trước khi chèn.

~~~mermaid
flowchart LR
    SRC[Transaction data] --> ING[Ingestion]
    ING --> RAW[(RAW layer)]
    RAW --> DBT[dbt: staging, marts, tests]
    DBT --> DW[(PostgreSQL Data Warehouse)]
    AF[Apache Airflow] -. orchestrates .-> ING
    AF -. orchestrates .-> DBT
    DW --> ML[Model training and evaluation]
    ML --> ART[(Model artifacts)]
    ART --> API[FastAPI]
    DW --> BI[Metabase dashboards]
    WEB[React web app] --> API
    API --> WEB
    API --> DW
~~~

## 2. Sơ đồ luồng dữ liệu

~~~mermaid
flowchart TD
    A[Source files / transaction data] --> B[Ingestion]
    B --> C[(RAW)]
    C --> D[dbt staging: type and schema cleanup]
    D --> E[dbt marts: facts and dimensions]
    E --> F[(Data Warehouse)]
    F --> G[Data quality tests]
    F --> H[Feature preparation]
    H --> I[Train / validation / test]
    I --> J[Model evaluation]
    J --> K[API inference with XGBoost]
    F --> L[Metabase analytics]
    O[Airflow] -. schedules and monitors .-> B
    O -. schedules and monitors .-> D
~~~

## 3. Sơ đồ huấn luyện và suy luận

Đặt ở phần Machine Learning. Sơ đồ thể hiện LightGBM đã được đánh giá Phase 30 nhưng API hiện sử dụng XGBoost.

~~~mermaid
flowchart LR
    D[(Prepared dataset)] --> SPLIT[Train / validation / test]
    SPLIT --> TRAIN[Train Logistic Regression, Random Forest, XGBoost, LightGBM]
    TRAIN --> VAL[Compare metrics on validation]
    VAL --> REPORT[ROC-AUC, PR-AUC, Precision, Recall, F1]
    XGB[XGBoost artifact] --> API[Current API inference]
    LGBM[LightGBM evaluated in Phase 30] -. not currently served by API .-> REPORT
~~~

## 4. Sơ đồ tích hợp Web/API

~~~mermaid
sequenceDiagram
    actor U as User
    participant W as React Web
    participant A as FastAPI
    participant M as XGBoost model
    participant D as PostgreSQL / Data Warehouse
    U->>W: Enter transaction or open dashboard
    W->>A: Send HTTP request
    A->>M: Run fraud inference
    M-->>A: Score and predicted class
    A->>D: Store/read permitted data
    D-->>A: Result or records
    A-->>W: JSON response
    W-->>U: Show prediction and status
~~~

## 5. Xuất sơ đồ Mermaid thành ảnh

1. Sao chép một khối Mermaid ở trên.
2. Mở [Mermaid Live Editor](https://mermaid.live/).
3. Dán code, kiểm tra sơ đồ không báo lỗi và các nhãn không bị cắt.
4. Chọn **Actions → PNG** (hoặc SVG nếu trường yêu cầu vector).
5. Đặt tên tệp, ví dụ: hinh_kien_truc_tong_the.png.
6. Trong Word chọn **Insert → Pictures → This Device**, chèn ảnh; căn giữa, đặt độ rộng vừa trang và thêm caption bằng **References → Insert Caption**.
7. Ghi nguồn “Nguồn: Nhóm tác giả tổng hợp từ kiến trúc triển khai của đề tài.” Chỉ dùng câu này cho sơ đồ tự dựng, không dùng cho ảnh chụp phần mềm.

## 6. Hướng dẫn chụp ảnh minh chứng thật cho Chương 4

Chụp từ ứng dụng/repo đang chạy, không vẽ lại giao diện. Kiểm tra ảnh không lộ token, mật khẩu, connection string hoặc dữ liệu cá nhân.

| Phần báo cáo | Bằng chứng nên chụp | Cách chụp/điều kiện |
|---|---|---|
| Data Warehouse | Kết quả query đếm dòng hoặc schema fact/dimension | Chạy truy vấn đọc trong pgAdmin/DBeaver hoặc psql; ảnh thấy tên bảng và kết quả, không lộ thông tin đăng nhập. |
| dbt tests | Summary lệnh dbt test và số pass/fail | Tại thư mục dbt chạy dbt test; chụp phần tổng kết terminal, không chỉ dòng lệnh. |
| Airflow pipeline | DAG Graph/Grid và lần chạy thành công | Mở Airflow UI, chọn DAG dự án và run gần nhất có trạng thái thành công; thấy tên DAG, trạng thái và task. |
| So sánh mô hình | Bảng/biểu đồ metrics Phase 30 | Dùng kết quả thật; ghi rõ validation, không gọi là test. |
| API dự đoán | Swagger /docs, POST /predictions và response 201 | Chạy API theo README, mở http://localhost:<API_PORT>/docs, gửi mẫu không nhạy cảm; chụp request và response. |
| Health/monitoring | Endpoint health/monitoring | Gọi endpoint hiện có qua Swagger hoặc trình duyệt; ảnh thấy URL và response thật. |
| Web frontend | Giao diện đang chạy và kết quả thao tác | Chạy frontend theo README/package scripts, mở URL local, thực hiện luồng đã hoàn tất Phase 32 và chụp kết quả. |
| MLflow (nếu chạy được) | Experiment/run, metric, artifact | Chụp run thật. Nếu tracking server không chạy ổn định thì bỏ ảnh và nêu hạn chế. |
| Metabase | Dashboard dùng dữ liệu dự án | Chụp chart thật, thấy tiêu đề, bộ lọc (nếu có), kết quả và giao diện Metabase. |

### Phím chụp màn hình Windows

- **Win + Shift + S**: chọn vùng; lưu từ Snipping Tool hoặc dán vào Paint.
- **Alt + PrtScn**: chụp cửa sổ đang active.
- Dùng PNG, cắt phần thừa nhưng giữ tiêu đề/cửa sổ, URL hoặc trạng thái cần chứng minh.
- Lưu dưới evidence/report_screenshots/ với tên gắn với caption.
- Ghi nguồn dưới ảnh dạng “Nguồn: Kết quả chạy thử của nhóm, ngày …”. Ghi đúng ngày chụp và môi trường local/Docker.

### Điều kiện đưa ảnh vào báo cáo

- Ảnh thể hiện kết quả thật, chữ và trạng thái đọc được.
- Caption mô tả đúng nội dung; số liệu khớp bảng và tài liệu xác minh.
- Sơ đồ Mermaid ghi là “sơ đồ kiến trúc/luồng xử lý”; không gọi là ảnh chụp hoặc kết quả chạy.
- Hình nào chưa có bằng chứng thật thì giữ trong checklist, không thay bằng ảnh AI.
