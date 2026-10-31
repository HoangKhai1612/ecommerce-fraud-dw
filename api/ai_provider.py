"""AI Provider abstraction for Phase 30 EXT-02."""
import os
from abc import ABC, abstractmethod

import httpx


class AIProvider(ABC):
    @abstractmethod
    def generate(self, prompt: str) -> str:
        pass

    @abstractmethod
    def is_available(self) -> bool:
        pass


class OllamaProvider(AIProvider):
    def __init__(self, base_url: str, model: str, timeout: int = 60):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        self.client = httpx.Client(timeout=timeout)

    def generate(self, prompt: str) -> str:
        url = f"{self.base_url}/api/chat"
        response = self.client.post(
            url,
            json={
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "stream": False,
            },
        )
        response.raise_for_status()
        data = response.json()
        return data.get("message", {}).get("content", "")

    def is_available(self) -> bool:
        try:
            response = self.client.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception:
            return False


class DeepSeekProvider(AIProvider):
    def __init__(self, api_key: str, model: str = "deepseek-chat", base_url: str = "https://api.deepseek.com", timeout: int = 60):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.client = httpx.Client(timeout=timeout)

    def generate(self, prompt: str) -> str:
        if not self.api_key:
            raise ValueError("DeepSeek API key not configured")
        url = f"{self.base_url}/chat/completions"
        response = self.client.post(
            url,
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
            },
        )
        response.raise_for_status()
        data = response.json()
        return data.get("choices", [{}])[0].get("message", {}).get("content", "")

    def is_available(self) -> bool:
        return bool(self.api_key)


def get_ai_provider() -> AIProvider:
    provider_name = os.getenv("AI_PROVIDER", "ollama").lower()
    if provider_name == "deepseek":
        return DeepSeekProvider(
            api_key=os.getenv("DEEPSEEK_API_KEY", ""),
            model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
        )
    return OllamaProvider(
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        model=os.getenv("OLLAMA_MODEL", "llama3"),
    )
