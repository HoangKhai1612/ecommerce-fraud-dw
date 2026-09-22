# RISK REGISTER

**Dự án:** Ecommerce Fraud Detection Data Warehouse  
**Ngày tạo:** 02/09/2026

> Cập nhật Risk Register sau mỗi phase.  
> Probability: LOW / MEDIUM / HIGH  
> Impact: LOW / MEDIUM / HIGH / CRITICAL

---

| ID | Risk | Probability | Impact | Mitigation | Status | Phase phát hiện |
|----|------|:-----------:|:------:|-----------|:------:|:--------------:|
| R01 | Dataset quá lớn gây RAM/Disk issue | MEDIUM | HIGH | Sampling với stratified fraud ratio (giữ nguyên tỷ lệ fraud) | OPEN | P00 |
| R02 | Airflow + Metabase + Ollama cùng chạy gây OOM | MEDIUM | HIGH | Tắt service không dùng; tăng Docker RAM limit | OPEN | P00 |
| R03 | LLM generate SQL nguy hiểm (DROP/DELETE) | HIGH | CRITICAL | SQL validation layer, whitelist SELECT only | OPEN | P00 |
| R04 | Model không đạt F1 ≥ 0.7 trên fraud class | MEDIUM | MEDIUM | Thử 3 models, SMOTE, tune hyperparameter | OPEN | P00 |
| R05 | dbt model fail do schema không khớp | LOW | MEDIUM | Schema validation trước khi run dbt | OPEN | P00 |
| R06 | Docker port conflict | LOW | LOW | Document port map, dùng port cố định | OPEN | P00 |
| R07 | Kaggle dataset bị xóa/không accessible | LOW | HIGH | Dataset đã có sẵn trong data/raw/ | MITIGATED | P00 |
| R08 | Data leakage trong ML pipeline | MEDIUM | HIGH | Strict train/val/test split; kiểm tra future data | OPEN | P00 |
| R09 | Thời gian không đủ để hoàn thiện | MEDIUM | HIGH | Ưu tiên core scope; extension sau | OPEN | P00 |
| R10 | PostgreSQL encoding issue với CSV | LOW | MEDIUM | Specify encoding='utf-8' trong ingestion | OPEN | P00 |
| R11 | Airflow DAG import error | MEDIUM | MEDIUM | Test DAG locally trước khi deploy | OPEN | P00 |
| R12 | dbt test fail block pipeline | MEDIUM | MEDIUM | Severity levels, warn vs error | OPEN | P00 |
| R13 | Missing values quá nhiều trong features | HIGH | MEDIUM | Imputation strategy, feature selection | OPEN | P00 |
| R14 | SHAP chậm trên dataset lớn | MEDIUM | LOW | Sample 1000-5000 rows cho SHAP viz | OPEN | P00 |
| R15 | Metabase không connect được PostgreSQL | LOW | MEDIUM | Test connection trước, verify credentials | OPEN | P00 |

---

## RISK DETAIL

### R03 — LLM SQL Injection Risk (CRITICAL)
```
Problem: LLM có thể generate câu SQL nguy hiểm như:
  DROP TABLE facts;
  DELETE FROM predictions;
  UPDATE transactions SET isFraud = 0;

Prevention:
  1. Read-only PostgreSQL user cho AI Assistant
  2. SQL Parser để check statement type
  3. Whitelist: chỉ cho phép SELECT
  4. Blacklist keywords: DROP, DELETE, UPDATE, INSERT, ALTER, TRUNCATE, CREATE
  5. Query timeout: 30 seconds
  6. Result limit: 1000 rows
  7. Schema restriction: chỉ được query marts schema
```

### R08 — Data Leakage (HIGH)
```
Problem: Nếu train set chứa thông tin từ future,
model sẽ "overfitting" và fail trên real data.

Prevention:
  1. Split theo thời gian (time-based split) nếu có timestamp
  2. Hoặc random split 70/15/15 với stratify=isFraud
  3. Không dùng features được tính từ test set
  4. Fit scaler/encoder chỉ trên train set
  5. Kiểm tra correlation bất thường giữa feature và label
```

### R01 — Dataset Size (HIGH)
```
Dataset IEEE-CIS:
  train_transaction.csv: ~590K rows × 394 cols
  train_identity.csv: ~144K rows × 41 cols

Potential issues:
  - pandas read_csv dùng nhiều RAM (~2-4GB)
  - PostgreSQL COPY chậm nếu không optimize
  - dbt models chậm nếu không có index

Mitigation:
  1. Đọc theo chunks: pd.read_csv(chunksize=10000)
  2. Tạo index trên TransactionID, isFraud
  3. Nếu RAM < 8GB: sample 20% với stratify=isFraud
```

---

## RISK HISTORY (Đã đóng)

| ID | Risk | Resolution | Date Closed |
|----|------|-----------|-------------|
| R07 | Dataset không accessible | Dataset đã có trong data/raw/ | 02/09/2026 |

---

*Cập nhật: 02/09/2026 | Version: 1.0*
