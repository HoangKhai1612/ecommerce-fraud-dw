# DECISION LOG

**Dự án:** Ecommerce Fraud Detection Data Warehouse  
**Ngày tạo:** 02/09/2026

> Mọi quyết định kỹ thuật quan trọng phải được ghi vào đây.  
> Không xóa quyết định cũ — chỉ cập nhật trạng thái.

---

## TEMPLATE

```markdown
### DEC-XXX — [Tên quyết định]

- **Date:** DD/MM/YYYY
- **Phase:** PHASE XX
- **Context:** [Bối cảnh tại sao phải đưa ra quyết định này]
- **Problem:** [Vấn đề cần giải quyết]
- **Options:**
  - Option A: ...
  - Option B: ...
  - Option C: ...
- **Decision:** Option X
- **Reason:** [Lý do chọn]
- **Trade-offs:** [Những gì phải hy sinh]
- **Impact:** [Ảnh hưởng đến hệ thống]
- **Status:** APPROVED / PENDING / SUPERSEDED
```

---

## DECISIONS

### DEC-001 — Chọn PostgreSQL làm Database chính

- **Date:** 02/09/2026
- **Phase:** PHASE 00
- **Context:** Cần RDBMS để lưu RAW, STAGING và Data Warehouse
- **Problem:** Chọn database nào phù hợp nhất?
- **Options:**
  - Option A: PostgreSQL
  - Option B: MySQL
  - Option C: SQLite
- **Decision:** PostgreSQL
- **Reason:** Đề cương quy định rõ ràng. PostgreSQL mạnh về analytical queries, hỗ trợ nhiều kiểu dữ liệu, dbt tích hợp tốt, có nhiều tài liệu
- **Trade-offs:** Nặng hơn SQLite, cần Docker container
- **Impact:** Tất cả SQL phải viết theo PostgreSQL dialect
- **Status:** APPROVED (theo đề cương)

---

### DEC-002 — Chọn Apache Airflow làm Orchestration

- **Date:** 02/09/2026
- **Phase:** PHASE 00
- **Context:** Cần tool để tự động hóa và schedule pipeline
- **Problem:** Chọn workflow orchestrator nào?
- **Options:**
  - Option A: Apache Airflow
  - Option B: Prefect
  - Option C: Cron job đơn giản
- **Decision:** Apache Airflow
- **Reason:** Đề cương quy định. Industry standard, có UI để monitor, hỗ trợ DAG, retry, alerting
- **Trade-offs:** Nặng hơn Prefect, khó setup hơn cron
- **Impact:** Cần Docker container riêng cho Airflow
- **Status:** APPROVED (theo đề cương)

---

### DEC-003 — Chọn dbt Core (không phải dbt Cloud)

- **Date:** 02/09/2026
- **Phase:** PHASE 00
- **Context:** Cần tool để transformation và data testing
- **Problem:** dbt Core vs dbt Cloud?
- **Options:**
  - Option A: dbt Core (open-source, local)
  - Option B: dbt Cloud (SaaS, cần account)
- **Decision:** dbt Core
- **Reason:** Free, local, đủ cho quy mô đồ án, không cần internet để chạy
- **Trade-offs:** Không có dbt Cloud UI đẹp, nhưng có `dbt docs serve` thay thế
- **Impact:** Cài dbt-core via pip, connect thẳng vào PostgreSQL
- **Status:** APPROVED

---

### DEC-004 — Chọn Metabase làm BI Dashboard

- **Date:** 02/09/2026
- **Phase:** PHASE 00
- **Context:** Cần dashboard tool để visualize dữ liệu DW
- **Problem:** Chọn BI tool nào?
- **Options:**
  - Option A: Metabase (open-source)
  - Option B: Apache Superset
  - Option C: Grafana
  - Option D: Power BI
- **Decision:** Metabase
- **Reason:** Đề cương quy định. Dễ cài qua Docker, giao diện thân thiện, connect tốt với PostgreSQL
- **Trade-offs:** Ít customizable hơn Superset, nhưng đủ dùng
- **Impact:** Cần Docker container, port 3000
- **Status:** APPROVED (theo đề cương)

---

### DEC-005 — Chọn FastAPI làm API Framework

- **Date:** 02/09/2026
- **Phase:** PHASE 00
- **Context:** Cần REST API framework cho Python
- **Problem:** Chọn framework nào?
- **Options:**
  - Option A: FastAPI
  - Option B: Flask
  - Option C: Django REST Framework
- **Decision:** FastAPI
- **Reason:** Đề cương quy định. Modern, async, tự động sinh API docs, type hints, validation
- **Trade-offs:** Learning curve hơn Flask một chút
- **Impact:** API code trong `api/` folder
- **Status:** APPROVED (theo đề cương)

---

### DEC-006 — Chọn SHAP cho Explainable AI

- **Date:** 02/09/2026
- **Phase:** PHASE 00
- **Context:** Cần giải thích kết quả ML model
- **Problem:** Chọn XAI method nào?
- **Options:**
  - Option A: SHAP
  - Option B: LIME
  - Option C: Feature Importance đơn giản
- **Decision:** SHAP
- **Reason:** Đề cương quy định. SHAP là standard industry tool, có visualizations đẹp, hỗ trợ tốt cho XGBoost và RF
- **Trade-offs:** Chậm hơn Feature Importance, nhưng chính xác hơn
- **Impact:** Phải install `shap` library
- **Status:** APPROVED (theo đề cương)

---

### DEC-007 — Dataset: IEEE-CIS Fraud Detection

- **Date:** 02/09/2026
- **Phase:** PHASE 00
- **Context:** Cần dataset để train fraud detection model
- **Problem:** Chọn dataset nào?
- **Options:**
  - Option A: IEEE-CIS Fraud Detection (Kaggle)
  - Option B: Credit Card Fraud Detection (Kaggle)
  - Option C: PaySim synthetic dataset
- **Decision:** IEEE-CIS Fraud Detection
- **Reason:** Đề cương ưu tiên dataset này. Có đặc trưng e-commerce thực tế, gồm 2 file (transaction + identity), nhiều features đa dạng, dataset công khai cho nghiên cứu
- **Trade-offs:** Lớn (590K rows, 433 columns), nhiều missing values
- **Impact:** Ingestion cần xử lý join giữa transaction và identity
- **Status:** APPROVED (theo đề cương)

---

*Cập nhật: 02/09/2026 | Version: 1.0*
