# PHASE 18 — SHAP / XAI

## 1. MỤC TIÊU

Sử dụng SHAP (SHapley Additive exPlanations) để giải thích quyết định của mô hình XGBoost:
- Hiểu feature nào đóng góp nhiều nhất vào dự đoán của mô hình
- Visualize top features quan trọng nhất (beeswarm, bar, force plot)

**Lưu ý học thuật:** SHAP **không chứng minh** một feature "gây ra" gian lận. SHAP giải thích **mức độ đóng góp của feature vào đầu ra mô hình** trên tập mẫu đang xét. Cách viết đúng:

- ❌ "V317 là nguyên nhân khiến giao dịch gian lận."
- ✅ "Theo giá trị SHAP, num__c14 có mức đóng góp lớn vào đầu ra của mô hình trên tập mẫu được phân tích."

TreeExplainer là cơ chế phù hợp cho nhóm tree ensemble (XGBoost) — tài liệu báo cáo đã xác định điều này.

---

## 2. CÀI ĐẶT

```bash
.venv\Scripts\python.exe -m pip install shap matplotlib
```

Đã cài: `shap 0.52.0`, `matplotlib 3.11.2`.

---

## 3. CODE SHAP EXPLANATION

File: `ml/shap_explain.py` (đường dẫn tuyệt đối dựa trên `__file__`, nên chạy được từ mọi cwd, nhưng thống nhất chạy từ **root project**)

```python
"""
Phase 18: SHAP / XAI

Explain the selected XGBoost fraud detection model using SHAP.
"""

from pathlib import Path
import json
import warnings

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import shap

warnings.filterwarnings("ignore")

SAMPLE_SIZE = 5000
RANDOM_STATE = 42

BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "data" / "test.parquet"
MODEL_PATH = BASE_DIR / "models" / "xgboost.pkl"
FEATURE_COLS_PATH = BASE_DIR / "models" / "feature_columns.json"
OUTPUT_DIR = BASE_DIR / "models"


def load_data_and_model():
    """Load test data, feature list and trained XGBoost model."""

    print("Loading test data...")

    test_df = pd.read_parquet(DATA_PATH)

    print(f"Test rows: {len(test_df):,}")

    # Load feature columns from JSON
    with open(
        FEATURE_COLS_PATH,
        "r",
        encoding="utf-8",
    ) as f:
        feature_cols = json.load(f)

    missing_features = [
        col for col in feature_cols
        if col not in test_df.columns
    ]

    if missing_features:
        raise ValueError(
            f"Missing features in test data: {missing_features[:10]}"
        )

    X_test = test_df[feature_cols].copy()

    # Convert boolean columns to integers.
    bool_cols = X_test.select_dtypes(include=["bool"]).columns

    for col in bool_cols:
        X_test[col] = X_test[col].astype("int8")

    # Keep only numeric features used by the model.
    X_test = X_test.select_dtypes(
        include=["number"]
    )

    # Replace inf values if present.
    X_test = X_test.replace(
        [np.inf, -np.inf],
        np.nan
    )

    # XGBoost model input should not contain NaN unless
    # the trained model explicitly supports the same representation.
    # Preserve NaN here because XGBoost supports missing values.
    
    sample_size = min(
        SAMPLE_SIZE,
        len(X_test)
    )

    X_sample = X_test.sample(
        n=sample_size,
        random_state=RANDOM_STATE
    )

    print(f"SHAP sample size: {len(X_sample):,}")
    print(f"Features: {X_sample.shape[1]:,}")

    print("Loading XGBoost model...")

    model = joblib.load(MODEL_PATH)

    return X_sample, model


def create_shap_explainer(model):
    """Create TreeExplainer for XGBoost."""

    print("Creating SHAP TreeExplainer...")

    return shap.TreeExplainer(model)


def compute_shap_values(explainer, X):
    """Compute SHAP values."""

    print("Computing SHAP values...")

    shap_values = explainer.shap_values(X)

    # Normalize possible SHAP output formats.
    if isinstance(shap_values, list):
        # Binary classification:
        # use positive/fraud class.
        if len(shap_values) == 2:
            shap_values = shap_values[1]
        else:
            shap_values = shap_values[0]

    shap_values = np.asarray(shap_values)

    # Some SHAP versions may return:
    # (n_samples, n_features, n_classes)
    if shap_values.ndim == 3:
        shap_values = shap_values[:, :, 1]

    if shap_values.shape != X.shape:
        raise ValueError(
            f"SHAP shape {shap_values.shape} "
            f"does not match X shape {X.shape}"
        )

    print(
        f"SHAP matrix: "
        f"{shap_values.shape[0]:,} samples × "
        f"{shap_values.shape[1]:,} features"
    )

    return shap_values


def plot_summary(shap_values, X):
    """Generate SHAP beeswarm summary plot."""

    print("Generating SHAP summary plot...")

    plt.figure(figsize=(12, 10))

    shap.summary_plot(
        shap_values,
        X,
        plot_type="dot",
        show=False,
        max_display=20
    )

    plt.title("SHAP Summary — Top 20 Features")
    plt.tight_layout()

    output_path = OUTPUT_DIR / "shap_summary.png"

    plt.savefig(
        output_path,
        dpi=150,
        bbox_inches="tight"
    )

    plt.close()

    print(f"Saved: {output_path}")


def plot_bar(shap_values, X):
    """Generate mean absolute SHAP importance bar chart."""

    print("Generating SHAP bar plot...")

    plt.figure(figsize=(12, 10))

    shap.summary_plot(
        shap_values,
        X,
        plot_type="bar",
        show=False,
        max_display=20
    )

    plt.title("SHAP Feature Importance — Top 20")
    plt.tight_layout()

    output_path = OUTPUT_DIR / "shap_bar.png"

    plt.savefig(
        output_path,
        dpi=150,
        bbox_inches="tight"
    )

    plt.close()

    print(f"Saved: {output_path}")


def plot_individual(explainer, shap_values, X):
    """Generate individual SHAP explanations."""

    print("Generating individual explanations...")

    indices = [0, 100, 500]

    for idx in indices:

        if idx >= len(X):
            continue

        sample = X.iloc[idx]

        base_value = explainer.expected_value

        if isinstance(base_value, np.ndarray):
            if base_value.ndim > 0:
                base_value = base_value[-1]

        sample_shap = shap_values[idx]

        plt.figure(figsize=(16, 6))

        shap.force_plot(
            base_value,
            sample_shap,
            sample,
            matplotlib=True,
            show=False
        )

        plt.title(
            f"SHAP Force Plot — Sample #{idx}"
        )

        plt.tight_layout()

        output_path = (
            OUTPUT_DIR /
            f"shap_individual_{idx}.png"
        )

        plt.savefig(
            output_path,
            dpi=150,
            bbox_inches="tight"
        )

        plt.close()

        print(f"Saved: {output_path}")


def get_top_features(shap_values, X, top_n=20):
    """Calculate mean absolute SHAP feature importance."""

    print("Calculating feature importance...")

    mean_abs_shap = np.abs(
        shap_values
    ).mean(axis=0)

    importance_df = pd.DataFrame({
        "feature": X.columns,
        "mean_abs_shap": mean_abs_shap
    })

    importance_df = importance_df.sort_values(
        "mean_abs_shap",
        ascending=False
    ).reset_index(drop=True)

    top_features = importance_df.head(top_n)

    output_path = OUTPUT_DIR / "top_features.csv"

    top_features.to_csv(
        output_path,
        index=False
    )

    print(f"\nTop {top_n} features:")
    print(top_features.to_string(index=False))

    print(f"\nSaved: {output_path}")

    return top_features


def main():

    print("=" * 70)
    print("PHASE 18 — SHAP / XAI")
    print("=" * 70)

    X_sample, model = load_data_and_model()

    explainer = create_shap_explainer(model)

    shap_values = compute_shap_values(
        explainer,
        X_sample
    )

    plot_summary(
        shap_values,
        X_sample
    )

    plot_bar(
        shap_values,
        X_sample
    )

    plot_individual(
        explainer,
        shap_values,
        X_sample
    )

    top_features = get_top_features(
        shap_values,
        X_sample,
        top_n=20
    )

    print("\n" + "=" * 70)
    print("PHASE 18 — SHAP EXPLANATION COMPLETE")
    print("=" * 70)

    print("\nTop 5 features:")

    print(
        top_features
        .head(5)
        .to_string(index=False)
    )


if __name__ == "__main__":
    main()
```

### Sửa so với bản trước

- `MODEL_PATH`: `xgb_model.pkl` → **`xgboost.pkl`** (tên file thực tế từ Phase 16)
- `FEATURE_COLS_PATH`: `feature_cols.pkl` → **`feature_columns.json`** (load bằng `json.load`, không phải `joblib.load`)

---

## 4. CHẠY

```bash
.venv\Scripts\Activate.ps1
.venv\Scripts\python.exe ml\shap_explain.py
```

Chạy từ **root project**, không `cd ml` rồi dùng đường dẫn tương đối lẫn lộn.

---

## 5. KẾT QUẢ THỰC TẾ (ACTUAL RESULTS)

Log đầy đủ: `evidence/phase_18/execution_log.txt`

```
Test rows: 88,581
SHAP sample size: 5,000
Features: 1,014
SHAP matrix: 5,000 samples × 1,014 features
```

### 5.1 Top 20 features (mean |SHAP| — đo thực tế từ `top_features.csv`)

| # | Feature | mean_abs_shap |
|---|---------|---------------|
| 1 | num__c14 | 0.186257 |
| 2 | num__transaction_amt | 0.176893 |
| 3 | num__v258 | 0.157891 |
| 4 | num__c1 | 0.150194 |
| 5 | num__v70 | 0.148455 |
| 6 | num__v48 | 0.121820 |
| 7 | cat__card6_credit | 0.119443 |
| 8 | num__card1_freq | 0.095237 |
| 9 | num__v294 | 0.094872 |
| 10 | num__d3 | 0.091954 |
| 11 | num__v308 | 0.091344 |
| 12 | num__c13 | 0.089610 |
| 13 | num__c11 | 0.089317 |
| 14 | num__v91 | 0.079044 |
| 15 | num__d2 | 0.071198 |
| 16 | num__c8 | 0.071144 |
| 17 | num__d15 | 0.067024 |
| 18 | num__transaction_day_index | 0.063672 |
| 19 | num__c6 | 0.060987 |
| 20 | num__d4 | 0.058009 |

### 5.2 Phân tích (viết theo hướng đóng góp, không phải nhân quả)

- Top features là sự pha trộn của: **Vesta C-features** (c14, c1, c13, c11, c8, c6 — thường là biến đếm), **V-features** (v258, v70, v48, v294, v308, v91), **D-features** (d3, d2, d15, d4 — delta/time), cùng các feature nghiệp vụ: **transaction_amt** (số tiền giao dịch), **card6_credit** (loại thẻ), **card1_freq** (tần suất card1 — feature tần số tạo ở Phase 15), **transaction_day_index** (feature thời gian tạo ở Phase 15).
- **num__transaction_amt** đứng #2 → theo SHAP, số tiền giao dịch có mức đóng góp lớn vào đầu ra mô hình trên tập mẫu phân tích — phù hợp hiểu biết nghiệp vụ (giao dịch có số tiền bất thường thường liên quan gian lận).
- **id_XX features KHÔNG xuất hiện trong top 20** — khác với bảng minh họa ban đầu.
- Giá trị mean |SHAP| thực tế (~0.06–0.19) nhỏ hơn nhiều so với bảng minh họa (0.25–0.45) — bảng đó chỉ mang tính minh họa, KHÔNG đưa vào báo cáo.

### 5.3 Bảng minh họa ban đầu (KHÔNG dùng làm kết quả)

| Feature | Mean \|SHAP\| |
|---------|-------------|
| V317 | 0.45 |
| V316 | 0.38 |
| id_02 | 0.32 |
| V287 | 0.28 |
| V207 | 0.25 |

Chỉ minh họa. Kết quả chính thức lấy từ `top_features.csv` thực tế (mục 5.1).

---

## 6. KIỂM TRA BỔ SUNG (VERIFICATION — trước Phase 19)

Script: `ml/verify_shap.py` — log: `evidence/phase_18/verification_checks.txt`

Chạy:

```bash
.venv\Scripts\python.exe ml\verify_shap.py
```

### 6.1 Check 1 — Force plot dùng đúng base value và SHAP values (binary classification)

SHAP values shape `(5000, 1014)` khớp X. `expected_value` là scalar float32 = **-0.60523087** (base margin của XGBoost). Kiểm tra tính chất cộng (additive property) — `base_value + Σ SHAP_i` phải bằng raw margin đầu ra mô hình trên cùng sample:

| Sample | base + ΣSHAP | Model margin | diff | Kết quả |
|--------|--------------|--------------|------|---------|
| #0 | -1.514971 | -1.514971 | 5.36e-07 | OK |
| #100 | -2.804760 | -2.804760 | 4.17e-07 | OK |
| #500 | -3.603232 | -3.603231 | 5.36e-07 | OK |

diff ~5e-7 tương ứng độ chính xác float32 → force plot dùng đúng base value và SHAP values của class fraud (binary classification).

### 6.2 Check 2 — Hàng được giải thích thuộc tập test, không đưa nhãn vào feature

- `'is_fraud' in feature_cols`: **False** ✅
- `'is_fraud' in X_sample columns`: **False** ✅
- Sample indices ⊆ test indices: **True** ✅
- Sampled rows identical to test rows: **True** ✅ (5,000/5,000)
- Ánh xạ force plot → test row:
  - sample #0 → test row 24134, is_fraud = 0
  - sample #100 → test row 45573, is_fraud = 0
  - sample #500 → test row 52226, is_fraud = 0

**Ghi nhận:** cả 3 mẫu force plot đều là giao dịch **không gian lận** (do random sampling với random_state=42). Nhãn `is_fraud` không lọt vào đầu vào — kiểm tra đạt. Nếu cần force plot cho mẫu gian lận, có thể bổ sung sau (không thuộc phạm vi kiểm tra này).

### 6.3 Check 3 — top_features.csv đúng 20 hàng, sắp xếp giảm dần, khớp biểu đồ

- Rows: **20** ✅
- Columns: `['feature', 'mean_abs_shap']` ✅
- Sorted descending by mean_abs_shap: **True** ✅
- Feature order khớp recomputation từ SHAP values: **True** ✅
- max |diff| CSV vs recomputation: **4.77e-09** → OK (chỉ là sai số làm tròn khi CSV lưu 8 chữ số thập phân; ngưỡng cho round-trip CSV là 1e-6)
- Biểu đồ `shap_bar.png` dùng cùng nguồn: `summary_plot(shap_values, X_sample, plot_type="bar", max_display=20)` → top 20 theo mean|SHAP| == 20 rows trong CSV ✅

---

## 7. EVIDENCE FILES

```
ml/models/
├── shap_summary.png          # Beeswarm plot (156 KB)
├── shap_bar.png              # Bar chart (79 KB)
├── shap_individual_0.png     # Force plot sample 0 (87 KB)
├── shap_individual_100.png   # Force plot sample 100 (72 KB)
├── shap_individual_500.png   # Force plot sample 500 (81 KB)
├── top_features.csv          # Top 20 features thực tế
└── [saved models từ Phase 16]

ml/
├── shap_explain.py           # Script SHAP chính
└── verify_shap.py            # Script kiểm tra bổ sung

evidence/phase_18/
├── execution_log.txt         # Log chạy shap_explain.py
└── verification_checks.txt   # Log 3 kiểm tra bổ sung
```

---

## 8. SUCCESS CRITERIA (kiểm tra thực tế 09/10/2026)

```text
[✅] XGBoost model loaded successfully
[✅] Test data loaded successfully (88,581 rows)
[✅] 5,000 samples used for SHAP
[✅] SHAP matrix = 5,000 × 1,014 features
[✅] No SHAP shape mismatch (kiểm tra shape == X.shape trong code)
[✅] shap_summary.png generated
[✅] shap_bar.png generated
[✅] shap_individual_0.png generated
[✅] shap_individual_100.png generated
[✅] shap_individual_500.png generated
[✅] top_features.csv generated
[✅] Top 20 features chứa mean(|SHAP|) đo thực tế (0.058–0.186)
[✅] Top features được diễn giải từ evidence thực tế:
     Vesta C/V/D features + transaction_amt + card6_credit
     + card1_freq + transaction_day_index
     (id_XX KHÔNG nằm trong top 20 — ghi đúng, không chỉnh số)

Kiểm tra bổ sung (ml/verify_shap.py):
[✅] Force plot dùng đúng base value (-0.60523087) và SHAP values
     class fraud — additive property diff ~5e-7 (float32 precision)
[✅] Hàng giải thích thuộc test set (5,000/5,000 khớp),
     is_fraud KHÔNG có trong feature_cols / X_sample
[✅] top_features.csv: đúng 20 rows, sắp xếp giảm dần,
     khớp recomputation (max diff 4.77e-09 = sai số làm tròn CSV)
     và cùng nguồn với shap_bar.png
```

---

## 9. Liên hệ

- Trước: [PHASE 17 — Model Evaluation](../17_model_evaluation/model_evaluation.md)
- Sau: [PHASE 19 — Model Integration](../19_model_integration/model_integration.md)

*Cập nhật: 09/10/2026 | Version: 2.1 (kết quả thực nghiệm + verification)*
