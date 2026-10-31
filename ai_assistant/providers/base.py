"""Base AI Provider interface."""
from abc import ABC, abstractmethod

class AIProvider(ABC):
    @abstractmethod
    def invoke(self, prompt: str) -> str:
        """Invoke the LLM with a prompt and return response text."""
        pass
