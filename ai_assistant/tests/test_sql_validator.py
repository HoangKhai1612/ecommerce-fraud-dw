
import pytest

from ai_assistant.sql_validator import validate_sql


def test_valid_select():
    valid, sql = validate_sql(
        "SELECT COUNT(*) FROM marts.fact_transactions"
    )
    assert valid
    assert "LIMIT 100" in sql.upper()


def test_reject_delete():
    valid, _ = validate_sql(
        "DELETE FROM marts.fact_transactions"
    )
    assert not valid


def test_reject_update():
    valid, _ = validate_sql(
        "UPDATE marts.fact_transactions SET is_fraud = 0"
    )
    assert not valid


def test_reject_insert():
    valid, _ = validate_sql(
        "INSERT INTO marts.fact_transactions VALUES (1)"
    )
    assert not valid


def test_reject_drop():
    valid, _ = validate_sql(
        "DROP TABLE marts.fact_transactions"
    )
    assert not valid


def test_reject_multiple_statements():
    valid, _ = validate_sql(
        "SELECT * FROM marts.fact_transactions; "
        "DELETE FROM marts.fact_transactions"
    )
    assert not valid


def test_reject_public_schema():
    valid, _ = validate_sql("SELECT * FROM public.users")
    assert not valid


def test_reject_unqualified_table():
    valid, _ = validate_sql("SELECT * FROM fact_transactions")
    assert not valid


def test_reject_unapproved_schema_in_cte():
    valid, _ = validate_sql(
        """
        WITH data AS (
            SELECT * FROM public.users
        )
        SELECT * FROM data
        """
    )
    assert not valid


def test_cap_large_limit():
    valid, sql = validate_sql(
        "SELECT * FROM marts.fact_transactions LIMIT 100000"
    )
    assert valid
    assert "LIMIT 100" in sql.upper()


def test_reject_negative_limit():
    valid, _ = validate_sql(
        "SELECT * FROM marts.fact_transactions LIMIT -1"
    )
    assert not valid


def test_reject_empty_query():
    valid, _ = validate_sql("")
    assert not valid
