# PROJECT CONSTRAINTS & ASSUMPTIONS

**Ngày tạo:** 02/09/2026

---

## PHẦN A: CONSTRAINTS (Ràng buộc)

### C01 — Technology Stack cố định
- **Constraint:** Phải dùng đúng các công nghệ đề cương quy định
- **Impact:** Không được tự ý thay PostgreSQL bằng MySQL, Airflow bằng Prefect...
- **Mitigation:** Luôn kiểm tra đề cương trước khi chọn tool mới

### C02 — Phạm vi Machine Learning
- **Constraint:** Chỉ dùng LR, RF, XGBoost — không dùng Deep Learning
- **Impact:** Không được thêm Neural Network, LSTM...
- **Mitigation:** Extension backlog nếu muốn thêm

### C03 — AI Assistant phải Read-only
- **Constraint:** AI chỉ được phép thực thi SELECT queries
- **Impact:** Phải có SQL validation layer chặn DROP/DELETE/UPDATE/INSERT
- **Mitigation:** Whitelist-based SQL validator

### C04 — Local Deployment only
- **Constraint:** Không deploy lên cloud
- **Impact:** Không cần AWS/GCP/Azure account
- **Mitigation:** Docker Compose cho local environment

### C05 — Dữ liệu nghiên cứu
- **Constraint:** Không sử dụng dữ liệu cá nhân thực tế
- **Impact:** Chỉ dùng IEEE-CIS public dataset
- **Mitigation:** Dataset đã có sẵn trong data/raw/

### C06 — Thời hạn
- **Constraint:** Hoàn thành trước 25/10/2026
- **Impact:** Phải ưu tiên core scope trước extension
- **Mitigation:** Gate system, milestone tracking

### C07 — Không commit secret
- **Constraint:** Không được commit password, API key, credentials vào Git
- **Impact:** Phải dùng .env file và .gitignore
- **Mitigation:** .env.example với placeholder values

### C08 — Phạm vi báo cáo
- **Constraint:** Báo cáo phải bám theo cấu trúc 4 chương đề cương
- **Impact:** Mỗi phase phải map ra chapter tương ứng
- **Mitigation:** Traceability matrix luôn được cập nhật

---

## PHẦN B: ASSUMPTIONS (Giả định)

### A01 — Dataset
- **Assumption:** Dataset IEEE-CIS trong `data/raw/` hợp lệ và đọc được
- **Verify:** Chạy `python -c "import pandas as pd; df=pd.read_csv('data/raw/train_transaction.csv', nrows=5); print(df.shape)"` để confirm
- **Fallback:** Nếu lỗi encoding → thêm `encoding='utf-8'` hoặc `latin-1`

### A02 — Python Environment
- **Assumption:** Python 3.10+ đã cài và available trên PATH
- **Verify:** `python --version`
- **Fallback:** Cài Python từ python.org

### A03 — Docker
- **Assumption:** Docker Desktop đã hoặc sẽ được cài
- **Verify:** `docker --version`
- **Fallback:** Cài Docker Desktop cho Windows

### A04 — Hardware
- **Assumption:** RAM ≥ 8GB để chạy PostgreSQL + Airflow + Metabase
- **Impact nếu sai:** Phải tắt Metabase hoặc Airflow khi không dùng
- **Fallback:** Chạy từng service, không chạy cùng lúc

### A05 — LLM
- **Assumption:** Sử dụng Ollama (local) với model llama3 hoặc mistral
- **Impact nếu sai:** Chuyển sang OpenAI/Gemini API (cần key)
- **Fallback:** Cấu hình trong .env

### A06 — Internet Access
- **Assumption:** Có internet để tải Docker images, Python packages
- **Impact nếu sai:** Pre-download packages vào requirements.txt
- **Fallback:** Offline pip install từ local cache

### A07 — Git đã cài
- **Assumption:** Git đã cài và configured với username/email
- **Verify:** `git --version`
- **Fallback:** Cài Git for Windows

---

## PHẦN C: DEPENDENCIES (Phụ thuộc)

### Internal Dependencies

```
Dataset → Ingestion → RAW → STAGING → dbt → DW → ML
                                                  ↓
                                           Dashboard
                                           API
                                           AI Assistant
```

### External Dependencies

| Phụ thuộc | Mục đích | Risk |
|-----------|---------|------|
| Kaggle / IEEE-CIS dataset | Input data | LOW (đã có) |
| PyPI packages | Python libs | LOW (internet needed) |
| Docker Hub images | Airflow, Metabase | MEDIUM (size lớn) |
| Ollama models | LLM local | MEDIUM (cần download) |

---

*Cập nhật: 02/09/2026 | Version: 1.0*
