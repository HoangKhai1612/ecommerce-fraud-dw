"""DeepSeek provider implementation."""
import logging
import os
from langchain_openai import ChatOpenAI
from ai_assistant.providers.base import AIProvider

logger = logging.getLogger(__name__)


class DeepSeekProvider(AIProvider):
    def __init__(self, api_key: str = None, model: str = None, base_url: str = None, timeout: int = None):
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY", "")
        self.model = model or os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
        self.base_url = base_url or os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
        self.timeout = timeout or int(os.getenv("DEEPSEEK_TIMEOUT_SECONDS", "60"))
        if not self.api_key:
            raise ValueError("DeepSeek API key not configured")
        self.llm = ChatOpenAI(
            model=self.model,
            api_key=self.api_key,
            base_url=self.base_url,
            temperature=0,
            timeout=self.timeout,
        )

    def invoke(self, prompt: str) -> str:
        try:
            response = self.llm.invoke(prompt)
            return str(response.content).strip()
        except Exception as e:
            logger.error("DeepSeek provider error: %s", e)
            raise
