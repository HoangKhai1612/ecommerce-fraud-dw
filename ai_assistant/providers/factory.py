"""AI Provider factory."""
import logging
import os
from ai_assistant.providers.base import AIProvider
from ai_assistant.providers.ollama_provider import OllamaProvider

logger = logging.getLogger(__name__)


def get_provider() -> AIProvider:
    provider_type = os.getenv("AI_PROVIDER", "ollama").lower()
    if provider_type == "deepseek":
        try:
            api_key = os.getenv("DEEPSEEK_API_KEY", "")
            if not api_key:
                logger.warning("DEEPSEEK_API_KEY not set, falling back to Ollama")
                return OllamaProvider()
            from ai_assistant.providers.deepseek_provider import DeepSeekProvider
            return DeepSeekProvider()
        except Exception as e:
            logger.warning("Failed to initialize DeepSeek provider, falling back to Ollama: %s", e)
            return OllamaProvider()
    return OllamaProvider()
