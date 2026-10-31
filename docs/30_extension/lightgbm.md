# EXT-01: LightGBM Model

## 1. Mục tiêu
Bổ sung mô hình LightGBM (Light Gradient Boosting Machine) vào hệ thống so sánh và đánh giá, nhằm tìm kiếm mô hình có hiệu năng tốt hơn cho bài toán phát hiện gian lận với dữ liệu mất cân bằng.

## 2. Thực hiện

### Training Pipeline
- **File**: ml/train_lightgbm.py
- **Dataset**: Sử dụng cùng tập dữ liệu train/validation như các mô hình khác
- **Cấu hình**: Hyperparameters được tối ưu cho dữ liệu mất cân bằng
- **Scale_pos_weight**: Tính toán tự động dựa trên tỷ lệ fraud/legit

### Model Artifacts
- **Model file**: ml/models/lightgbm.pkl (4,040,484 bytes)
- **Metadata**: ml/models/lightgbm_metadata.json
- **Comparison**: ml/models/model_comparison_phase30.json

### Kết quả đánh giá
Dựa trên tập validation (88,581 mẫu, fraud rate ~3.5%):

| Mô hình | ROC-AUC | PR-AUC | Precision | Recall | F1-Score |
|---------|---------|--------|-----------|--------|----------|
| Logistic Regression | 0.8700 | 0.4859 | 0.8174 | 0.2845 | 0.4221 |
| Random Forest | 0.9130 | 0.6452 | 0.9259 | 0.3626 | 0.5211 |
| XGBoost | 0.9160 | 0.5913 | 0.3160 | 0.7135 | 0.4381 |
| **LightGBM** | **0.9476** | **0.7115** | 0.3117 | **0.8190** | 0.4516 |

**Lưu ý quan trọng:** Mặc dù LightGBM có hiệu năng tốt nhất về ROC-AUC, PR-AUC và Recall, **hiện tại API inference vẫn sử dụng XGBoost** (ml/models/xgboost.pkl). LightGBM chỉ được sử dụng cho mục đích so sánh và đánh giá.
