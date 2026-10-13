"""
Phase 19 — automated tests for ml/predict.py.

Run from the project root:

    .venv\\Scripts\\python.exe -m pytest ml/tests -v

Test categories:
- Unit tests: feature matrix building, threshold
  classification, metrics calculation, error handling
  (use synthetic data or mocks).
- Integration tests: real artifact loading, real model
  prediction, transaction_id recovery (read-only DB),
  PostgreSQL roundtrip on a SCRATCH table (never
  touches marts.predictions).

Idempotency of the real pipeline is verified separately
by the controlled double-run documented in
docs/19_model_integration/model_integration.md
(Bước H), not by writing to marts.predictions here.
"""

import json

import joblib
import numpy as np
import pandas as pd
import pytest
from sqlalchemy import create_engine, text

import ml.predict as predict


# ---------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------

@pytest.fixture(scope="module")
def loaded():
    """Load the real test set, feature matrix and model once."""

    return predict.load_model_and_data()


@pytest.fixture(scope="module")
def model(loaded):
    return loaded[0]


@pytest.fixture(scope="module")
def x_test(loaded):
    return loaded[1]


@pytest.fixture(scope="module")
def test_df(loaded):
    return loaded[2]


class FakeModel:
    """Minimal model stub returning fixed fraud probabilities."""

    def __init__(self, probas):
        self._probas = np.asarray(probas, dtype="float64")

    def predict_proba(self, X):
        n = len(X)

        if n != len(self._probas):
            raise AssertionError(
                f"FakeModel expects {len(self._probas)} rows, "
                f"got {n}"
            )

        return np.column_stack(
            [1.0 - self._probas, self._probas]
        )


# ---------------------------------------------------------------------
# 1. Load artifact and verify schema
# ---------------------------------------------------------------------

def test_load_model_and_data(loaded, test_df, x_test):
    """Integration: real artifacts load with the right shapes."""

    model, X_test, df = loaded

    assert len(df) == 88_581

    assert len(X_test) == 88_581

    assert X_test.shape[1] == 1_014

    assert "is_fraud" in df.columns

    assert df["is_fraud"].sum() == 3_099

    with open(predict.FEATURE_COLS_PATH) as f:
        feature_cols = json.load(f)

    assert list(X_test.columns) == feature_cols

    assert all(
        pd.api.types.is_numeric_dtype(X_test[c])
        for c in X_test.columns
    )


def test_load_model_and_data_rejects_missing_model(
    monkeypatch,
    tmp_path,
):
    """Unit: a missing model artifact fails loudly."""

    monkeypatch.setattr(
        predict,
        "MODEL_PATH",
        tmp_path / "does_not_exist.pkl",
    )

    with pytest.raises((FileNotFoundError, OSError)):
        predict.load_model_and_data()


def test_load_model_and_data_rejects_unknown_feature(
    monkeypatch,
    tmp_path,
):
    """Unit: a feature list referencing an unknown column
    fails loudly instead of silently predicting on wrong
    inputs."""

    bogus = tmp_path / "bogus_features.json"

    bogus.write_text(
        json.dumps(["num__c14", "no_such_feature"]),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        predict,
        "FEATURE_COLS_PATH",
        bogus,
    )

    with pytest.raises(ValueError, match="[Mm]issing features"):
        predict.load_model_and_data()


# ---------------------------------------------------------------------
# 2. Feature order and dtype validation
# ---------------------------------------------------------------------

def test_build_feature_matrix_preserves_order_and_types():
    """Unit: column order follows feature_cols and bool
    columns are converted to int before dtype filtering."""

    df = pd.DataFrame({
        "f_bool": [True, False, True],
        "f_int": [1, 2, 3],
        "f_float": [0.1, 0.2, 0.3],
    })

    X = predict.build_feature_matrix(
        df,
        ["f_bool", "f_int", "f_float"],
    )

    assert list(X.columns) == ["f_bool", "f_int", "f_float"]

    assert X["f_bool"].tolist() == [1, 0, 1]

    assert X.shape[1] == 3


def test_build_feature_matrix_replaces_inf_with_nan():
    """Unit: infinite values become NaN (XGBoost handles
    NaN natively)."""

    df = pd.DataFrame({
        "f1": [1.0, np.inf, -np.inf],
        "f2": [0.1, 0.2, 0.3],
    })

    X = predict.build_feature_matrix(df, ["f1", "f2"])

    assert X["f1"].isna().sum() == 2

    assert np.isfinite(X["f2"]).all()


def test_build_feature_matrix_rejects_dropped_columns():
    """Unit: a feature lost to dtype filtering raises
    instead of silently shrinking the matrix."""

    df = pd.DataFrame({
        "f_int": [1, 2, 3],
        "f_str": ["a", "b", "c"],
    })

    with pytest.raises(ValueError, match="[Ff]eature count"):
        predict.build_feature_matrix(df, ["f_int", "f_str"])


# ---------------------------------------------------------------------
# 3-5. Prediction, probability and threshold classification
# ---------------------------------------------------------------------

def test_predict_probabilities_and_threshold():
    """Unit: fraud-class probability and threshold
    classification are consistent."""

    probas = np.array([0.1, 0.4, 0.5, 0.6, 0.9])

    fake = FakeModel(probas)

    X = pd.DataFrame({"f": range(len(probas))})

    y_pred_proba, y_pred = predict.predict(fake, X)

    np.testing.assert_allclose(y_pred_proba, probas)

    np.testing.assert_array_equal(
        y_pred,
        (probas >= predict.THRESHOLD).astype(int),
    )

    assert y_pred.sum() == 3


def test_predict_real_model_proba_bounds(model, x_test):
    """Integration: the real XGBoost model produces finite
    probabilities in [0, 1] for every test row."""

    y_pred_proba, y_pred = predict.predict(model, x_test)

    assert len(y_pred_proba) == 88_581

    assert np.isfinite(y_pred_proba).all()

    assert (y_pred_proba >= 0.0).all()

    assert (y_pred_proba <= 1.0).all()

    assert set(np.unique(y_pred)) <= {0, 1}


# ---------------------------------------------------------------------
# 6. Transaction ID uniqueness (integration, read-only DB)
# ---------------------------------------------------------------------

def test_transaction_id_recovery(test_df):
    """Integration: replaying the Phase 15 split recovers
    88,581 distinct, non-NULL transaction_ids and passes
    the is_fraud verification gate."""

    transaction_ids = predict.recover_transaction_ids(test_df)

    assert len(transaction_ids) == 88_581

    assert len(np.unique(transaction_ids)) == 88_581

    assert not pd.isna(transaction_ids).any()


# ---------------------------------------------------------------------
# 7. Metrics calculation
# ---------------------------------------------------------------------

def test_metrics_calculation():
    """Unit: metrics on a known small case."""

    y_true = np.array([0, 0, 1, 1])

    y_pred = np.array([0, 1, 1, 1])

    y_proba = np.array([0.1, 0.7, 0.6, 0.9])

    metrics = predict.calculate_metrics(y_true, y_pred, y_proba)

    # confusion matrix: TN=1, FP=1, FN=0, TP=2
    assert metrics["confusion_matrix"] == [[1, 1], [0, 2]]

    assert metrics["precision"] == pytest.approx(2 / 3)

    assert metrics["recall"] == pytest.approx(1.0)

    assert metrics["f1"] == pytest.approx(0.8)

    assert metrics["roc_auc"] == pytest.approx(0.75)

    # AP = 0.5 * 1.0 + 0.5 * (2/3)
    assert metrics["pr_auc"] == pytest.approx(5 / 6)

    assert metrics["n_predictions"] == 4

    assert metrics["n_fraud_actual"] == 2

    assert metrics["n_fraud_predicted"] == 3

    assert "classification_report" in metrics

    assert "Non-Fraud" in metrics["classification_report"]


def test_metrics_single_class_raises():
    """Unit: ROC-AUC/PR-AUC are undefined for a single-class
    test set — the pipeline must fail loudly, not silently
    emit wrong numbers."""

    y_true = np.zeros(10, dtype=int)

    y_pred = np.zeros(10, dtype=int)

    y_proba = np.full(10, 0.1)

    with pytest.raises(ValueError, match="only one class"):
        predict.calculate_metrics(y_true, y_pred, y_proba)


# ---------------------------------------------------------------------
# 8. PostgreSQL write path (scratch table — never touches
#    marts.predictions)
# ---------------------------------------------------------------------

def test_postgres_roundtrip_scratch_table():
    """Integration: the same write/read mechanisms used by
    predict.py (to_sql append + SQL verification queries)
    work against a scratch schema, and cleanup removes it."""

    engine = create_engine(predict.DATABASE_URL)

    schema = "marts_tests"

    table = "scratch_roundtrip"

    try:
        with engine.begin() as conn:
            conn.execute(
                text(f"CREATE SCHEMA IF NOT EXISTS {schema}")
            )

            conn.execute(
                text(f"DROP TABLE IF EXISTS {schema}.{table}")
            )

            conn.execute(
                text(
                    f"""
                    CREATE TABLE {schema}.{table} (
                        transaction_id BIGINT NOT NULL,
                        model_version  TEXT NOT NULL,
                        fraud_probability DOUBLE PRECISION NOT NULL,
                        UNIQUE (transaction_id, model_version)
                    )
                    """
                )
            )

        rows = pd.DataFrame({
            "transaction_id": [101, 102, 103],
            "model_version": ["test"] * 3,
            "fraud_probability": [0.25, 0.5, 0.75],
        })

        rows.to_sql(
            table,
            schema=schema,
            con=engine,
            if_exists="append",
            index=False,
        )

        with engine.connect() as conn:
            count = conn.execute(
                text(f"SELECT COUNT(*) FROM {schema}.{table}")
            ).scalar()

            assert count == 3

            dups = conn.execute(
                text(
                    f"""
                    SELECT COUNT(*) FROM (
                        SELECT transaction_id, model_version
                        FROM {schema}.{table}
                        GROUP BY transaction_id, model_version
                        HAVING COUNT(*) > 1
                    ) AS dups
                    """
                )
            ).scalar()

            assert dups == 0

            # Composite unique rejects a duplicate
            # (transaction_id, model_version) pair.
            with pytest.raises(Exception):
                with engine.begin() as conn:
                    conn.execute(
                        text(
                            f"""
                            INSERT INTO {schema}.{table}
                            VALUES (101, 'test', 0.99)
                            """
                        )
                    )

    finally:
        with engine.begin() as conn:
            conn.execute(
                text(f"DROP TABLE IF EXISTS {schema}.{table}")
            )

            conn.execute(
                text(f"DROP SCHEMA IF EXISTS {schema}")
            )

        engine.dispose()


# ---------------------------------------------------------------------
# 10. Metrics artifact
# ---------------------------------------------------------------------

def test_prediction_metrics_artifact():
    """Integration: after a pipeline run,
    prediction_metrics.json contains the required keys and
    values consistent with the test set."""

    if not predict.METRICS_JSON.exists():
        pytest.skip(
            "prediction_metrics.json not found — "
            "run ml/predict.py first"
        )

    with open(predict.METRICS_JSON) as f:
        metrics = json.load(f)

    required = {
        "model_version",
        "threshold",
        "n_predictions",
        "n_fraud_actual",
        "n_fraud_predicted",
        "actual_fraud_rate",
        "predicted_fraud_rate",
        "roc_auc",
        "pr_auc",
        "precision",
        "recall",
        "f1",
        "confusion_matrix",
        "classification_report",
    }

    assert required <= set(metrics.keys())

    assert metrics["n_predictions"] == 88_581

    assert metrics["n_fraud_actual"] == 3_099

    assert metrics["threshold"] == 0.5

    assert 0.0 <= metrics["roc_auc"] <= 1.0

    assert 0.0 <= metrics["pr_auc"] <= 1.0

    assert metrics["confusion_matrix"][0][0] + \
        metrics["confusion_matrix"][0][1] + \
        metrics["confusion_matrix"][1][0] + \
        metrics["confusion_matrix"][1][1] == 88_581
