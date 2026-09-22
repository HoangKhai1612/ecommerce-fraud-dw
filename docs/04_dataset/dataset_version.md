# DATASET VERSION

**Nguồn:** IEEE-CIS Fraud Detection  
**Ngày tạo:** 02/09/2026  

---

## 1. VERSION INFO

| Thuộng số | Giá trị |
|----------|---------|
| Dataset name | IEEE-CIS Fraud Detection |
| Version | 1.0 (Kaggle original) |
| Download date | Trước 02/09/2026 |
| Source | Kaggle competition (CC0 license) |
| Local path | `data/raw/` |
| File count | 5 files |

---

## 2. FILES & CHECKSUMS

| File | Size | Rows | Columns | MD5 (approx) |
|------|------|------|---------|--------------|
| `train_transaction.csv` | 653 MB | 590,540 | 394 | N/A |
| `train_identity.csv` | 26 MB | 144,233 | 41 | N/A |
| `test_transaction.csv` | 585 MB | ~506,691 | 393 | N/A |
| `test_identity.csv` | 25 MB | ~146,133 | 41 | N/A |
| `sample_submission.csv` | 6 MB | 506,691 | 2 | N/A |

> **Checksum note:** MD5 chưa được tính do file lớn. Sẽ thêm sau nếu cần.

---

## 3. VERSION CONTROL STRATEGY

### Dataset được version như sau:

| Version | Date | Changes | Notes |
|---------|------|---------|-------|
| v1.0 | 02/09/2026 | Initial dataset (Kaggle original) | Files in data/raw/ |

### Dataset không được commit vào Git

Dòng `.gitignore` chặn:
```
data/raw/*.csv
```

### Cách chia sẻ dataset:
1. Dataset được lưu trữ cục bộ trong `data/raw/`
2. Không đẩy lên GitHub
3. Khi cần chia sẻ: hướng dẫn tải lại từ Kaggle

---

## 4. DATASET IN PIPELINE

### Sử dụng trong các phases:

| Phase | Sử dụng dataset nào? |
|-------|-----------------------|
| P09 (Ingestion) | `train_transaction.csv`, `train_identity.csv` |
| P10 (RAW) | `train_transaction.csv`, `train_identity.csv` |
| P11-P14 (Staging, dbt, Airflow, Quality) | RAW tables |
| P15-P17 (ML) | RAW tables (sample nếu cần) |
| P18-P19 (SHAP, Integration) | ML results |
| P20-P22 (Dashboard, API, AI) | DW tables |
| P24 (E2E) | All |

### Files không sử dụng:
- `test_transaction.csv` — không có nhãn `isFraud`
- `test_identity.csv` — không có nhãn
- `sample_submission.csv` — chỉ dùng để format submission

---

## 5. DATA PROVENANCE

```text
Kaggle (CC0)
    ↓
Download ZIP (~768MB)
    ↓
Extract to data/raw/
    ↓
Verify with: python -c "import pandas as pd; pd.read_csv('data/raw/train_transaction.csv', nrows=5)"
    ↓
Load to PostgreSQL RAW layer (ingestion/load_raw.py)
    ↓
RAW layer becomes single source of truth for pipeline
```

---

## 6. DATA UPDATE POLICY

- **Dataset này là STATIC** — không cập nhật trong suốt dự án
- Không có data versioning (DVC, Delta Lake) — nằm ngoài scope
- Nếu dataset thay đổi: cập nhật version ở đây

*Cập nhật: 02/09/2026 | Version: 1.0*
