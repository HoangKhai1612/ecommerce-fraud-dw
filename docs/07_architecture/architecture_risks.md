# ARCHITECTURE RISKS

**Dự án:** Ecommerce Fraud Detection Data Warehouse  
**Phase:** 07 — System Architecture  
**Ngày tạo:** 02/09/2026  

---

## 1. ARCHITECTURE RISK TABLE

| ID | Risk | Probability | Impact | Mitigation | Status |
|----|------|-------------|--------|------------|--------|
| AR-01 | Dataset quá lớn gây OOM | MEDIUM | HIGH | Chunked loading, sampling nếu RAM < 8GB | OPEN |
| AR-02 | Airflow + Metabase + Ollama cùng chạy OOM | HIGH | HIGH | Tắt service không dùng, tăng Docker RAM | OPEN |
| AR-03 | PostgreSQL schema mismatch với dbt models | MEDIUM | MEDIUM | Validation trước khi run dbt | OPEN |
| AR-04 | SHAP chạm timeout trên full dataset | HIGH | LOW | Chỉ chạy SHAP trên sample 5000 rows | OPEN |
| AR-05 | LLM sinh SQL nguy hiểm | HIGH | CRITICAL | Read-only user + SQL validator | OPEN |
| AR-06 | Data leakage trong ML split | MEDIUM | HIGH | Strict split, impute chỉ trên train | OPEN |
| AR-07 | dbt model dependency chain quá dài | LOW | MEDIUM | Modularize models, test từng phần | OPEN |
| AR-08 | Metabase không connect được PostgreSQL | LOW | MEDIUM | Test connection trước | OPEN |
| AR-09 | Ollama model download thất bại | LOW | MEDIUM | Fallback sang OpenAI API | OPEN |
| AR-10 | Docker port conflict | LOW | LOW | Document port mapping, dùng port cố định | OPEN |

---

## 2. RISK DETAILS

### AR-01: Dataset Size (590K rows × 394 cols)
**Problem:** File train_transaction.csv ~653MB, đọc toàn bộ có thể dùng ~4GB RAM.

**Mitigation:**
- Ingestion script đã sử dụng `chunksize=50000`
- dbt chỉ chạy transform, không load toàn bộ vào memory
- ML có thể sample nếu cần

**Evidence needed:** RAM usage khi chạy ingestion script.

### AR-02: Multi-service OOM
**Problem:** Docker chạy PostgreSQL + Airflow (2 containers) + Metabase + Ollama — có thể vượt quá RAM.

**Mitigation:**
- Cấu hình `mem_limit` trong docker-compose
- Tắt Metabase/Ollama khi không dùng
- Chỉ chạy PostgreSQL + Airflow trong dev phase

**Evidence needed:** `docker stats` output.

### AR-05: LLM SQL Injection (CRITICAL)
**Problem:** Ollama/LLM có thể sinh câu SQL như `DROP TABLE`, `DELETE FROM`.

**Mitigation (3 layers):**
1. **Read-only PostgreSQL user** (`ai_assistant_ro`) — không có quyền DROP/DELETE
2. **SQL Validator** — parse SQL, chặn mọi non-SELECT statements
3. **Query timeout** + **result limit** (30s, 1000 rows)

**Evidence needed:** Test với prompt độc hại.

### AR-06: Data Leakage
**Problem:** Nếu imputation/scaler fit trên full dataset → model "thấy" test data.

**Mitigation:**
- Split train/val/test TRƯỚC khi preprocessing
- Fit scaler/encoder CHỈ trên train set
- Apply transform trên val/test

**Evidence needed:** Code review ml/prepare_data.py.

*Cập nhật: 02/09/2026 | Version: 1.0*
