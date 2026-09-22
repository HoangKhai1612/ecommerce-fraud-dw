# EXTENSION BACKLOG

**Dự án:** Ecommerce Fraud Detection Data Warehouse  
**Ngày tạo:** 02/09/2026

> ⚠️ **QUAN TRỌNG:** Tuyệt đối không triển khai bất kỳ extension nào trước khi:
> - CORE SCOPE = 100% hoàn thành
> - Tất cả tests PASS
> - Báo cáo hoàn chỉnh
> - Demo ổn định

---

## ĐIỀU KIỆN ĐỂ BẮT ĐẦU EXTENSION

```
[ ] Tất cả phases core (P00 → P25) = DONE
[ ] docker compose up → tất cả services healthy
[ ] End-to-end pipeline chạy không lỗi
[ ] Báo cáo 4 chương đã viết xong
[ ] Demo script đã test
```

---

## EXTENSION LIST

| ID | Idea | Benefit | Complexity | Time Est. | Priority | Status |
|----|------|---------|-----------|-----------|---------|--------|
| EXT-001 | Real-time streaming với Kafka | Gần thực tế hơn | Very High | 5+ ngày | LOW | BACKLOG |
| EXT-002 | Isolation Forest (Anomaly Detection) | So sánh supervised vs unsupervised | Medium | 2 ngày | MEDIUM | BACKLOG |
| EXT-003 | Auto-retraining khi model drift | MLOps | High | 3+ ngày | LOW | BACKLOG |
| EXT-004 | Alert system khi fraud rate tăng đột biến | Business value | Medium | 1 ngày | HIGH | BACKLOG |
| EXT-005 | CI/CD với GitHub Actions | DevOps | Medium | 2 ngày | LOW | BACKLOG |
| EXT-006 | API Authentication (JWT) | Security | Medium | 1 ngày | LOW | BACKLOG |
| EXT-007 | MLflow Model Registry | MLOps | Medium | 2 ngày | MEDIUM | BACKLOG |
| EXT-008 | Slack/Email notification pipeline | Operational | Low | 0.5 ngày | HIGH | BACKLOG |
| EXT-009 | Advanced Text-to-SQL với schema awareness | AI quality | Medium | 2 ngày | MEDIUM | BACKLOG |
| EXT-010 | Graph-based fraud detection | Research | Very High | 5+ ngày | LOW | BACKLOG |

---

## EXTENSION DETAIL (Khi được phép triển khai)

### EXT-004 — Alert System (Recommended first)

**Idea:** Tự động gửi alert khi fraud rate trong 1 giờ vượt ngưỡng  
**Why useful:** Giá trị kinh doanh cao, demo ấn tượng  
**Complexity:** LOW-MEDIUM  
**Benefit:** Tăng giá trị thực tế của hệ thống  
**Implementation:** Airflow sensor + email/Slack webhook  
**Risk:** Thêm dependency vào external service  
**Dependency:** P24 (E2E pipeline phải chạy được)  

### EXT-008 — Pipeline Notification (Recommended second)

**Idea:** Gửi thông báo khi Airflow pipeline fail  
**Why useful:** Operational monitoring  
**Complexity:** LOW  
**Benefit:** Professional MLOps practice  
**Implementation:** Airflow email operator hoặc Slack callback  
**Risk:** LOW  
**Dependency:** P13 (Airflow phải setup xong)  

---

*Cập nhật: 02/09/2026 | Version: 1.0*
