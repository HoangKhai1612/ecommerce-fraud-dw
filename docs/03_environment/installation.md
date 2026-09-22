# INSTALLATION GUIDE

**Dự án:** Ecommerce Fraud Detection Data Warehouse  
**Phase:** 03 — Environment Setup  
**Ngày tạo:** 02/09/2026  

---

## 1. MỤC TIÊU

Hướng dẫn cài đặt môi trường phát triển từ A-Z cho dự án Data Warehouse + Fraud Detection.

---

## 2. CHECKLIST CÔNG CỤ

| Tool | Cài đặt | Verify command |
|------|--------|----------------|
| [x] Python 3.10+ | [python.org](https://www.python.org/downloads/) | `python --version` |
| [x] PostgreSQL 15+ | [postgresql.org](https://www.postgresql.org/download/) hoặc Docker | `psql --version` hoặc `docker ps` |
| [ ] Docker Desktop 25+ | [docker.com](https://www.docker.com/products/docker-desktop) | `docker --version` |
| [ ] Git 2.x | [git-scm.com](https://git-scm.com/) | `git --version` |
| [ ] VS Code | [code.visualstudio.com](https://code.visualstudio.com/) | `code --version` |

---

## 3. CÀI ĐẶT PYTHON

### Windows:
1. Tải Python 3.10+ từ [python.org](https://www.python.org/downloads/)
2. Chạy installer, **chọn "Add Python to PATH"**
3. Mở PowerShell, kiểm tra: `python --version`

### Tạo virtual environment:
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

---

## 4. CÀI ĐẶT PYTHON PACKAGES

```powershell
# Kích hoạt venv
.venv\Scripts\Activate.ps1

# Cài đặt
pip install -r requirements.txt

# Kiểm tra
pip list
```

---

## 5. CÀI ĐẬT DOCKER DESKTOP (Windows)

1. Tải Docker Desktop từ [docker.com](https://www.docker.com/products/docker-desktop)
2. Chạy installer
3. Khởi động Docker Desktop
4. Kiểm tra: `docker --version`

---

## 6. CÀI ĐẶT GIT

1. Tải từ [git-scm.com](https://git-scm.com/download/win)
2. Chạy installer với mặc định
3. Cấu hình:
```bash
git config --global user.name "Hoàng Quốc Khải"
git config --global user.email "student@university.edu"
```
4. Kiểm tra: `git --version`

---

## 7. CÀI ĐẶT POSTGRESQL (qua Docker)

```powershell
docker compose up -d postgres
```

Hoặc cài trực tiếp:
1. Tải từ [postgresql.org](https://www.postgresql.org/download/windows/)
2. Chạy installer, ghi nhớ password
3. Cài đặt port 5432

---

## 8. CÀI ĐẶT AIRFLOW (qua Docker)

```yaml
# Trong docker-compose.yml (sẽ thêm service airflow-webserver, airflow-scheduler, airflow-postgres)
```

Xem chi tiết ở `docs/23_docker/`.

---

## 9. CÀI ĐẶT METABASE (qua Docker)

```yaml
# Trong docker-compose.yml (sẽ thêm service metabase)
```

---

## 10. CÀI ĐẶT OLLAMA (cho AI Assistant)

1. Tải từ [ollama.com](https://ollama.com/download)
2. Cài đặt và chạy
3. Tải model: `ollama pull llama3`

---

## TÀI LIỆU THAM KHẢO

- Python: https://docs.python.org/3/
- PostgreSQL: https://www.postgresql.org/docs/
- Docker: https://docs.docker.com/
- Git: https://git-scm.com/doc
- Airflow: https://airflow.apache.org/docs/

*Cập nhật: 02/09/2026 | Version: 1.0*
