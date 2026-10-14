"""
Phase 25 — dbt Model & Data Quality Tests.

Tests the dbt data-quality rules defined in dbt/tests/ against
the real Data Warehouse. Requires a live PostgreSQL connection
(env vars POSTGRES_* must be set).

Run from the project root:

    .venv\\Scripts\\python.exe -m pytest tests/test_dbt.py -v

Design:
- These are INTEGRATION tests: they query the real DW.
- They do NOT run `dbt test` itself (that is done by
  test_end_to_end.py::TestDbt::test_dbt_tests_pass).
- Instead they verify the same invariants directly with SQL,
  so the tests are runnable without the Airflow container.
"""

from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

import pytest

from dotenv import load_dotenv
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

EXPECTED_RAW = {
    "raw.transactions": 590540,
    "raw.identity": 144233,
}

EXPECTED_FACT = 590540


@pytest.fixture(scope="module")
def db_engine():
    """Session-scoped engine against the real DW."""
    load_dotenv(PROJECT_ROOT / ".env")
    url = URL.create(
        drivername="postgresql+psycopg2",
        username=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD", "postgres"),
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        database=os.getenv("POSTGRES_DB", "ecommerce_fraud_dw"),
    )
    engine = create_engine(url, pool_pre_ping=True)
    yield engine
    engine.dispose()


def scalar(db_engine, sql):
    with db_engine.connect() as conn:
        return conn.execute(text(sql)).scalar()


def rows(db_engine, sql):
    with db_engine.connect() as conn:
        return conn.execute(text(sql)).fetchall()


# ---------------------------------------------------------------------
# Row counts
# ---------------------------------------------------------------------


class TestRowCounts:
    def test_raw_transactions_count(self, db_engine):
        count = scalar(db_engine, "SELECT COUNT(*) FROM raw.transactions")
        assert count == EXPECTED_RAW["raw.transactions"]

    def test_raw_identity_count(self, db_engine):
        count = scalar(db_engine, "SELECT COUNT(*) FROM raw.identity")
        assert count == EXPECTED_RAW["raw.identity"]

    def test_staging_transactions_count(self, db_engine):
        count = scalar(db_engine, "SELECT COUNT(*) FROM staging.stg_transactions")
        assert count == EXPECTED_FACT

    def test_marts_fact_count(self, db_engine):
        count = scalar(db_engine, "SELECT COUNT(*) FROM marts.fact_transactions")
        assert count == EXPECTED_FACT

    def test_dim_product_count(self, db_engine):
        count = scalar(db_engine, "SELECT COUNT(*) FROM marts.dim_product")
        assert count == 22

    def test_dim_device_count(self, db_engine):
        count = scalar(db_engine, "SELECT COUNT(*) FROM marts.dim_device")
        assert count == 1939

    def test_dim_date_count(self, db_engine):
        count = scalar(db_engine, "SELECT COUNT(*) FROM marts.dim_date")
        assert count == 183


# ---------------------------------------------------------------------
# Primary key uniqueness
# ---------------------------------------------------------------------


class TestPrimaryKeys:
    def test_raw_transactions_pk_unique(self, db_engine):
        dup = scalar(
            db_engine,
            """
            SELECT COUNT(*) FROM (
                SELECT "TransactionID" FROM raw.transactions
                GROUP BY "TransactionID" HAVING COUNT(*) > 1
            ) d
            """,
        )
        assert dup == 0

    def test_raw_identity_pk_unique(self, db_engine):
        dup = scalar(
            db_engine,
            """
            SELECT COUNT(*) FROM (
                SELECT "TransactionID" FROM raw.identity
                GROUP BY "TransactionID" HAVING COUNT(*) > 1
            ) d
            """,
        )
        assert dup == 0

    def test_marts_fact_transaction_id_unique(self, db_engine):
        dup = scalar(
            db_engine,
            """
            SELECT COUNT(*) FROM (
                SELECT transaction_id FROM marts.fact_transactions
                GROUP BY transaction_id HAVING COUNT(*) > 1
            ) d
            """,
        )
        assert dup == 0


# ---------------------------------------------------------------------
# Foreign key integrity
# ---------------------------------------------------------------------


class TestForeignKeys:
    def test_no_orphan_product_key(self, db_engine):
        orphan = scalar(
            db_engine,
            """
            SELECT COUNT(*) FROM marts.fact_transactions f
            LEFT JOIN marts.dim_product d ON f.product_key = d.product_key
            WHERE f.product_key IS NOT NULL AND d.product_key IS NULL
            """,
        )
        assert orphan == 0

    def test_no_orphan_device_key(self, db_engine):
        orphan = scalar(
            db_engine,
            """
            SELECT COUNT(*) FROM marts.fact_transactions f
            LEFT JOIN marts.dim_device d ON f.device_key = d.device_key
            WHERE f.device_key IS NOT NULL AND d.device_key IS NULL
            """,
        )
        assert orphan == 0

    def test_no_orphan_predictions(self, db_engine):
        orphan = scalar(
            db_engine,
            """
            SELECT COUNT(*) FROM marts.predictions p
            LEFT JOIN marts.fact_transactions f ON p.transaction_id = f.transaction_id
            WHERE f.transaction_id IS NULL
            """,
        )
        assert orphan == 0


# ---------------------------------------------------------------------
# Domain checks
# ---------------------------------------------------------------------


class TestDomain:
    def test_is_fraud_values_valid(self, db_engine):
        invalid = scalar(
            db_engine,
            """
            SELECT COUNT(*) FROM marts.fact_transactions
            WHERE is_fraud NOT IN (0, 1)
            """,
        )
        assert invalid == 0

    def test_transaction_amount_non_negative(self, db_engine):
        negative = scalar(
            db_engine,
            "SELECT COUNT(*) FROM marts.fact_transactions WHERE transaction_amt < 0"
        )
        assert negative == 0

    def test_predictions_probability_in_range(self, db_engine):
        out_of_range = scalar(
            db_engine,
            """
            SELECT COUNT(*) FROM marts.predictions
            WHERE fraud_probability < 0.0 OR fraud_probability > 1.0
            """,
        )
        assert out_of_range == 0

    def test_predictions_is_fraud_predicted_valid(self, db_engine):
        invalid = scalar(
            db_engine,
            """
            SELECT COUNT(*) FROM marts.predictions
            WHERE is_fraud_predicted NOT IN (0, 1)
            """,
        )
        assert invalid == 0


# ---------------------------------------------------------------------
# Staging <-> marts consistency
# ---------------------------------------------------------------------


class TestConsistency:
    def test_staging_equals_fact_count(self, db_engine):
        staging = scalar(db_engine, "SELECT COUNT(*) FROM staging.stg_transactions")
        fact = scalar(db_engine, "SELECT COUNT(*) FROM marts.fact_transactions")
        assert staging == fact

    def test_predictions_no_duplicates(self, db_engine):
        dup = scalar(
            db_engine,
            """
            SELECT COUNT(*) FROM (
                SELECT transaction_id, model_version
                FROM marts.predictions
                GROUP BY transaction_id, model_version
                HAVING COUNT(*) > 1
            ) d
            """,
        )
        assert dup == 0