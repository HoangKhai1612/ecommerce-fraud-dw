# DEFINITION OF DONE

**Dự án:** Ecommerce Fraud Detection Data Warehouse  
**Ngày tạo:** 02/09/2026

> DoD là tiêu chuẩn để xác định một task/phase thực sự HOÀN THÀNH.  
> **KHÔNG được gọi là "done" nếu chưa đạt đủ tiêu chí.**

---

## 1. DEFINITION OF DONE — TASK LEVEL

Một task chỉ được đánh dấu ✅ DONE khi:

```
[ ] Objective đã đạt được (không chỉ "code xong")
[ ] Code đã được implement đúng
[ ] Code có logging (biết khi nào chạy, khi nào fail)
[ ] Code có error handling (không crash mà không báo lỗi)
[ ] Code đã được chạy ít nhất 1 lần thành công
[ ] Test đã viết và đã PASS
[ ] Evidence đã lưu (screenshot / log / SQL result)
[ ] Không có CRITICAL issue chưa giải quyết
[ ] File đã được git commit
```

---

## 2. DEFINITION OF DONE — PHASE LEVEL

Một phase chỉ được đánh dấu ✅ PASS khi:

```
[ ] Tất cả tasks trong phase đã DONE
[ ] Phase documentation đã viết
[ ] Test results đã documented
[ ] Evidence đã lưu trong evidence/ folder
[ ] Failure cases đã xem xét
[ ] Report section tương ứng đã cập nhật
[ ] Decision log đã cập nhật (nếu có quyết định)
[ ] Risk register đã review (nếu phát hiện risk mới)
[ ] Issue log đã cập nhật (nếu có lỗi)
[ ] Gate checkpoint đã PASS
```

---

## 3. DEFINITION OF DONE — COMPONENT LEVEL

### Data Pipeline (P09 → P14)
```
[ ] Ingestion: CSV → PostgreSQL, row count đúng, không mất data
[ ] RAW: Table tồn tại, schema đúng, không biến đổi nghiệp vụ
[ ] STAGING: Rename đúng, type cast đúng, null handling đúng
[ ] dbt: dbt run PASS, dbt test PASS, dbt docs generate OK
[ ] Airflow: DAG load OK, 8+ tasks, tất cả SUCCESS
[ ] Data Quality: ≥10 tests, 0 critical failure
```

### Machine Learning (P15 → P19)
```
[ ] EDA: Phân tích fraud ratio, missing values, distributions
[ ] Feature Engineering: Features documented, no leakage
[ ] 3 models trained: LR, RF, XGBoost
[ ] Metrics: Precision, Recall, F1, ROC-AUC, PR-AUC cho cả 3
[ ] Comparison table tồn tại
[ ] Best model selected với lý do rõ ràng
[ ] Model artifact saved (.pkl hoặc .joblib)
[ ] SHAP explanation generated
[ ] Predictions saved vào DW
```

### API (P21)
```
[ ] /api/health endpoint hoạt động
[ ] /api/predict endpoint hoạt động với valid input
[ ] /api/predict trả về error đúng với invalid input
[ ] Swagger docs accessible tại /docs
[ ] Unit tests PASS
[ ] Integration test với DW PASS
```

### AI Assistant (P22)
```
[ ] NL câu hỏi → SQL được generate
[ ] SQL Validation chặn DROP/DELETE/UPDATE/INSERT
[ ] SELECT queries thực thi được trên DW (read-only user)
[ ] Kết quả được trả về dạng NL
[ ] Test với ≥5 câu hỏi mẫu, ≥80% đúng
[ ] Không có SQL injection risk
```

### Dashboard (P20)
```
[ ] Metabase kết nối được PostgreSQL DW
[ ] ≥5 KPI charts/visualizations
[ ] Dữ liệu hiển thị đúng với SQL queries
[ ] Mỗi chart có tên và mô tả rõ ràng
```

### Docker (P23)
```
[ ] docker compose up thành công
[ ] Tất cả services: healthy
[ ] Services có thể communicate với nhau
[ ] .env.example đã có với tất cả variables cần thiết
[ ] README hướng dẫn đủ để người khác setup
```

---

## 4. DEFINITION OF DONE — PROJECT LEVEL

Dự án chỉ được tuyên bố HOÀN THÀNH khi:

### ✅ Functional
```
[ ] End-to-end pipeline chạy được (P24)
[ ] Dashboard hiển thị đúng dữ liệu
[ ] API respond đúng
[ ] AI Assistant trả lời câu hỏi nghiệp vụ
[ ] Docker Compose up thành công
```

### ✅ Quality
```
[ ] Tất cả dbt tests PASS
[ ] Tất cả pytest tests PASS
[ ] Không có CRITICAL / HIGH issue chưa resolved
[ ] Data lineage documented (dbt docs)
```

### ✅ Documentation
```
[ ] README đầy đủ và có thể reproduce
[ ] Toàn bộ docs/ structure đã viết
[ ] Báo cáo 4 chương hoàn chỉnh
[ ] Evidence folder có đủ bằng chứng
```

### ✅ Demo
```
[ ] Demo script đã chuẩn bị
[ ] Demo chạy ổn định (không crash)
[ ] Có thể giải thích từng thành phần
[ ] Slide/presentation sẵn sàng
```

---

## 5. TRẠNG THÁI TASKS

```
NOT_STARTED   — Chưa bắt đầu
IN_PROGRESS   — Đang làm
BLOCKED       — Bị block bởi dependency khác
FAILED        — Thất bại, cần debug
PARTIAL       — Làm được một phần, chưa đủ DoD
PASSED        ✅ — Đạt tất cả tiêu chí DoD
SKIPPED       — Có lý do hợp lý để bỏ qua
```

---

*Cập nhật: 02/09/2026 | Version: 1.0*
