"""Base LLM client interface."""

from abc import ABC, abstractmethod


class BaseLLM(ABC):
    @abstractmethod
    def complete(self, prompt: str, **kwargs) -> str:
        """Send a prompt and return the completion text.

        Optional kwargs: system, temperature, max_tokens.
        """
        ...


class DummyLLM(BaseLLM):
    """No-op LLM that returns empty string — used when no API key is configured."""

    def complete(self, prompt: str, **kwargs) -> str:
        return ""
