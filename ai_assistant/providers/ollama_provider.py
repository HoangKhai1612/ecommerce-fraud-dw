"""Ollama provider implementation."""
import logging
from langchain_ollama import ChatOllama
from ai_assistant.config import LLM_MODEL, OLLAMA_BASE_URL, LLM_TIMEOUT_SECONDS
from ai_assistant.providers.base import AIProvider

logger = logging.getLogger(__name__)


class OllamaProvider(AIProvider):
    def __init__(self, model: str = None, base_url: str = None, timeout: int = None):
        self.model = model or LLM_MODEL
        self.base_url = base_url or OLLAMA_BASE_URL
        self.timeout = timeout or LLM_TIMEOUT_SECONDS
        self.llm = ChatOllama(
            model=self.model,
            base_url=self.base_url,
            temperature=0,
            validate_model_on_init=False,
            client_kwargs={"timeout": self.timeout},
        )

    def invoke(self, prompt: str) -> str:
        try:
            response = self.llm.invoke(prompt)
            return str(response.content).strip()
        except Exception as e:
            logger.error("Ollama provider error: %s", e)
            raise
