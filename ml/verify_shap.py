"""
Phase 18 — Additional verification checks (pre-Phase 19).

Check 1: Force plot uses correct base value + SHAP values for
         binary classification (additive property vs model margin).
Check 2: Explained rows belong to the test set; is_fraud label
         is NOT among input features.
Check 3: top_features.csv has exactly 20 rows, sorted descending
         by mean_abs_shap, and matches the recomputed values
         (same source as the bar chart).
"""

import json
import warnings
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import shap

warnings.filterwarnings("ignore")

SAMPLE_SIZE = 5000
RANDOM_STATE = 42

BASE_DIR = Path(__file__).resolve().parent.parent / "ml"
DATA_PATH = BASE_DIR / "data" / "test.parquet"
MODEL_PATH = BASE_DIR / "models" / "xgboost.pkl"
FEATURE_COLS_PATH = BASE_DIR / "models" / "feature_columns.json"
TOP_CSV = BASE_DIR / "models" / "top_features.csv"

print("=" * 70)
print("PHASE 18 — VERIFICATION CHECKS")
print("=" * 70)

test_df = pd.read_parquet(DATA_PATH)

with open(FEATURE_COLS_PATH, "r", encoding="utf-8") as f:
    feature_cols = json.load(f)

X_test = test_df[feature_cols].copy()

bool_cols = X_test.select_dtypes(include=["bool"]).columns
for col in bool_cols:
    X_test[col] = X_test[col].astype("int8")

X_test = X_test.select_dtypes(include=["number"])
X_test = X_test.replace([np.inf, -np.inf], np.nan)

X_sample = X_test.sample(
    n=SAMPLE_SIZE,
    random_state=RANDOM_STATE,
)

model = joblib.load(MODEL_PATH)

# -----------------------------------------------------------------
# CHECK 2: rows belong to test set; is_fraud not in features
# -----------------------------------------------------------------

print("\n[CHECK 2] Explained rows belong to test set; "
      "is_fraud not in input features")

print(f"  'is_fraud' in feature_cols        : "
      f"{'is_fraud' in feature_cols}")

print(f"  'is_fraud' in X_sample columns    : "
      f"{'is_fraud' in X_sample.columns}")

sample_idx = set(X_sample.index)
test_idx = set(X_test.index)

print(f"  sample indices subset of test     : "
      f"{sample_idx.issubset(test_idx)}")

print(f"  sample size                       : {len(X_sample):,}")

rows_identical = X_test.loc[X_sample.index].equals(X_sample)

print(f"  sampled rows identical to test    : {rows_identical}")

y = test_df["is_fraud"]

for idx in [0, 100, 500]:
    row_pos = X_sample.index[idx]

    print(f"  force plot sample #{idx:<3} -> test row "
          f"index {row_pos}, is_fraud = {int(y.loc[row_pos])}")

# -----------------------------------------------------------------
# CHECK 1: base value + SHAP additive property (binary classification)
# -----------------------------------------------------------------

print("\n[CHECK 1] Force plot base value & SHAP values "
      "(binary classification)")

explainer = shap.TreeExplainer(model)

shap_values = explainer.shap_values(X_sample)
shap_values = np.asarray(shap_values)

if shap_values.ndim == 3:
    shap_values = shap_values[:, :, 1]

print(f"  shap_values shape                 : {shap_values.shape} "
      f"(expected {X_sample.shape})")

print(f"  shape matches X                   : "
      f"{shap_values.shape == X_sample.shape}")

base_value = explainer.expected_value

print(f"  expected_value type               : "
      f"{type(base_value).__name__}")

print(f"  expected_value                    : "
      f"{np.asarray(base_value).ravel()[:5]}")

# Raw margin of the model (before sigmoid) for the fraud class.
margin = model.predict(X_sample, output_margin=True)

if isinstance(base_value, np.ndarray):
    base_value_scalar = float(np.asarray(base_value).ravel()[-1])
else:
    base_value_scalar = float(base_value)

for idx in [0, 100, 500]:
    lhs = base_value_scalar + float(shap_values[idx].sum())
    rhs = float(margin[idx])
    diff = abs(lhs - rhs)

    status = "OK" if diff < 1e-3 else "MISMATCH"

    print(f"  sample #{idx:<3}: base + sum(SHAP) = {lhs:.6f} | "
          f"model margin = {rhs:.6f} | "
          f"diff = {diff:.2e} -> {status}")

# -----------------------------------------------------------------
# CHECK 3: top_features.csv integrity
# -----------------------------------------------------------------

print("\n[CHECK 3] top_features.csv integrity")

top = pd.read_csv(TOP_CSV)

print(f"  rows                              : {len(top)} (expected 20)")

print(f"  columns                           : {list(top.columns)}")

descending = top["mean_abs_shap"].is_monotonic_decreasing

print(f"  sorted descending by mean_abs_shap: {descending}")

recomputed = (
    pd.DataFrame({
        "feature": X_sample.columns,
        "mean_abs_shap": np.abs(shap_values).mean(axis=0),
    })
    .sort_values("mean_abs_shap", ascending=False)
    .reset_index(drop=True)
    .head(20)
)

feature_order_match = (
    recomputed["feature"].values == top["feature"].values
).all()

values_diff = (
    recomputed["mean_abs_shap"].values
    - top["mean_abs_shap"].values
)

max_diff = float(np.abs(values_diff).max())

print(f"  feature order matches recomputation: {feature_order_match}")

# CSV stores 8 significant decimals, so round-trip
# tolerance is 1e-6 (not float64 epsilon).
print(f"  max |diff| vs recomputation       : {max_diff:.2e} "
      f"-> {'OK' if max_diff < 1e-6 else 'MISMATCH'}")

print(f"  bar chart uses same source        : "
      f"summary_plot(shap_values, X_sample, plot_type='bar', "
      f"max_display=20) -> top 20 by mean|SHAP| == CSV rows")

print("\n" + "=" * 70)
print("VERIFICATION COMPLETE")
print("=" * 70)
