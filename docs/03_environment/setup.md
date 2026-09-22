# ENVIRONMENT SETUP & VERIFICATION

**Dự án:** Ecommerce Fraud Detection Data Warehouse  
**Phase:** 03 — Environment Setup  
**Ngày tạo:** 02/09/2026

---

## 1. DANH SÁCH CÔNG CỤ HỆ THỐNG (SYSTEM TOOLS)

| Tool | Required Version | Installed Version | Status |
|------|------------------|-------------------|--------|
| **Python** | ≥ 3.10 | 3.14.0 | ✅ PASS |
| **Docker** | ≥ 25.0 | 29.6.2 | ✅ PASS |
| **Docker Compose** | ≥ 2.0 | 5.3.1 | ✅ PASS |
| **Git** | ≥ 2.0 | Not in PATH | ⚠️ CLI Pending |

---

## 2. FILE CẤU HÌNH & QUẢN LÝ THƯ VIỆN

1. **`requirements.txt`**: Khai báo danh sách các thư viện Python (pandas, psycopg2, sqlalchemy, dbt-core, scikit-learn, xgboost, shap, fastapi, pydantic, pytest...).
2. **`.env` / `.env.example`**: Quản lý biến môi trường kết nối PostgreSQL, Airflow, FastAPI, Metabase, LLM Provider.
3. **`.gitignore`**: Chặn commit các file nhạy cảm, dataset lớn (`.csv`), file môi trường (`.env`), virtualenv (`.venv`).

---

## 3. HƯỚNG DẪN KÍCH HOẠT VIRTUAL ENVIRONMENT & CÀI ĐẶT

```bash
# 1. Tạo Virtual Environment
python -m venv .venv

# 2. Kích hoạt Virtual Environment (Windows PowerShell)
.\.venv\Scripts\Activate.ps1

# 3. Cài đặt các thư viện phụ thuộc
pip install -r requirements.txt
```
