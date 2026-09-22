from dotenv import load_dotenv
import os

load_dotenv()

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

POSTGRES_RO_USER = os.getenv("POSTGRES_RO_USER", "ai_assistant_ro")
POSTGRES_RO_PASSWORD = os.getenv("POSTGRES_RO_PASSWORD", "ai_assistant_ro_pass")

