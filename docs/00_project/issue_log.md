# ISSUE LOG

**Dự án:** Ecommerce Fraud Detection Data Warehouse  
**Ngày tạo:** 02/09/2026

> Ghi lại TẤT CẢ lỗi gặp phải trong quá trình thực hiện.  
> Không xóa issue — chỉ cập nhật status.  
> Lỗi là bằng chứng của quá trình học thực tế.

---

## TEMPLATE

```markdown
### ISS-XXX — [Tên issue]

- **Date:** DD/MM/YYYY
- **Phase:** PHASE XX
- **Severity:** CRITICAL / HIGH / MEDIUM / LOW
- **Status:** OPEN / IN_PROGRESS / RESOLVED / WONT_FIX
- **Symptoms:** [Biểu hiện lỗi]
- **Root Cause:** [Nguyên nhân gốc rễ]
- **Fix Applied:** [Cách sửa]
- **Test:** [Cách verify đã fix]
- **Prevention:** [Cách ngăn chặn lần sau]
```

---

### ISS-002 — dbt schema concatenation (target_schema + custom_schema)

- **Date:** 02/09/2026
- **Phase:** PHASE 11
- **Severity:** MEDIUM
- **Status:** RESOLVED
- **Symptoms:** dbt tạo schema `raw_staging` (và sau đó `_staging`) thay vì `staging` do macro `default__generate_schema_name` nối target.schema với custom schema
- **Root Cause:** dbt-postgres default macro concatenates `target.schema` + `_` + `custom_schema_name`
- **Fix Applied:** Tạo macro override `default__generate_schema_name` trong `dbt/macros/schema_override.sql` để trả về `custom_schema_name` trực tiếp
- **Test:** dbt run thành công, views được tạo trong schema `staging`
- **Prevention:** Include schema_override macro trong mọi dbt project

### ISS-003 — protobuf incompatible with Python 3.14

- **Date:** 02/09/2026
- **Phase:** PHASE 11
- **Severity:** HIGH
- **Status:** RESOLVED
- **Symptoms:** `TypeError: Metaclasses with custom tp_new are not supported` khi chạy dbt
- **Root Cause:** dbt-core 1.8.0 requires protobuf<5, nhưng protobuf 4.25.x không tương thích với Python 3.14
- **Fix Applied:** `pip install --upgrade protobuf` lên phiên bản 7.36.1
- **Test:** `dbt debug` và `dbt run` thành công
- **Prevention:** Pin protobuf version trong requirements.txt

---

## RESOLVED ISSUES

### ISS-001 — Docker port 5432 conflict với PostgreSQL local

- **Date:** 02/09/2026
- **Phase:** PHASE 09
- **Severity:** HIGH
- **Status:** RESOLVED
- **Symptoms:** `psycopg2.OperationalError: connection to server at "localhost" (::1), port 5432 failed: FATAL: password authentication failed for user "postgres"`
- **Root Cause:** Có PostgreSQL local (PID 8024) đang chạy trên máy Windows, chiếm cùng port 5432 với Docker container. Khi kết nối qua localhost, kết nối đến PostgreSQL local (password khác) thay vì Docker container.
- **Fix Applied:** Dừng PostgreSQL local bằng `taskkill /PID 8024 /F`
- **Test:** Kết nối lại bằng Python SQLAlchemy — thành công
- **Prevention:** Document trong `docs/03_environment/troubleshooting.md`. Trong tương lai, có thể đổi port PostgreSQL trong docker-compose.yml nếu conflict.

---

## ISSUE STATISTICS

| Phase | Total | Critical | High | Medium | Low | Resolved |
|-------|-------|---------|------|--------|-----|---------|
| P00 | 0 | 0 | 0 | 0 | 0 | 0 |
| P09 | 1 | 0 | 1 | 0 | 0 | 1 |
| P11 | 2 | 0 | 1 | 1 | 0 | 2 |

---

*Cập nhật: 02/09/2026 | Version: 1.0*
