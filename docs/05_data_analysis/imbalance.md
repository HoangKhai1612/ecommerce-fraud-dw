# IMBALANCE ANALYSIS

**Dự án:** Ecommerce Fraud Detection Data Warehouse  
**Phase:** 05 — Data Profiling & EDA  
**Ngày thực hiện:** 02/09/2026  

---

## 1. CLASS IMBALANCE OVERVIEW

| Label | Count | Ratio |
|-------|-------|-------|
| 0 (Non-Fraud) | 569,877 | 96.50% |
| 1 (Fraud) | 20,663 | 3.50% |

**Tỷ lệ imbalance:** 1:27.6 (1 fraud với mỗi 27.6 non-fraud)

---

## 2. TẠI SAO IMBALANCE LÀ VẤN ĐỄ QUAN TRỌNG?

### Vấn đề với Accuracy:
Nếu model dự đoán **tất cả là Non-Fraud** (isFraud=0):
- Accuracy = 96.50% — trông rất tốt!
- **Nhưng Recall (fraud detection rate) = 0%** — tất cả fraud đều bỏ qua

### Đây là lý do tại sao chúng ta KHÔNG dùng Accuracy:
| Metric | Khi predict tất cả = Non-Fraud |
|--------|-------------------------------|
| Accuracy | 96.50% ❌ (gây lừa) |
| Precision | 0.00% |
| Recall | 0.00% |
| F1-score | 0.00% |
| ROC-AUC | 0.50 (random) |
| PR-AUC | 0.035 (rất tệ) |

---

## 3. STRATEGIES FOR IMBALANCE HANDLING

### Option 1: Class Weight (Recommended for this project)
```python
# Logistic Regression
LogisticRegression(class_weight='balanced')

# Random Forest
RandomForestClassifier(class_weight='balanced')

# XGBoost
XGBClassifier(scale_pos_weight=ratio)  # ratio = 27.6
```

**Advantages:**
- Không tạo dữ liệu giả
- Nhanh, đơn giản
- Phù hợp với đề cương (batch processing)

**Disadvantages:**
- Có thể bỏ sót một số fraud cases

### Option 2: SMOTE (Synthetic Minority Oversampling Technique)
```python
from imblearn.over_sampling import SMOTE
smote = SMOTE(sampling_strategy=0.3, random_state=42)
X_res, y_res = smote.fit_resample(X_train, y_train)
```

**Advantages:**
- Tăng số lượng fraud mẫu
- Cải thiện recall

**Disadvantages:**
- Cần cài thêm `imbalanced-learn`
- Có thể gây overfitting nếu không cẩn trọng
- Chỉ áp dụng trên **train set** — không áp dụng val/test

### Option 3: Combination
- Dùng SMOTE cho một số models, class_weight cho số khác
- So sánh results

---

## 4. SPLIT STRATEGY (PHÌNH TRƯỚC KHI XỬ LÝ)

### 1. Split trước khi xử lý imbalance:
```
Full Dataset (590,540)
    ↓
70% Train (413,378) → SMOTE/class_weight
    ↓
15% Validation (88,581) → Pure, no resampling
    ↓
15% Test (88,581) → Pure, no resampling
```

**Lý do:**
- Validation/test phải phản ánh thực tế (imbalanced)
- SMOTE chỉ áp dụng trên train để tránh data leakage

### 2. Stratified split:
```python
from sklearn.model_selection import train_test_split

# Split giữ nguyên tỷ lệ fraud
X_train, X_temp, y_train, y_temp = train_test_split(
    X, y, test_size=0.30, stratify=y, random_state=42
)

X_val, X_test, y_val, y_test = train_test_split(
    X_temp, y_temp, test_size=0.50, stratify=y_temp, random_state=42
)
```

---

## 5. EVALUATION METRICS CHO IMBALANCED DATA

| Metric | Công formulation | Tại sao dùng |
|--------|----------------|-------------|
| **PR-AUC** | Area under Precision-Recall curve | **Tốt nhất** cho imbalanced — tập trung vào minority class |
| **F1-score** | 2 * (Precision * Recall) / (Precision + Recall) | Cân bằng giữa precision và recall |
| **Recall (Sensitivity)** | TP / (TP + FN) | Tỷ lệ fraud bị phát hiện — QUAN TRỌNG |
| **Precision** | TP / (TP + FP) | Trong số dự đoán fraud, bao nhiêu đúng |
| **ROC-AUC** | Area under ROC curve | Tốt nhưng có thể gây lừa với imbalanced data |
| **Accuracy** | (TP + TN) / Total | ❌ KHÔNG DÙNG — bị lừa bởi imbalance |

---

## 6. KẾ HOẠCH CHIẾN LƯỢC CHO DỰ ÁN

| Model | Strategy | Rationale |
|-------|----------|-----------|
| Logistic Regression | `class_weight='balanced'` | Baseline, simple, interpretable |
| Random Forest | `class_weight='balanced'` | Robust, handles non-linear patterns |
| XGBoost | `scale_pos_weight=27.6` | Best performance, gradient boosting |

### So sánh chiến lược:
1. **Model 1**: LR + class_weight → baseline
2. **Model 2**: RF + class_weight → ensemble
3. **Model 3**: XGBoost + scale_pos_weight → boosting
4. (Nếu cần) **Model 4**: XGBoost + SMOTE → so sánh thêm

---

## 7. EXPECTED OUTCOMES

| Metric | Target |
|--------|--------|
| Recall (fraud) | ≥ 0.70 |
| F1-score (fraud) | ≥ 0.70 (theo DoD) |
| PR-AUC | ≥ 0.40 |
| ROC-AUC | ≥ 0.90 |

> **Lưu ý:** F1 ≥ 0.7 là tiêu chuẩn từ project_objectives.md (M4).

*Cập nhật: 02/09/2026 | Version: 1.0*
