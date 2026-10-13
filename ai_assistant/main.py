"""FastAPI entry point for the AI Assistant."""

import logging
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from ai_assistant.config import ALLOWED_SCHEMAS, MAX_ROWS
from ai_assistant.db_connector import execute_sql
from ai_assistant.llm_service import (
    answer_chat,
    classify_question,
    generate_sql,
    summarize_query_result,
)
from ai_assistant.sql_validator import validate_sql

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="E-commerce Fraud AI Assistant",
    version="1.0.0",
    description="Vietnamese AI assistant for read-only data analysis.",
)


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)


class ChatResponse(BaseModel):
    answer: str
    sql_query: str | None = None
    results: list[dict[str, Any]] | None = None


SCHEMA_CACHE: str | None = None


def get_schema_context() -> str:
    """Build schema context from actual database introspection."""
    global SCHEMA_CACHE

    if SCHEMA_CACHE is not None:
        return SCHEMA_CACHE

    try:
        # Get tables
        table_rows = execute_sql("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'marts'
            ORDER BY table_name
        """)

        parts = []
        for table_row in table_rows:
            table = table_row["table_name"]
            parts.append(f"Table: marts.{table}")

            # Get columns for this table
            col_rows = execute_sql(f"""
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_schema = 'marts' AND table_name = '{table}'
                ORDER BY ordinal_position
            """, max_rows=500)

            # For fact_transactions, only show key columns (too many otherwise)
            if table == "fact_transactions":
                key_cols = [
                    "transaction_key", "transaction_id", "is_fraud", "transaction_dt",
                    "product_key", "device_key", "transaction_amt", "product_cd",
                    "card1", "card2", "card3", "card4", "card5", "card6",
                    "addr1", "addr2", "dist1", "dist2",
                    "p_emaildomain", "r_emaildomain",
                    "device_type", "device_info"
                ]
                shown = 0
                for col_row in col_rows:
                    if col_row["column_name"] in key_cols:
                        parts.append(f"  - {col_row['column_name']} ({col_row['data_type']})")
                        shown += 1
                parts.append(f"  ... and {len(col_rows) - shown} more columns (V1-V339, C1-C14, D1-D15, M1-M9, id_01-id_38)")
            else:
                for col_row in col_rows:
                    parts.append(f"  - {col_row['column_name']} ({col_row['data_type']})")

            parts.append("")

        SCHEMA_CACHE = "\n".join(parts)
        return SCHEMA_CACHE

    except Exception as e:
        logger.warning("Failed to introspect schema, using fallback: %s", e)
        return "Allowed schemas: marts. Use only tables verified to exist in these schemas."


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "ai-assistant",
    }


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    question = request.question.strip()

    if not question:
        raise HTTPException(
            status_code=422,
            detail="Question must not be empty.",
        )

    try:
        question_type = classify_question(question)

        if question_type != "DATA":
            return ChatResponse(
                answer=answer_chat(question),
            )

        schema_context = get_schema_context()

        sql = generate_sql(question, schema_context)

        if sql.strip() == "CANNOT_ANSWER":
            return ChatResponse(
                answer=(
                    "Chưa thể tạo truy vấn phù hợp với schema "
                    "được cung cấp."
                ),
            )

        valid, checked_sql = validate_sql(sql)

        if not valid:
            logger.warning("Generated SQL was rejected by validator.")
            return ChatResponse(
                answer=(
                    "Truy vấn được đề xuất không vượt qua kiểm tra "
                    "an toàn. Dữ liệu chưa được truy vấn."
                ),
            )

        rows = execute_sql(checked_sql)
        rows = rows[:MAX_ROWS]

        answer = summarize_query_result(question, rows)

        return ChatResponse(
            answer=answer,
            sql_query=checked_sql,
            results=rows,
        )

    except HTTPException:
        raise
    except Exception:
        logger.exception("AI Assistant request failed.")
        raise HTTPException(
            status_code=503,
            detail=(
                "AI Assistant tạm thời không thể xử lý yêu cầu. "
                "Vui lòng kiểm tra dịch vụ LLM và database."
            ),
        ) from None