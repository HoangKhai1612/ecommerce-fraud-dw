# SCOPE CONTROL

**Ngày tạo:** 02/09/2026

> File này dùng để kiểm soát phạm vi trong suốt dự án.  
> Trước khi làm bất kỳ thứ gì mới, phải kiểm tra tại đây.

---

## SCOPE CONTROL CHECKLIST

Khi muốn thêm thành phần mới, hãy hỏi:

```
[ ] Thành phần này có trong đề cương không?
[ ] Thành phần này có thực sự cần thiết không?
[ ] Core scope đã 100% chưa?
[ ] Thời gian có đủ không?
[ ] Có ảnh hưởng đến stability của core không?
```

Nếu câu trả lời cho bất kỳ câu nào là KHÔNG → **Đưa vào Extension Backlog**

---

## IN SCOPE — CHECKLIST HÀNG NGÀY

Dán cái này lên màn hình:

```
✅ ĐƯỢC LÀM:
  Python ingestion
  PostgreSQL (RAW, STG, DW)
  dbt (models, tests)
  Airflow (DAG, tasks)
  Logistic Regression
  Random Forest
  XGBoost
  SHAP
  FastAPI
  Metabase
  AI Assistant (Text-to-SQL)
  Docker Compose
  Git

❌ KHÔNG ĐƯỢC TỰ Ý THÊM:
  Kafka
  Spark
  Kubernetes
  Cloud (AWS/GCP/Azure)
  Deep Learning
  Streaming
  Lakehouse
  Frontend (React/Vue)
  Real-time prediction
  Auto-retraining
  Microservices architecture
```

---

## SCOPE VIOLATION LOG

| Date | Ai phát hiện | Mô tả vi phạm | Action |
|------|-------------|---------------|--------|
| — | — | Chưa có vi phạm | — |

---

## SCOPE CHANGE REQUEST

Nếu muốn thay đổi scope:

1. Ghi vào `decision_log.md`
2. Phải có lý do rõ ràng từ đề cương
3. Đánh giá impact
4. Nếu là extension → `extension_backlog.md`
5. Chỉ thực hiện nếu core = 100%

---

*Cập nhật: 02/09/2026 | Version: 1.0*
