# PHASE 31 - UNIFIED WEB APPLICATION

## 1. Mục tiêu

Phase 31 tích hợp tất cả các chức năng đã phát triển (Data Warehouse, Machine Learning, AI Assistant, Monitoring) thành một ứng dụng web thống nhất với giao diện người dùng hoàn chỉnh.

## 2. Kiến trúc

`mermaid
graph TB
    A[React Frontend - Vite] --> B[FastAPI Backend]
    B --> C[PostgreSQL DW]
    B --> D[XGBoost Model]
    B --> E[AI Assistant]
    B --> F[Ollama/LLM]
    A --> G[API Client /api]
`

**Frontend:** React + TypeScript + Vite (port 5173)  
**Backend:** FastAPI (port 8000)  
**Proxy:** Vite dev server proxies /api/* to http://localhost:8000

## 3. Các trang chức năng (12 trang)

| Trang | Route | Mục đích |
|-------|-------|----------|
| Overview | / | Dashboard tổng quan hệ thống |
| Data Warehouse | /dw | Khám phá dữ liệu Data Warehouse |
| Transaction Testing | /transactions, /testing | Kiểm thử giao dịch với XGBoost thực tế |
| Prediction Detail | /prediction/:id | Chi tiết kết quả dự đoán |
| Prediction History | /history | Lịch sử dự đoán với bộ lọc và phân trang |
| Machine Learning | /ml | Thông tin ML models |
| Model Comparison | /models | So sánh hiệu năng các mô hình |
| Batch Prediction | /batch | Dự đoán hàng loạt |
| AI Assistant | /ai | AI Data Analyst với Text-to-SQL |
| Monitoring | /monitoring | Giám sát hệ thống và tỷ lệ gian lận |
| System Status | /status | Trạng thái các thành phần hệ thống |
| Settings | /settings | Cài đặt ứng dụng |

## 4. Tích hợp Frontend-Backend

- **API Client**: web/src/api.ts - Centralized API calls với error handling
- **Type Definitions**: web/src/types.ts - TypeScript interfaces
- **Routing**: React Router v6 với redirects cho login paths
- **Build**: Vite production build thành công (213KB JS bundle)
