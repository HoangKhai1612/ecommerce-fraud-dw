# ASSUMPTIONS

**Dự án:** Ecommerce Fraud Detection Data Warehouse  
**Ngày tạo:** 02/09/2026  
**Ngày verify:** 02/09/2026

---

## ASSUMPTIONS ĐÃ VERIFY ✅

| ID | Assumption | Kết quả Verify | Date |
|----|-----------|---------------|------|
| A01 | Dataset IEEE-CIS tồn tại và đọc được | ✅ CONFIRMED — 5 files, đọc OK | 02/09/2026 |
| A07 | Git đã cài | ✅ CONFIRMED — Có .git folder | 02/09/2026 |

---

## ASSUMPTIONS CHƯA VERIFY ⏳

| ID | Assumption | Cách Verify | Risk nếu sai |
|----|-----------|------------|-------------|
| A02 | Python 3.10+ đã cài | `python --version` | Cần cài lại |
| A03 | Docker / Docker Compose | `docker --version` | Cần cài |
| A04 | RAM ≥ 8GB | Task Manager | Phải optimize |
| A05 | LLM: Ollama local hoặc API | Confirm với SV | Phải chọn approach |
| A06 | Internet access | Test pip install | Offline cache |

---

## ASSUMPTIONS ĐẶC THÙ DỰ ÁN

### Về Dataset
```
- train_transaction.csv: 590,540 rows × 394 cols — ĐÃ CONFIRM
- train_identity.csv: ~144,233 rows × 41 cols — ĐÃ CONFIRM
- isFraud ratio: ~94.2% Non-Fraud / 5.8% Fraud (IMBALANCED)
- Chỉ dùng train_* files (test_* không có label)
- Nếu RAM < 8GB: sample 30% với stratify=isFraud
```

### Về Data Warehouse
```
- PostgreSQL chạy trên Docker container
- Schema structure: raw | staging | marts
- Surrogate key sẽ dùng SERIAL hoặc GENERATED ALWAYS AS IDENTITY
- Không implement SCD Type 2 (không cần cho đồ án này)
```

### Về Machine Learning
```
- Split: 70% train / 15% validation / 15% test
- Stratify theo isFraud
- Fit scaler/encoder CHỈ trên train set
- Metric ưu tiên: F1-score (fraud class), PR-AUC
- Không dùng accuracy làm metric chính
```

### Về AI Assistant
```
- LLM có thể là Ollama (local) hoặc API-based
- Default assumption: Ollama với model llama3 hoặc mistral
- Nếu không đủ RAM: dùng OpenAI API (cần set OPENAI_API_KEY trong .env)
- AI chỉ được SELECT — phải có SQL validation
```

### Về Docker
```
- Docker Desktop đã hoặc sẽ cài trước Phase 03
- Ports mặc định:
  PostgreSQL: 5432
  Airflow: 8080
  Metabase: 3000
  API: 8000
  Ollama: 11434
```

---

## ASSUMPTION VIOLATIONS (Nếu xảy ra)

| Assumption | Violation scenario | Action |
|-----------|-------------------|--------|
| RAM ≥ 8GB | RAM < 8GB | Sample dataset 30%, tắt service không dùng |
| Ollama local | GPU/RAM không đủ | Chuyển sang OpenAI API |
| PostgreSQL port 5432 free | Port bị chiếm | Change port trong .env |

---

*Cập nhật: 02/09/2026 | Version: 1.0*
