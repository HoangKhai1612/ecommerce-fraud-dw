
"""Ollama-backed LLM service."""

from pathlib import Path

from langchain_ollama import ChatOllama

from ai_assistant.config import (
    LLM_MODEL,
    LLM_TIMEOUT_SECONDS,
    OLLAMA_BASE_URL,
    SYSTEM_PROMPT_PATH,
    SQL_GENERATE_PROMPT_PATH,
)

SYSTEM_PROMPT = SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")
SQL_PROMPT = SQL_GENERATE_PROMPT_PATH.read_text(encoding="utf-8")

llm = ChatOllama(
    model=LLM_MODEL,
    base_url=OLLAMA_BASE_URL,
    temperature=0,
    validate_model_on_init=False,
    client_kwargs={"timeout": LLM_TIMEOUT_SECONDS},
)


def _invoke(prompt: str) -> str:
    response = llm.invoke(prompt)
    return str(response.content).strip()


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
