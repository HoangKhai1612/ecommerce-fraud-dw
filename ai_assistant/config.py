
"""Configuration for the AI Assistant."""

import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

OLLAMA_BASE_URL = os.getenv(
    "OLLAMA_BASE_URL",
    "http://localhost:11434",
).rstrip("/")

LLM_MODEL = os.getenv("LLM_MODEL", "llama3")

# Local Windows development uses localhost.
# Docker Compose should override DB_HOST with the PostgreSQL service name.
DB_CONFIG = {
    "host": os.getenv("AI_DB_HOST", "localhost"),
    "port": int(os.getenv("AI_DB_PORT", "5432")),
    "dbname": os.getenv(
        "AI_DB_NAME",
        "ecommerce_fraud_dw",
    ),
    "user": os.getenv("AI_DB_USER", ""),
    "password": os.getenv("AI_DB_PASSWORD", ""),
    "connect_timeout": int(
        os.getenv("AI_DB_CONNECT_TIMEOUT", "5")
    ),
}

ALLOWED_SCHEMAS = {
    item.strip()
    for item in os.getenv("AI_ALLOWED_SCHEMAS", "marts").split(",")
    if item.strip()
}

MAX_ROWS = 100
QUERY_TIMEOUT_MS = 5000
LLM_TIMEOUT_SECONDS = 60

PROMPT_DIR = Path(__file__).resolve().parent / "prompts"
SYSTEM_PROMPT_PATH = PROMPT_DIR / "system_prompt.txt"
SQL_GENERATE_PROMPT_PATH = PROMPT_DIR / "generate_sql.txt"
