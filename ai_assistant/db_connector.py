
"""Read-only PostgreSQL connector."""

import psycopg

from ai_assistant.config import DB_CONFIG, QUERY_TIMEOUT_MS


MAX_ROWS_DEFAULT = 100


def execute_sql(sql: str, max_rows: int = MAX_ROWS_DEFAULT) -> list[dict]:
    """Execute validated SQL in a read-only transaction."""

    if not DB_CONFIG["user"] or not DB_CONFIG["password"]:
        raise RuntimeError("AI database credentials are not configured.")

    connection = None

    try:
        connection = psycopg.connect(**DB_CONFIG)

        with connection.cursor() as cursor:
            cursor.execute("SET TRANSACTION READ ONLY")
            cursor.execute(f"SET LOCAL statement_timeout = {QUERY_TIMEOUT_MS}")
            cursor.execute(sql)

            if cursor.description is None:
                raise RuntimeError("Query did not return a result set.")

            columns = [item.name for item in cursor.description]
            rows = cursor.fetchmany(max_rows + 1)

            if len(rows) > max_rows:
                raise RuntimeError("Query result exceeded the row limit.")

            return [
                dict(zip(columns, row))
                for row in rows
            ]

    finally:
        if connection is not None:
            connection.rollback()
            connection.close()
