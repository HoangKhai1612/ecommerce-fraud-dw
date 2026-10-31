"""LLM service with provider abstraction."""

from pathlib import Path

from ai_assistant.config import (
    LLM_MODEL,
    LLM_TIMEOUT_SECONDS,
    OLLAMA_BASE_URL,
    SYSTEM_PROMPT_PATH,
    SQL_GENERATE_PROMPT_PATH,
)
from ai_assistant.providers.factory import get_provider

SYSTEM_PROMPT = SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")
SQL_PROMPT = SQL_GENERATE_PROMPT_PATH.read_text(encoding="utf-8")

# Use provider abstraction
_provider = get_provider()


def _invoke(prompt: str) -> str:
    response = _provider.invoke(prompt)
    return str(response).strip() if not isinstance(response, str) else response.strip()


def classify_question(question: str) -> str:
    """Classify a question as DATA or CHAT."""

    prompt = f"""
Phân loại câu hỏi sau thành đúng một nhãn:
DATA: cần truy vấn số liệu hoặc dữ liệu trong database.
CHAT: hội thoại thông thường hoặc hỏi kiến thức chung về hệ thống.

Chỉ trả lời DATA hoặc CHAT.

Câu hỏi: {question}
Nhãn:
"""
    result = _invoke(prompt).upper().strip()

    if result == "DATA":
        return "DATA"

    return "CHAT"


def generate_sql(question: str, schema: str) -> str:
    prompt = SQL_PROMPT.format(
        schema=schema,
        question=question,
    )
    result = _invoke(prompt)

    if result.startswith("```"):
        lines = result.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        result = "\n".join(lines).strip()

    return result


def answer_chat(question: str) -> str:
    prompt = f"""
{SYSTEM_PROMPT}

Câu hỏi của người dùng:
{question}

Trả lời bằng tiếng Việt:
"""
    return _invoke(prompt)


def summarize_query_result(question: str, rows: list[dict]) -> str:
    prompt = f"""
{SYSTEM_PROMPT}

Câu hỏi: {question}

Kết quả truy vấn PostgreSQL thực tế:
{rows}

Hãy trả lời ngắn gọn bằng tiếng Việt, chỉ dựa trên kết quả được cung cấp.
Nếu kết quả rỗng, hãy nói rằng không tìm thấy dữ liệu phù hợp.
Không tự tạo thêm số liệu.
"""
    return _invoke(prompt)