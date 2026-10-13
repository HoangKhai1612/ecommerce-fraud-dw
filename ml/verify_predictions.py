"""
Phase 19 — SQL Verification for marts.predictions.

Executes the verification queries against the actual
PostgreSQL database and records the REAL results.
Run from the project root:

    .venv\\Scripts\\python.exe ml\\verify_predictions.py
"""

import os
import warnings
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import URL, create_engine, text

warnings.filterwarnings("ignore")

load_dotenv()

DATABASE_URL = URL.create(
    drivername="postgresql+psycopg2",
    username=os.getenv("POSTGRES_USER", "postgres"),
    password=os.getenv("POSTGRES_PASSWORD", "postgres"),
    host=os.getenv("POSTGRES_HOST", "localhost"),
    port=int(os.getenv("POSTGRES_PORT", "5432")),
    database=os.getenv("POSTGRES_DB", "ecommerce_fraud_dw"),
)

MODEL_VERSION = "xgboost-v1-phase16"

SEPARATOR = "=" * 70


def run_query(conn, title, query, params=None):
    """Run one verification query and print results."""

    print()

    print(SEPARATOR)

    print(title)

    print(SEPARATOR)

    print(query.strip())

    print("-" * 70)

    df = pd.read_sql(
        text(query),
        conn,
        params=params or {},
    )

    print(df.to_string(index=False))

    return df


def main():

    print(SEPARATOR)

    print("PHASE 19 — SQL VERIFICATION: marts.predictions")

    print(SEPARATOR)

    engine = create_engine(DATABASE_URL)

    try:
        with engine.connect() as conn:
            # Table exists?
            exists = conn.execute(
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

            print(f"\nmarts.predictions exists: {exists}")

            if not exists:
                raise SystemExit(
                    "marts.predictions does not exist. "
                    "Run ml/predict.py first."
                )

            # 1. Total row count
            run_query(
                conn,
                "1. TOTAL ROW COUNT",
                """
                SELECT COUNT(*) AS total_rows
                FROM marts.predictions
                """,
            )

            # 2. Duplicate transaction check
            #    (per model_version — a transaction may be
            #     predicted again under a different version)
            run_query(
                conn,
                "2. DUPLICATE (transaction_id, model_version)",
                """
                SELECT
                    transaction_id,
                    model_version,
                    COUNT(*) AS n
                FROM marts.predictions
                GROUP BY transaction_id, model_version
                HAVING COUNT(*) > 1
                """,
            )

            # 3. NULL and invalid probability checks
            run_query(
                conn,
                "3. NULL AND INVALID PROBABILITY CHECKS",
                """
                SELECT
                    COUNT(*) FILTER (
                        WHERE transaction_id IS NULL
                    ) AS null_ids,
                    COUNT(*) FILTER (
                        WHERE model_version IS NULL
                    ) AS null_model_versions,
                    COUNT(*) FILTER (
                        WHERE fraud_probability IS NULL
                    ) AS null_probabilities,
                    COUNT(*) FILTER (
                        WHERE fraud_probability < 0
                        OR fraud_probability > 1
                    ) AS invalid_probabilities,
                    COUNT(*) FILTER (
                        WHERE is_fraud_actual IS NULL
                    ) AS null_actuals,
                    COUNT(*) FILTER (
                        WHERE is_fraud_predicted IS NULL
                    ) AS null_predictions
                FROM marts.predictions
                """,
            )

            # 4. Actual vs predicted labels
            run_query(
                conn,
                "4. ACTUAL VS PREDICTED LABELS",
                """
                SELECT
                    is_fraud_actual,
                    is_fraud_predicted,
                    COUNT(*) AS n,
                    AVG(fraud_probability) AS avg_probability
                FROM marts.predictions
                GROUP BY is_fraud_actual, is_fraud_predicted
                ORDER BY is_fraud_actual, is_fraud_predicted
                """,
            )

            # 5. Top 10 highest fraud probability
            run_query(
                conn,
                "5. TOP 10 HIGHEST FRAUD PROBABILITY",
                """
                SELECT
                    transaction_id,
                    is_fraud_actual,
                    is_fraud_predicted,
                    ROUND(fraud_probability::numeric, 4)
                        AS fraud_prob
                FROM marts.predictions
                WHERE model_version = :mv
                ORDER BY fraud_probability DESC, transaction_id
                LIMIT 10
                """,
                {"mv": MODEL_VERSION},
            )

            # 6. Model version and threshold distribution
            run_query(
                conn,
                "6. MODEL VERSION / THRESHOLD DISTRIBUTION",
                """
                SELECT
                    model_version,
                    threshold,
                    COUNT(*) AS n,
                    MIN(predicted_at) AS first_predicted_at,
                    MAX(predicted_at) AS last_predicted_at
                FROM marts.predictions
                GROUP BY model_version, threshold
                ORDER BY model_version, threshold
                """,
            )

            # 7. Join integrity against the fact table
            run_query(
                conn,
                "7. JOIN INTEGRITY VS marts.fact_transactions",
                """
                SELECT
                    COUNT(*) AS matched_rows,
                    SUM(CASE
                        WHEN f.is_fraud = p.is_fraud_actual
                        THEN 1 ELSE 0 END) AS fraud_flag_match
                FROM marts.predictions AS p
                JOIN marts.fact_transactions AS f
                  ON f.transaction_id = p.transaction_id
                WHERE p.model_version = :mv
                """,
                {"mv": MODEL_VERSION},
            )

            # 8. Schema and constraints
            run_query(
                conn,
                "8. TABLE COLUMNS AND TYPES",
                """
                SELECT
                    column_name,
                    data_type,
                    is_nullable
                FROM information_schema.columns
                WHERE table_schema = 'marts'
                  AND table_name = 'predictions'
                ORDER BY ordinal_position
                """,
            )

            run_query(
                conn,
                "9. TABLE CONSTRAINTS",
                """
                SELECT
                    constraint_name,
                    constraint_type
                FROM information_schema.table_constraints
                WHERE table_schema = 'marts'
                  AND table_name = 'predictions'
                ORDER BY constraint_type
                """,
            )

    finally:
        engine.dispose()

    print()

    print(SEPARATOR)

    print("SQL VERIFICATION COMPLETE")

    print(SEPARATOR)


if __name__ == "__main__":
    main()
