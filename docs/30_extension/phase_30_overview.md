# PHASE 30 - EXTENSION & ADVANCED FEATURES

## 1. Mục tiêu

Phase 30 bổ sung 6 tính năng mở rộng nhằm nâng cao khả năng của hệ thống phát hiện gian lận thương mại điện tử:

1. **EXT-01**: LightGBM Model - Thêm mô hình LightGBM và so sánh hiệu năng với các mô hình hiện có
2. **EXT-02**: AI Provider Abstraction - Tách biệt providers AI (Ollama/DeepSeek) theo thiết kế Factory Pattern
3. **EXT-03**: MLflow Experiment Tracking - Theo dõi thí nghiệm ML
4. **EXT-04**: GitHub Actions CI/CD - Tự động hóa kiểm thử
5. **EXT-05**: Fraud Monitoring & Alerting - Giám sát tỷ lệ gian lận
6. **EXT-06**: Batch Prediction API - Dự đoán hàng loạt

## 2. Phạm vi triển khai

Phase 30 tập trung vào việc mở rộng mà không làm thay đổi kiến trúc cốt lõi của hệ thống. Tất cả các extension được thiết kế module hóa, có thể bật/tắt độc lập.
