# CHAPTER MAPPING

**Dự án:** Ecommerce Fraud Detection Data Warehouse  
**Phase:** 01 — Đề cương Analysis  
**Ngày tạo:** 02/09/2026  

> File này ánh xạ từng thành phần triễn khai sang chương báo cáo cuối cùng theo cấu trúc 4 chương của đề cương.

---

## 1. CẤU TRÚC BÁO CÁO (THEO ĐỀ CƯƠNG)

```text
CHƯƠNG 1: GIỚI THIỆU TỔNG QUAN
  1.1 Lý do chọn đề tài
  1.2 Mục tiêu và Nhiệm vụ
  1.3 Phạm vi nghiên cứu
  1.4 Kết quả dự kiến

CHƯƠNG 2: KIẾN THỨC NỀN TẢNG
  2.1 Cơ sở lý thuyết (Data Engineering, DW, ML, SHAP, LLM, BI...)
  2.2 Công cụ sử dụng (Python, PostgreSQL, Airflow, dbt, sklearn, XGBoost, SHAP, FastAPI, Metabase, Ollama, Docker, Git)

CHưƢƠNG 3: PHÂN TÍCH THIẾT KẾ
  3.1 Khảo sát (bài toán, dữ liệu, yêu cầu)
  3.2 Phân tích (quy trình dữ liệu, ML pipeline, AI Assistant)
  3.3 Thiết kế (kiến trúc, DW, pipeline, ML pipeline, AI Assistant)

CHƯƠNG 4: XÂY DỰNG CHƯƠNG TRÌNH
  4.1 Môi trường
  4.2 Data Ingestion
  4.3 Data Pipeline và Transformation
  4.4 Data Quality
  4.5 Data Warehouse
  4.6 Fraud Detection Model
  4.7 SHAP + tích hợp model
  4.8 Dashboard
  4.9 AI Assistant + FastAPI
  4.10 Đóng gói + Kiểm thử

KẾT LUẬN: Kết quả, Hạn chế, Hướng phát triển
```

---

## 2. PHASE → CHAPTER ÁNH XẠ

| Phase | Tên phase | Nội dung triễn khai | Chapter | Section |
|-------|-----------|---------------------|---------|---------|
| P00 | Project Governance | Scope, assumptions, constraints, decision log | Ch.1 | 1.3 |
| P01 | De cuong analysis | Tóm tắt đề cương, traceability | Ch.1, 3.1 | 1.2, 3.1.1 |
| P02 | Problem analysis | Business problem, fraud patterns, requirements | Ch.1, 3.1 | 1.1, 3.1.1, 3.1.3 |
| P03 | Environment setup | Cài đặt công cụ, môi trường | Ch.2, Ch.4 | 2.2, 4.1 |
| P04 | Dataset acquisition | Dataset source, structure, download | Ch.2, 3.1 | 2.1, 3.1.2 |
| P05 | Data profiling & EDA | Phân tích missing, imbalance, distributions | Ch.2, 3.1, 4.6 | 2.1, 3.1.2, 4.6 |
| P06 | System requirements | FR, NFR | Ch.1, 3.1 | 1.2, 3.1.3 |
| P07 | System architecture | High-level architecture, components | Ch.2, 3.3 | 2.2, 3.3 |
| P08 | Data modeling | Star Schema, fact/dimension design | Ch.3 | 3.3.2 |
| P09 | Data ingestion | Python script nạp CSV → PostgreSQL | Ch.4 | 4.2 |
| P10 | RAW layer | Schema raw, tables raw.transactions, raw.identity | Ch.4 | 4.3, 4.5 |
| P11 | Staging layer | Rename, cast, standardize | Ch.4 | 4.3 |
| P12 | dbt models | Staging + marts models, tests | Ch.4 | 4.3, 4.5 |
| P13 | Airflow | DAG orchestration | Ch.4 | 4.3 |
| P14 | Data quality | Completeness, validity, uniqueness tests | Ch.4 | 4.4 |
| P15 | Fraud data prep | Label analysis, feature engineering | Ch.4 | 4.6 |
| P16 | Machine learning | LR, RF, XGBoost training | Ch.4 | 4.6 |
| P17 | Model evaluation | Metrics comparison table | Ch.4 | 4.6 |
| P18 | SHAP / XAI | Global + local explanations | Ch.4 | 4.7 |
| P19 | Model integration | Lưu prediction vào DW | Ch.4 | 4.7 |
| P20 | Metabase dashboard | KPI visualizations | Ch.4 | 4.8 |
| P21 | FastAPI | REST API | Ch.4 | 4.9 |
| P22 | AI Assistant | Text-to-SQL | Ch.4 | 4.9 |
| P23 | Docker Compose | Container deployment | Ch.4 | 4.10 |
| P24 | End-to-end pipeline | Full pipeline integration test | Ch.4 | 4.10 |
| P25 | Testing | Unit, integration, E2E | Ch.4 | 4.10 |
| P26 | Failure engineering | Error scenarios | Kết luận | Kết luận |
| P27 | Performance | Runtime, query time | Ch.4 | 4.10 |
| P28 | Security | Read-only user, SQL validation | Ch.4 | 4.9 |
| P29 | Documentation | README, docs | Ch.1 | Toàn bộ |
| P30 | Extension | Các tính năng mở rộng | Kết luận | Kết luận |

---

## 3. DELIVERABLE → CHAPTER ÁNH XẠ

| Deliverable | Chapter | Section |
|-------------|---------|---------|
| D01 — Python Ingestion | Ch.4 | 4.2 |
| D02 — RAW Layer | Ch.4 | 4.3, 4.5 |
| D03 — STAGING Layer | Ch.4 | 4.3 |
| D04 — Data Warehouse | Ch.3, Ch.4 | 3.3.2, 4.5 |
| D05 — Airflow DAG | Ch.4 | 4.3 |
| D06 — dbt Models | Ch.4 | 4.3 |
| D07 — Data Quality Report | Ch.4 | 4.4 |
| D08 — ML Models (3) | Ch.4 | 4.6 |
| D09 — Model Comparison Table | Ch.4 | 4.6 |
| D11 — SHAP Reports | Ch.4 | 4.7 |
| D12 — Predictions in DW | Ch.4 | 4.7 |
| D13 — Metabase Dashboard | Ch.4 | 4.8 |
| D14 — FastAPI | Ch.4 | 4.9 |
| D15 — AI Assistant | Ch.4 | 4.9 |
| D16 — Docker Compose | Ch.4 | 4.10 |
| D17 — Documentation | Toàn bộ | Toàn bộ |
| D18 — Test Suite | Ch.4 | 4.10 |
| D19 — Evidence Folder | Toàn bộ | Toàn bộ |
| D20 — Báo cáo 4 chương | Toàn bộ | Toàn bộ |
| D21 — README | Ch.1 | Toàn bộ |
| D22 — Demo Script | Ch.4 | 4.10 |

*Cập nhật: 02/09/2026 | Version: 1.0*
