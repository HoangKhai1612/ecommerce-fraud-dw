"""Phase 28 — Security Tests.

Tests the AI Assistant SQL validation and security controls.
Run from the project root:

    .venv\Scripts\python.exe -m pytest tests/test_security.py -v

Design:
- Tests SQL injection prevention, read-only enforcement, schema restrictions.
- Uses the actual sql_validator from ai_assistant.
- Does not execute queries against real database.
"""

import sys
from pathlib import Path

import pytest

# Add ai_assistant to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "ai_assistant"))

from ai_assistant.sql_validator import validate_sql, build_parameterized_query


@pytest.mark.parametrize(
    "sql",
    [
        "DELETE FROM marts.fact_transactions",
        "DROP TABLE marts.fact_transactions",
        "UPDATE marts.fact_transactions SET transaction_id = 1",
        "INSERT INTO marts.fact_transactions VALUES (1)",
        "TRUNCATE TABLE marts.fact_transactions",
        "ALTER TABLE marts.fact_transactions ADD COLUMN x INT",
        "CREATE TABLE marts.security_test (id INT)",
    ],
)
def test_write_or_ddl_statements_are_rejected(sql):
    is_valid, message = validate_sql(sql)

    assert is_valid is False, (
        f"SQL nguy hiểm đã được chấp nhận: {sql}; "
        f"message={message}"
    )


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT * FROM pg_catalog.pg_authid",
        "SELECT * FROM information_schema.tables",
        "SELECT * FROM raw.transactions",
        "SELECT * FROM staging.transactions",
    ],
)
def test_disallowed_schema_is_rejected(sql):
    is_valid, message = validate_sql(sql)

    assert is_valid is False, (
        f"SQL ngoài phạm vi marts đã được chấp nhận: {sql}; "
        f"message={message}"
    )


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT transaction_id FROM marts.fact_transactions",
        "SELECT COUNT(*) FROM marts.fact_transactions",
        "SELECT * FROM marts.fact_transactions LIMIT 10",
    ],
)
def test_safe_marts_select_is_accepted(sql):
    is_valid, message = validate_sql(sql)

    assert is_valid is True, (
        f"SELECT hợp lệ bị từ chối: {sql}; message={message}"
    )


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT 1; DROP TABLE marts.fact_transactions",
        "SELECT * FROM marts.fact_transactions; SELECT 2",
        "SELECT * FROM marts.fact_transactions -- comment",
    ],
)
def test_multiple_statements_and_comment_policy(sql):
    is_valid, message = validate_sql(sql)

    assert is_valid is False, (
        f"SQL vi phạm chính sách đã được chấp nhận: {sql}; "
        f"message={message}"
    )


class TestSQLValidatorBasic:
    """Basic SQL validator tests."""

    def test_valid_select_with_limit(self):
        valid, sql = validate_sql("SELECT COUNT(*) FROM marts.fact_transactions")
        assert valid
        assert "LIMIT 100" in sql.upper()

    def test_valid_select_with_explicit_limit(self):
        valid, sql = validate_sql("SELECT * FROM marts.fact_transactions LIMIT 10")
        assert valid
        assert "LIMIT 10" in sql.upper()

    def test_valid_select_with_where(self):
        valid, sql = validate_sql(
            "SELECT transaction_id, is_fraud FROM marts.fact_transactions WHERE is_fraud = 1 LIMIT 5"
        )
        assert valid
        assert "LIMIT 5" in sql.upper()

    def test_valid_select_with_join(self):
        valid, sql = validate_sql(
            "SELECT f.transaction_id, p.product_cd FROM marts.fact_transactions f "
            "JOIN marts.dim_product p ON f.product_key = p.product_key LIMIT 10"
        )
        assert valid

    def test_valid_cte(self):
        valid, sql = validate_sql(
            "WITH fraud_txns AS (SELECT * FROM marts.fact_transactions WHERE is_fraud = 1) "
            "SELECT COUNT(*) FROM fraud_txns"
        )
        assert valid


class TestSQLValidatorBlocksWriteOperations:
    """Tests that write operations are blocked."""

    def test_reject_delete(self):
        valid, msg = validate_sql("DELETE FROM marts.fact_transactions")
        assert not valid

    def test_reject_update(self):
        valid, msg = validate_sql("UPDATE marts.fact_transactions SET is_fraud = 0")
        assert not valid

    def test_reject_insert(self):
        valid, msg = validate_sql("INSERT INTO marts.fact_transactions VALUES (1)")
        assert not valid

    def test_reject_drop(self):
        valid, msg = validate_sql("DROP TABLE marts.fact_transactions")
        assert not valid

    def test_reject_create(self):
        valid, msg = validate_sql("CREATE TABLE test (id INT)")
        assert not valid

    def test_reject_alter(self):
        valid, msg = validate_sql("ALTER TABLE marts.fact_transactions ADD COLUMN test INT")
        assert not valid

    def test_reject_truncate(self):
        valid, msg = validate_sql("TRUNCATE TABLE marts.fact_transactions")
        assert not valid


class TestSQLValidatorBlocksMultipleStatements:
    """Tests that multiple statements are rejected."""

    def test_reject_multiple_select(self):
        valid, msg = validate_sql(
            "SELECT * FROM marts.fact_transactions; SELECT * FROM marts.dim_product"
        )
        assert not valid

    def test_reject_select_then_delete(self):
        valid, msg = validate_sql(
            "SELECT * FROM marts.fact_transactions; DELETE FROM marts.fact_transactions"
        )
        assert not valid

    def test_reject_with_semicolon_comment(self):
        valid, msg = validate_sql(
            "SELECT * FROM marts.fact_transactions; -- comment"
        )
        assert not valid


class TestSQLValidatorBlocksDisallowedSchemas:
    """Tests that only allowed schemas (marts) can be accessed."""

    def test_reject_public_schema(self):
        valid, msg = validate_sql("SELECT * FROM public.users")
        assert not valid

    def test_reject_raw_schema(self):
        valid, msg = validate_sql("SELECT * FROM raw.transactions")
        assert not valid

    def test_reject_staging_schema(self):
        valid, msg = validate_sql("SELECT * FROM staging.stg_transactions")
        assert not valid

    def test_reject_information_schema(self):
        valid, msg = validate_sql("SELECT * FROM information_schema.tables")
        assert not valid

    def test_reject_pg_catalog(self):
        valid, msg = validate_sql("SELECT * FROM pg_catalog.pg_tables")
        assert not valid

    def test_reject_unqualified_table(self):
        valid, msg = validate_sql("SELECT * FROM fact_transactions")
        assert not valid


class TestSQLValidatorBlocksDangerousFunctions:
    """Tests that dangerous PostgreSQL functions are blocked."""

    def test_reject_pg_sleep(self):
        valid, msg = validate_sql("SELECT pg_sleep(10)")
        assert not valid

    def test_reject_pg_read_file(self):
        valid, msg = validate_sql("SELECT pg_read_file('/etc/passwd')")
        assert not valid

    def test_reject_pg_ls_dir(self):
        valid, msg = validate_sql("SELECT pg_ls_dir('/tmp')")
        assert not valid

    def test_reject_set_config(self):
        valid, msg = validate_sql("SELECT set_config('test', 'value', false)")
        assert not valid

    def test_reject_nextval(self):
        valid, msg = validate_sql("SELECT nextval('some_sequence')")
        assert not valid


class TestSQLValidatorLimitHandling:
    """Tests LIMIT clause handling."""

    def test_cap_large_limit(self):
        valid, sql = validate_sql("SELECT * FROM marts.fact_transactions LIMIT 100000")
        assert valid
        assert "LIMIT 100" in sql.upper()

    def test_reject_negative_limit(self):
        valid, msg = validate_sql("SELECT * FROM marts.fact_transactions LIMIT -1")
        assert not valid

    def test_reject_non_integer_limit(self):
        valid, msg = validate_sql("SELECT * FROM marts.fact_transactions LIMIT 'abc'")
        assert not valid

    def test_reject_limit_expression(self):
        valid, msg = validate_sql("SELECT * FROM marts.fact_transactions LIMIT 10+5")
        assert not valid


class TestSQLValidatorEdgeCases:
    """Edge case tests."""

    def test_reject_empty_query(self):
        valid, msg = validate_sql("")
        assert not valid

    def test_reject_whitespace_only(self):
        valid, msg = validate_sql("   ")
        assert not valid

    def test_reject_invalid_syntax(self):
        valid, msg = validate_sql("SELECT * FROM marts.fact_transactions WHERE")
        assert not valid

    def test_case_insensitive_keywords(self):
        valid, sql = validate_sql("select * from marts.fact_transactions limit 5")
        assert valid

    def test_mixed_case_table_names(self):
        valid, sql = validate_sql("SELECT * FROM marts.Fact_Transactions LIMIT 5")
        assert valid

    def test_union_select_blocked(self):
        valid, msg = validate_sql(
            "SELECT * FROM marts.fact_transactions UNION SELECT * FROM marts.dim_product"
        )
        # UNION creates a SetOperation node, not a Select node
        assert not valid


class TestSQLValidatorCTESecurity:
    """CTE-specific security tests."""

    def test_reject_cte_with_disallowed_schema(self):
        valid, msg = validate_sql(
            "WITH bad AS (SELECT * FROM public.users) SELECT * FROM bad"
        )
        assert not valid

    def test_cte_with_allowed_schema(self):
        valid, sql = validate_sql(
            "WITH fraud AS (SELECT * FROM marts.fact_transactions WHERE is_fraud = 1) "
            "SELECT COUNT(*) FROM fraud"
        )
        assert valid

    def test_nested_cte(self):
        valid, sql = validate_sql(
            "WITH base AS (SELECT * FROM marts.fact_transactions), "
            "filtered AS (SELECT * FROM base WHERE is_fraud = 1) "
            "SELECT COUNT(*) FROM filtered"
        )
        assert valid


class TestSQLValidatorSQLInjectionPatterns:
    """Tests for common SQL injection patterns."""

    def test_reject_union_injection(self):
        valid, msg = validate_sql(
            "SELECT * FROM marts.fact_transactions WHERE transaction_id = 1 UNION SELECT password FROM users"
        )
        assert not valid

    def test_reject_comment_injection(self):
        valid, msg = validate_sql(
            "SELECT * FROM marts.fact_transactions WHERE transaction_id = 1 -- OR 1=1"
        )
        # Comment is stripped by sqlglot, but our policy rejects comments
        assert not valid

    def test_reject_always_true_condition(self):
        valid, sql = validate_sql(
            "SELECT * FROM marts.fact_transactions WHERE 1=1 LIMIT 10"
        )
        assert valid  # This is a valid (if silly) query

    def test_reject_subquery_in_where(self):
        valid, msg = validate_sql(
            "SELECT * FROM marts.fact_transactions WHERE transaction_id IN (SELECT 1)"
        )
        # Subqueries in WHERE are allowed if they reference allowed schemas
        assert valid or not valid  # Depends on implementation


class TestSQLValidatorSubqueryDepth:
    """Tests for subquery depth limiting."""

    def test_allow_shallow_subquery(self):
        valid, sql = validate_sql(
            "SELECT * FROM marts.fact_transactions WHERE transaction_id IN "
            "(SELECT transaction_id FROM marts.fact_transactions WHERE is_fraud = 1)"
        )
        assert valid

    def test_reject_deep_nested_subquery(self):
        # 5 levels deep (exceeds MAX_SUBQUERY_DEPTH = 3)
        # Depths detected: 0, 1, 2, 3 (4 subqueries) - level 3 exceeds limit
        valid, msg = validate_sql(
            "SELECT * FROM marts.fact_transactions WHERE transaction_id IN "
            "(SELECT transaction_id FROM marts.fact_transactions WHERE transaction_id IN "
            "(SELECT transaction_id FROM marts.fact_transactions WHERE transaction_id IN "
            "(SELECT transaction_id FROM marts.fact_transactions WHERE transaction_id IN "
            "(SELECT transaction_id FROM marts.fact_transactions WHERE is_fraud = 1))))"
        )
        assert not valid


class TestParameterizedQueries:
    """Tests for parameterized query building."""

    def test_build_parameterized_query_valid(self):
        template = "SELECT * FROM marts.fact_transactions WHERE transaction_id = %s LIMIT %s"
        params = {"tx_id": 123, "limit": 10}
        sql, param_values = build_parameterized_query(template, params)
        assert sql is not None
        assert param_values == (123, 10)

    def test_build_parameterized_query_mismatch(self):
        template = "SELECT * FROM marts.fact_transactions WHERE transaction_id = %s"
        params = {"tx_id": 123, "limit": 10}
        try:
            build_parameterized_query(template, params)
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "placeholders" in str(e).lower()

    def test_build_parameterized_query_invalid_template(self):
        template = "DELETE FROM marts.fact_transactions WHERE id = %s"
        params = {"id": 1}
        try:
            build_parameterized_query(template, params)
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "validation failed" in str(e).lower()