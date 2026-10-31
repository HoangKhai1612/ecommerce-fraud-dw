"""
scripts/validate_dw_demo_samples.py

Batch-validate DW transactions through the real XGBoost inference pipeline
to find 10 fraud (actual=1, predicted=1) and 10 legitimate (actual=0, predicted=0)
demo samples. Writes a manifest + CSV evidence.

Usage:
    python scripts/validate_dw_demo_samples.py [--limit N] [--output-dir DIR]
"""
import argparse
import json
import sys
from pathlib import Path

import pandas as pd
import psycopg2

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from api.inference import (
    InferencePipeline,
    MODEL_VERSION,
    THRESHOLD,
    get_inference_pipeline,
)

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "dbname": "ecommerce_fraud_dw",
    "user": "postgres",
    "password": "@Melons16122005",
}

OUTPUT_DIR = Path("evidence/phase_31")


def fetch_transactions(conn, is_fraud: int, limit: int) -> pd.DataFrame:
    """Fetch up to `limit` transactions with the given actual label."""
    query = """
        SELECT * FROM marts.fact_transactions
        WHERE is_fraud = %s
        ORDER BY transaction_id
        LIMIT %s
    """
    df = pd.read_sql(query, conn, params=(is_fraud, limit))
    return df


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=200, help="Max transactions per class to test")
    parser.add_argument("--output-dir", type=str, default=str(OUTPUT_DIR))
    args = parser.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    print("Loading inference pipeline...")
    pipeline = get_inference_pipeline()
    pipeline.load()

    conn = psycopg2.connect(**DB_CONFIG)

    all_results = []

    for label in [1, 0]:
        print(f"\nFetching {args.limit} transactions with is_fraud={label}...")
        df = fetch_transactions(conn, label, args.limit)
        print(f"  Fetched {len(df)} rows")

        if len(df) == 0:
            print("  No rows found!")
            continue

        # Drop is_fraud from input (model shouldn't see label)
        feature_df = df.drop(columns=["is_fraud"], errors="ignore")

        print("  Running inference...")
        try:
            probas = pipeline.predict_proba(feature_df)
        except Exception as e:
            print(f"  ERROR: {e}")
            continue

        preds = (probas >= THRESHOLD).astype(int)

        for i, row in df.iterrows():
            tid = int(row["transaction_id"])
            actual = int(row["is_fraud"])
            pred = int(preds[i])
            prob = float(probas[i])
            correct = actual == pred

            all_results.append({
                "transaction_id": tid,
                "actual_label": actual,
                "predicted_label": pred,
                "fraud_probability": prob,
                "threshold": THRESHOLD,
                "model_version": MODEL_VERSION,
                "prediction_correct": correct,
                "feature_count": len(pipeline.feature_cols),
                "missing_feature_count": 0,
                "source": "data_warehouse",
                "dataset_split": "test",
            })

    conn.close()

    results_df = pd.DataFrame(all_results)
    results_df.to_csv(out_dir / "dw_validation_all.csv", index=False)

    # Select 10 fraud (TP) and 10 legit (TN)
    tp = results_df[(results_df["actual_label"] == 1) & (results_df["predicted_label"] == 1)]
    tn = results_df[(results_df["actual_label"] == 0) & (results_df["predicted_label"] == 0)]
    fp = results_df[(results_df["actual_label"] == 0) & (results_df["predicted_label"] == 1)]
    fn = results_df[(results_df["actual_label"] == 1) & (results_df["predicted_label"] == 0)]

    print(f"\n=== Summary ===")
    print(f"Total tested: {len(results_df)}")
    print(f"TP (fraud, predicted fraud): {len(tp)}")
    print(f"TN (legit, predicted legit): {len(tn)}")
    print(f"FP (legit, predicted fraud): {len(fp)}")
    print(f"FN (fraud, predicted legit): {len(fn)}")

    # Select diverse samples
    selected_fraud = tp.head(10)
    selected_legit = tn.head(10)

    selected = pd.concat([selected_fraud, selected_legit], ignore_index=True)
    selected.to_csv(out_dir / "dw_demo_sample_validation.csv", index=False)

    # Write markdown report
    md = f"""# DW Demo Sample Validation Report

## Model
- Model version: {MODEL_VERSION}
- Threshold: {THRESHOLD}
- Feature count: {len(pipeline.feature_cols)}

## Dataset
- Total tested: {len(results_df)}
- Fraud (actual=1): {len(results_df[results_df['actual_label']==1])}
- Legit (actual=0): {len(results_df[results_df['actual_label']==0])}

## Confusion Matrix (on tested subset)
- TP: {len(tp)}
- TN: {len(tn)}
- FP: {len(fp)}
- FN: {len(fn)}

## Selected Demo Samples
- Fraud (TP): {len(selected_fraud)}
- Legit (TN): {len(selected_legit)}

## Note
This is a curated demo set, NOT an independent evaluation.
Do not use these numbers to report model accuracy/precision/recall/F1.
"""
    (out_dir / "dw_demo_sample_validation.md").write_text(md, encoding="utf-8")

    # Write manifest (JSON) for frontend API
    manifest = {
        "model_version": MODEL_VERSION,
        "threshold": THRESHOLD,
        "feature_count": len(pipeline.feature_cols),
        "validated_at": pd.Timestamp.now().isoformat(),
        "fraud_samples": selected_fraud["transaction_id"].tolist(),
        "legit_samples": selected_legit["transaction_id"].tolist(),
    }
    (out_dir / "dw_demo_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    print(f"\nSelected {len(selected_fraud)} fraud + {len(selected_legit)} legit samples")
    print(f"Output written to {out_dir}")


if __name__ == "__main__":
    main()
