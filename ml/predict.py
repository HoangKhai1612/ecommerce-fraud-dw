"""
Phase 19: Model Integration

Load the trained XGBoost model, generate predictions on the
held-out test set, and persist results to PostgreSQL
(marts schema, predictions table).

Verified against actual project state (09/10/2026):

  - Model artifact: ml/models/xgboost.pkl (Phase 16)
- Feature list:   ml/models/feature_columns.json (1,014 features)
- The processed test set (ml/data/test.parquet) contains the
  1,014 engineered features + is_fraud, but NOT transaction_id:
  Phase 15 (ml/features/prepare.py) drops the id column when
  saving processed data. transaction_id is recovered by replaying
  the exact Phase 15 stratified split (random_state=42) against
  marts.fact_transactions, and the recovery is VERIFIED before
  use: the recovered is_fraud sequence must match the parquet
  is_fraud column element-wise (88,581/88,581). If the check
  fails, the pipeline aborts rather than writing wrong keys.
- Only Logistic Regression used a scaler; XGBoost was trained on
  the preprocessed feature matrix directly, so NO scaler is
  applied here.
- Features must be passed to predict_proba() with the same names,
  order and dtypes as during training: columns come from
  feature_columns.json, bool columns are converted to int BEFORE
  dtype filtering, and column order follows feature_columns.json.
- Database: localhost:5432 is the Windows PostgreSQL 18 instance
  (not the docker postgres container). The pipeline connects via
  POSTGRES_* env vars from .env.
- model_version tags every row so the table can hold prediction
  history for future model versions; uniqueness is enforced on
  (transaction_id, model_version), NOT on transaction_id alone.
"""

import json
import os
import warnings
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from dotenv import load_dotenv
from sklearn.metrics import (
    average_precision_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

warnings.filterwarnings("ignore")

# Standalone script convention (same as ingestion/load_raw.py):
# build the DB URL from env vars directly so the script works
# when executed as `python ml/predict.py` from the project root.
load_dotenv()

DATABASE_URL = URL.create(
    drivername="postgresql+psycopg2",
    username=os.getenv("POSTGRES_USER", "postgres"),
    password=os.getenv("POSTGRES_PASSWORD", "postgres"),
    host=os.getenv("POSTGRES_HOST", "localhost"),
    port=int(os.getenv("POSTGRES_PORT", "5432")),
    database=os.getenv("POSTGRES_DB", "ecommerce_fraud_dw"),
)

TEST_PATH = Path(__file__).resolve().parent / "data" / "test.parquet"

MODELS_DIR = Path(__file__).resolve().parent / "models"

FEATURE_COLS_PATH = MODELS_DIR / "feature_columns.json"

MODEL_PATH = MODELS_DIR / "xgboost.pkl"

METRICS_PKL = MODELS_DIR / "prediction_metrics.pkl"

METRICS_JSON = MODELS_DIR / "prediction_metrics.json"

# Model version tag stored in marts.predictions.
# Identifies the artifact generation (Phase 16 XGBoost,
# trained on the Phase 15 processed training set).
MODEL_VERSION = "xgboost-v1-phase16"

THRESHOLD = 0.5

# Phase 15 split configuration (ml/config.py).
RANDOM_STATE = 42

TRAIN_SIZE = 0.70

VALIDATION_SIZE = 0.15

TEST_SIZE = 0.15


def build_feature_matrix(test_df, feature_cols):
    """Build the model input matrix from a test dataframe.

    Reproduces exactly what the model saw during training:
    column selection by name (order follows feature_cols),
    bool columns converted to int BEFORE numeric dtype
    filtering (so no valid feature is dropped), and inf
    replaced by NaN (XGBoost handles NaN natively).

    Raises ValueError if any feature would be dropped by
    dtype filtering — a signal of a training/serving skew.
    """

    X_test = test_df[feature_cols].copy()

    # Convert bool columns to int BEFORE selecting numeric
    # dtypes, so no feature is accidentally dropped.
    bool_cols = X_test.select_dtypes(include=["bool"]).columns

    for col in bool_cols:
        X_test[col] = X_test[col].astype("int8")

    X_test = X_test.select_dtypes(include=["number"])

    if X_test.shape[1] != len(feature_cols):
        raise ValueError(
            "Feature count mismatch: "
            f"expected {len(feature_cols)}, "
            f"got {X_test.shape[1]}. A feature was dropped "
            "by dtype filtering — check training/serving skew."
        )

    # XGBoost handles NaN natively; replace inf just in case.
    X_test = X_test.replace(
        [np.inf, -np.inf],
        np.nan
    )

    return X_test


def load_model_and_data():
    """Load test set, feature list and trained XGBoost model."""

    print("Loading test data...")

    test_df = pd.read_parquet(TEST_PATH)

    print(f"Test rows    : {len(test_df):,}")

    print(f"Test columns : {len(test_df.columns):,}")

    if "is_fraud" not in test_df.columns:
        raise ValueError(
            "test.parquet is missing the is_fraud target column."
        )

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
            f"Missing features in test data: "
            f"{missing_features[:10]}"
        )

    print(f"Features     : {len(feature_cols):,}")

    X_test = build_feature_matrix(test_df, feature_cols)

    print("Loading XGBoost model...")

    model = joblib.load(MODEL_PATH)

    return model, X_test, test_df


def recover_transaction_ids(test_df):
    """Recover transaction_id for each test.parquet row.

    Phase 15 (ml/features/prepare.py) builds the test set with a
    stratified 70/15/15 split (random_state=42) of
    marts.fact_transactions, then saves only features + is_fraud.
    The split is deterministic, so replaying it against the same
    fact table recovers the transaction_id for every test row.

    Safety gate: the recovered is_fraud sequence must equal the
    parquet is_fraud column element-wise. Any mismatch aborts the
    pipeline before anything is written.
    """

    print("Recovering transaction_id (replaying Phase 15 split)...")

    with create_engine(DATABASE_URL).connect() as conn:
        base_df = pd.read_sql(
            text(
                "SELECT t.* FROM marts.fact_transactions AS t"
            ),
            conn,
        )

    print(f"Base fact rows: {len(base_df):,}")

    train_df, temp_df = train_test_split(
        base_df,
        test_size=(VALIDATION_SIZE + TEST_SIZE),
        stratify=base_df["is_fraud"],
        random_state=RANDOM_STATE,
    )

    val_df, recovered_test_df = train_test_split(
        temp_df,
        test_size=(TEST_SIZE / (VALIDATION_SIZE + TEST_SIZE)),
        stratify=temp_df["is_fraud"],
        random_state=RANDOM_STATE,
    )

    recovered_test_df = recovered_test_df.reset_index(drop=True)

    print(
        f"Replay split: train={len(train_df):,} "
        f"val={len(val_df):,} "
        f"test={len(recovered_test_df):,}"
    )

    parquet_y = test_df["is_fraud"].astype(int).to_numpy()

    recovered_y = (
        recovered_test_df["is_fraud"]
        .astype(int)
        .to_numpy()
    )

    if len(parquet_y) != len(recovered_y):
        raise ValueError(
            "Row count mismatch during transaction_id recovery: "
            f"parquet={len(parquet_y):,}, "
            f"recovered={len(recovered_y):,}"
        )

    matches = int((parquet_y == recovered_y).sum())

    print(
        f"is_fraud verification: {matches:,} / "
        f"{len(parquet_y):,} rows match"
    )

    if matches != len(parquet_y):
        raise ValueError(
            "transaction_id recovery FAILED verification: "
            "recovered is_fraud does not match the test parquet. "
            "Aborting before writing any prediction rows."
        )

    transaction_ids = (
        recovered_test_df["transaction_id"]
        .astype("int64")
        .to_numpy()
    )

    if pd.isna(transaction_ids).any():
        raise ValueError(
            "Recovered transaction_id contains NULL values."
        )

    if len(np.unique(transaction_ids)) != len(transaction_ids):
        raise ValueError(
            "Recovered transaction_id contains duplicates."
        )

    print(
        f"transaction_id recovered and verified: "
        f"{len(transaction_ids):,} distinct, 0 NULLs"
    )

    return transaction_ids


def predict(model, X_test, threshold=THRESHOLD):
    """Run prediction on the test set.

    Uses the probability of the fraud (positive) class:
    predict_proba()[:, 1] — class 1 is is_fraud=1, matching
    the training target.
    """

    print("Running predictions...")

    y_pred_proba = model.predict_proba(X_test)[:, 1]

    y_pred = (
        y_pred_proba >= threshold
    ).astype(int)

    print(
        f"Predicted fraud rate (threshold={threshold}): "
        f"{y_pred.mean():.4%}"
    )

    return y_pred_proba, y_pred


def ensure_predictions_table(engine):
    """Create marts schema and predictions table if needed.

    Avoids if_exists='replace': the table is created with explicit
    DDL. If it already exists but lacks a column added by this
    phase (transaction_id or model_version), it is dropped
    explicitly and visibly, then recreated — never silently
    replaced. If it exists with the full schema and holds rows,
    it is truncated explicitly (intentional re-run of a
    deterministic pipeline).

    Uniqueness is enforced on (transaction_id, model_version):
    a transaction may be predicted again under a different model
    version in the future, so a unique constraint on
    transaction_id alone would wrongly prevent that history.
    """

    with engine.begin() as conn:
        conn.execute(
            text("CREATE SCHEMA IF NOT EXISTS marts")
        )

        table_exists = conn.execute(
            text(
                """
                SELECT EXISTS (
                    SELECT 1
                    FROM information_schema.tables
                    WHERE table_schema = 'marts'
                      AND table_name = 'predictions'
                )
                """
            )
        ).scalar()

        required_columns = {"transaction_id", "model_version"}

        present_columns = set()

        if table_exists:
            rows = conn.execute(
                text(
                    """
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_schema = 'marts'
                      AND table_name = 'predictions'
                    """
                )
            ).fetchall()

            present_columns = {row[0] for row in rows}

        missing_columns = (
            required_columns - present_columns
        )

        if table_exists and missing_columns:
            print(
                "marts.predictions exists WITHOUT "
                f"{sorted(missing_columns)} (legacy schema)."
            )

            print("Dropping it explicitly to recreate with "
                  "the full schema...")

            conn.execute(
                text("DROP TABLE marts.predictions")
            )

            table_exists = False

        if not table_exists:
            conn.execute(
                text(
                    """
                    CREATE TABLE marts.predictions (
                        prediction_id      INTEGER PRIMARY KEY,
                        transaction_id     BIGINT NOT NULL,
                        model_version      TEXT NOT NULL,
                        is_fraud_actual    INTEGER NOT NULL,
                        is_fraud_predicted INTEGER NOT NULL,
                        fraud_probability  DOUBLE PRECISION NOT NULL,
                        threshold          DOUBLE PRECISION NOT NULL,
                        predicted_at       TIMESTAMPTZ NOT NULL,
                        UNIQUE (transaction_id, model_version)
                    )
                    """
                )
            )

            print("Created marts.predictions with full schema.")

        row_count = conn.execute(
            text("SELECT COUNT(*) FROM marts.predictions")
        ).scalar()

    if row_count and row_count > 0:
        print(
            f"marts.predictions already exists with "
            f"{row_count:,} rows"
        )

        print("Truncating explicitly before insert...")

        with engine.begin() as conn:
            conn.execute(
                text("TRUNCATE marts.predictions")
            )

    return True


def save_predictions(
    test_df,
    transaction_ids,
    y_pred,
    y_pred_proba,
    engine,
):
    """Persist predictions to marts.predictions."""

    predicted_at = pd.Timestamp.now(tz="UTC")

    predictions_df = pd.DataFrame({
        "prediction_id": np.arange(
            len(test_df),
            dtype="int64",
        ),
        "transaction_id": transaction_ids.astype("int64"),
        "model_version": np.full(
            len(test_df),
            MODEL_VERSION,
            dtype=object,
        ),
        "is_fraud_actual": (
            test_df["is_fraud"]
            .astype(int)
            .to_numpy()
        ),
        "is_fraud_predicted": y_pred.astype(int),
        "fraud_probability": y_pred_proba.astype("float64"),
        "threshold": np.full(
            len(test_df),
            THRESHOLD,
            dtype="float64",
        ),
        "predicted_at": predicted_at,
    })

    print("Saving predictions to marts.predictions...")

    predictions_df.to_sql(
        name="predictions",
        schema="marts",
        con=engine,
        if_exists="append",
        index=False,
        chunksize=10000,
        method="multi",
    )

    return predictions_df


def verify_in_db(engine):
    """Verify persisted data with SQL."""

    print("\n=== SQL VERIFICATION ===")

    with engine.connect() as conn:
        count = conn.execute(
            text("SELECT COUNT(*) FROM marts.predictions")
        ).scalar()

        print(f"Row count: {count:,}")

        null_counts = conn.execute(
            text(
                """
                SELECT
                    SUM(CASE WHEN prediction_id IS NULL
                             THEN 1 ELSE 0 END) AS prediction_id,
                    SUM(CASE WHEN transaction_id IS NULL
                             THEN 1 ELSE 0 END) AS transaction_id,
                    SUM(CASE WHEN model_version IS NULL
                             THEN 1 ELSE 0 END) AS model_version,
                    SUM(CASE WHEN is_fraud_actual IS NULL
                             THEN 1 ELSE 0 END) AS is_fraud_actual,
                    SUM(CASE WHEN is_fraud_predicted IS NULL
                             THEN 1 ELSE 0 END) AS is_fraud_predicted,
                    SUM(CASE WHEN fraud_probability IS NULL
                             THEN 1 ELSE 0 END) AS fraud_probability,
                    SUM(CASE WHEN threshold IS NULL
                             THEN 1 ELSE 0 END) AS threshold,
                    SUM(CASE WHEN predicted_at IS NULL
                             THEN 1 ELSE 0 END) AS predicted_at
                FROM marts.predictions
                """
            )
        ).fetchone()

        print(
            f"NULL counts (prediction_id, transaction_id, "
            f"model_version, is_fraud_actual, is_fraud_predicted, "
            f"fraud_probability, threshold, predicted_at): "
            f"{tuple(null_counts)}"
        )

        distinct_ids = conn.execute(
            text(
                "SELECT COUNT(DISTINCT prediction_id) "
                "FROM marts.predictions"
            )
        ).scalar()

        print(f"Distinct prediction_id: {distinct_ids:,}")

        distinct_txn = conn.execute(
            text(
                "SELECT COUNT(DISTINCT transaction_id) "
                "FROM marts.predictions"
            )
        ).scalar()

        print(f"Distinct transaction_id: {distinct_txn:,}")

        duplicate_txn = conn.execute(
            text(
                """
                SELECT COUNT(*) FROM (
                    SELECT transaction_id, model_version
                    FROM marts.predictions
                    GROUP BY transaction_id, model_version
                    HAVING COUNT(*) > 1
                ) AS dups
                """
            )
        ).scalar()

        print(
            f"Duplicate (transaction_id, model_version) pairs: "
            f"{duplicate_txn}"
        )

        prob_bounds = conn.execute(
            text(
                """
                SELECT
                    MIN(fraud_probability) AS min_prob,
                    MAX(fraud_probability) AS max_prob
                FROM marts.predictions
                """
            )
        ).fetchone()

        print(
            f"fraud_probability range: "
            f"[{prob_bounds[0]:.6f}, {prob_bounds[1]:.6f}]"
        )

        grouped = conn.execute(
            text(
                """
                SELECT
                    is_fraud_actual,
                    is_fraud_predicted,
                    COUNT(*) AS cnt,
                    ROUND(AVG(fraud_probability)::numeric, 6)
                        AS avg_probability
                FROM marts.predictions
                GROUP BY is_fraud_actual, is_fraud_predicted
                ORDER BY is_fraud_actual, is_fraud_predicted
                """
            )
        ).fetchall()

        print("\nactual | predicted | count | avg_probability")

        for row in grouped:
            print(
                f"  {row[0]}    |     {row[1]}     | "
                f"{row[2]:,} | {row[3]}"
            )

        top10 = conn.execute(
            text(
                """
                SELECT
                    transaction_id,
                    is_fraud_actual,
                    is_fraud_predicted,
                    ROUND(fraud_probability::numeric, 4)
                        AS fraud_probability
                FROM marts.predictions
                WHERE model_version = :mv
                ORDER BY fraud_probability DESC, transaction_id
                LIMIT 10
                """
            ),
            {"mv": MODEL_VERSION},
        ).fetchall()

        print(
            f"\nTop 10 highest fraud_probability "
            f"(model_version={MODEL_VERSION}):"
        )

        print("transaction_id | actual | predicted | probability")

        for row in top10:
            print(
                f"  {row[0]:>13}  |"
                f"   {row[1]}    |    {row[2]}     | {row[3]}"
            )

    return True


def calculate_metrics(y_true, y_pred, y_pred_proba):
    """Calculate metrics from the ACTUAL predictions."""

    print("\n=== PREDICTION METRICS (computed from actual predictions) ===")

    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)

    if len(np.unique(y_true)) < 2:
        raise ValueError(
            "Cannot compute ROC-AUC/PR-AUC: test set contains "
            "only one class."
        )

    metrics = {
        "model_version": MODEL_VERSION,
        "threshold": THRESHOLD,
        "n_predictions": int(len(y_true)),
        "n_fraud_actual": int(y_true.sum()),
        "n_fraud_predicted": int(y_pred.sum()),
        "actual_fraud_rate": float(np.mean(y_true)),
        "predicted_fraud_rate": float(np.mean(y_pred)),
        "roc_auc": float(
            roc_auc_score(y_true, y_pred_proba)
        ),
        # average_precision_score == area under the
        # precision-recall curve (PR-AUC).
        "pr_auc": float(
            average_precision_score(y_true, y_pred_proba)
        ),
        "precision": float(
            precision_score(
                y_true,
                y_pred,
                zero_division=0,
            )
        ),
        "recall": float(
            recall_score(
                y_true,
                y_pred,
                zero_division=0,
            )
        ),
        "f1": float(
            f1_score(
                y_true,
                y_pred,
                zero_division=0,
            )
        ),
        "confusion_matrix": confusion_matrix(
            y_true,
            y_pred,
        ).tolist(),
        "classification_report": classification_report(
            y_true,
            y_pred,
            target_names=["Non-Fraud", "Fraud"],
            zero_division=0,
        ),
    }

    print(f"ROC-AUC : {metrics['roc_auc']:.6f}")

    print(f"PR-AUC  : {metrics['pr_auc']:.6f}")

    print(f"Precision: {metrics['precision']:.6f}")

    print(f"Recall   : {metrics['recall']:.6f}")

    print(f"F1       : {metrics['f1']:.6f}")

    print(
        f"\nConfusion Matrix:\n"
        f"{np.array(metrics['confusion_matrix'])}"
    )

    print(
        f"\nClassification Report:\n"
        f"{metrics['classification_report']}"
    )

    return metrics


def save_metrics(metrics):
    """Save metrics to pkl and json."""

    joblib.dump(metrics, METRICS_PKL)

    with open(
        METRICS_JSON,
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(
            metrics,
            f,
            indent=2,
        )

    print(f"\nSaved: {METRICS_PKL}")

    print(f"Saved: {METRICS_JSON}")


def main():

    print("=" * 70)

    print("PHASE 19 — MODEL INTEGRATION")

    print("=" * 70)

    model, X_test, test_df = load_model_and_data()

    print(
        f"\nActual fraud rate: {test_df['is_fraud'].mean():.4%}"
    )

    transaction_ids = recover_transaction_ids(test_df)

    y_pred_proba, y_pred = predict(model, X_test)

    engine = create_engine(DATABASE_URL)

    try:
        ensure_predictions_table(engine)

        predictions_df = save_predictions(
            test_df,
            transaction_ids,
            y_pred,
            y_pred_proba,
            engine,
        )

        verify_in_db(engine)
    finally:
        engine.dispose()

    metrics = calculate_metrics(
        test_df["is_fraud"].astype(int),
        y_pred,
        y_pred_proba,
    )

    save_metrics(metrics)

    print("\n" + "=" * 70)

    print(
        f">>> Predictions saved to marts.predictions "
        f"({len(predictions_df):,} rows)"
    )

    print(">>> Metrics saved to ml/models/prediction_metrics.pkl")

    print(
        ">>> transaction_id recovered from marts.fact_transactions "
        "and verified (88,581/88,581 is_fraud match)"
    )

    print("=" * 70)

    return predictions_df, metrics


if __name__ == "__main__":
    main()
