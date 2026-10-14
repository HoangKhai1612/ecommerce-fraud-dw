
"""Validate read-only SQL for the AI Assistant."""

import sqlglot
from sqlglot import exp

from ai_assistant.config import ALLOWED_SCHEMAS, MAX_ROWS

# Functions that are not appropriate for AI-generated analytical queries.
BLOCKED_FUNCTIONS = {
    "PG_SLEEP",
    "PG_READ_FILE",
    "PG_READ_BINARY_FILE",
    "PG_LS_DIR",
    "PG_STAT_FILE",
    "SET_CONFIG",
    "NEXTVAL",
    "SETVAL",
    "LO_IMPORT",
    "LO_EXPORT",
}

# Maximum subquery depth to prevent resource exhaustion.
MAX_SUBQUERY_DEPTH = 3

ALLOWED_ROOT_TYPES = (exp.Select,)


def validate_sql(sql: str) -> tuple[bool, str]:
    """
    Validate a single read-only SELECT query.

    Returns (True, normalized_sql) or (False, reason).
    """
    if not isinstance(sql, str) or not sql.strip():
        return False, "SQL không được để trống."

    try:
        statements = sqlglot.parse(sql, read="postgres")
    except Exception:
        return False, "Cú pháp SQL không hợp lệ."

    # Reject empty input and multiple statements.
    if len(statements) != 1 or statements[0] is None:
        return False, "Chỉ cho phép một câu lệnh SQL."

    tree = statements[0]

    # Only SELECT queries are accepted. WITH ... SELECT is represented
    # as a Select node with a WITH clause in SQLGlot.
    if not isinstance(tree, ALLOWED_ROOT_TYPES):
        return False, "Chỉ cho phép truy vấn SELECT."

    # Reject data-modifying constructs anywhere in the AST.
    forbidden_nodes = (
        exp.Insert,
        exp.Update,
        exp.Delete,
        exp.Drop,
        exp.Create,
        exp.Alter,
        exp.Command,
    )

    for node_type in forbidden_nodes:
        if tree.find(node_type):
            return False, "Truy vấn chứa cấu trúc không được phép."

    # Reject dangerous functions by their parsed function name.
    for function in tree.find_all(exp.Func):
        name = function.sql_name().upper()
        if name in BLOCKED_FUNCTIONS:
            return False, f"Hàm SQL không được phép: {name}."

    # Every table must explicitly use an allowed schema.
    tables = list(tree.find_all(exp.Table))
    if not tables:
        return False, "Truy vấn phải tham chiếu bảng dữ liệu được phép."

    # Collect CTE names to exclude them from schema validation
    cte_names = set()
    for cte in tree.args.get("with_", []):
        cte_names.add(cte.alias_or_name)

    # Also collect nested CTE names recursively
    def collect_cte_names(cte):
        for nested_cte in cte.args.get("with_", []):
            cte_names.add(nested_cte.alias_or_name)
            collect_cte_names(nested_cte)

    for cte in tree.args.get("with_", []):
        collect_cte_names(cte)

    for table in tables:
        # Skip CTE references (they don't have a schema)
        if table.name in cte_names:
            continue

        schema = table.db
        if not schema or schema not in ALLOWED_SCHEMAS:
            return False, "Bảng thuộc schema không được phép."

        if table.catalog:
            return False, "Không cho phép truy vấn cross-database."

    # Recursively validate CTEs for allowed schemas
    def validate_cte(cte):
        cte_tables = list(cte.find_all(exp.Table))
        for table in cte_tables:
            # Skip CTE references (they don't have a schema)
            if table.name in cte_names:
                continue
            schema = table.db
            if not schema or schema not in ALLOWED_SCHEMAS:
                return False, "Bảng trong CTE thuộc schema không được phép."
            if table.catalog:
                return False, "Không cho phép truy vấn cross-database."
        return True, None

    # Check CTEs (the key is "with_" in SQLGlot)
    for cte in tree.args.get("with_", []):
        valid, err = validate_cte(cte)
        if not valid:
            return False, err

    # Validate subquery depth to prevent resource exhaustion
    def check_subquery_depth(node, depth=0):
        if depth > MAX_SUBQUERY_DEPTH:
            return False
        for child in node.iter_expressions():
            if isinstance(child, exp.Subquery):
                if not check_subquery_depth(child, depth + 1):
                    return False
            elif hasattr(child, 'iter_expressions'):
                if not check_subquery_depth(child, depth):
                    return False
        return True

    if not check_subquery_depth(tree):
        return False, f"Độ sâu subquery vượt quá giới hạn cho phép ({MAX_SUBQUERY_DEPTH})."

    # Reject comments that could be used for injection attempts
    # SQLGlot strips comments during parsing, but we check the original SQL
    if "--" in sql or "/*" in sql:
        return False, "Comment không được phép trong truy vấn."

    # Apply a maximum row limit using the parsed syntax tree.
    existing_limit = tree.args.get("limit")

    if existing_limit is None:
        tree = tree.limit(MAX_ROWS)
    else:
        limit_expression = existing_limit.expression

        # Require a simple non-negative integer limit.
        if not isinstance(limit_expression, exp.Literal):
            return False, "LIMIT phải là một số nguyên cố định."

        if limit_expression.is_string:
            return False, "LIMIT phải là một số nguyên."

        try:
            requested_limit = int(limit_expression.this)
        except (ValueError, TypeError):
            return False, "LIMIT không hợp lệ."

        if requested_limit < 0:
            return False, "LIMIT không được âm."

        if requested_limit > MAX_ROWS:
            tree = tree.limit(MAX_ROWS)

    return True, tree.sql(dialect="postgres")


def make_readonly_query(sql: str) -> str:
    """Validate SQL or raise ValueError."""
    is_valid, result = validate_sql(sql)

    if not is_valid:
        raise ValueError(result)

    return result


def build_parameterized_query(template: str, params: dict) -> tuple[str, tuple]:
    """
    Build a parameterized query safely.

    Args:
        template: SQL template with %s placeholders for parameters
        params: Dictionary of parameter values

    Returns:
        Tuple of (sql_string, params_tuple) for use with psycopg cursor.execute()

    Example:
        sql, params = build_parameterized_query(
            "SELECT * FROM marts.fact_transactions WHERE transaction_id = %s LIMIT %s",
            {"tx_id": 123, "limit": 10}
        )
        cursor.execute(sql, params)
    """
    # Replace placeholders with dummy values for validation
    import re
    placeholder_count = len(re.findall(r'%s', template))
    if placeholder_count != len(params):
        raise ValueError("Number of placeholders does not match number of parameters")

    # Create a dummy SQL for validation by replacing %s with appropriate dummy values
    # We need to be careful about context - for LIMIT we use a number, for WHERE we use a string/number
    dummy_values = []
    for i, (key, value) in enumerate(params.items()):
        if isinstance(value, int):
            dummy_values.append("1")
        elif isinstance(value, float):
            dummy_values.append("1.0")
        else:
            dummy_values.append("'dummy'")

    # Replace placeholders sequentially
    validation_sql = template
    for dummy in dummy_values:
        validation_sql = validation_sql.replace("%s", dummy, 1)

    # Validate the template with dummy values
    is_valid, normalized = validate_sql(validation_sql)
    if not is_valid:
        raise ValueError(f"Template validation failed: {normalized}")

    param_values = tuple(params.values())
    return normalized, param_values
