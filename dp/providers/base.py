from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator

DEFAULT_TEMPERATURE = 0.2
DEFAULT_MAX_TOKENS = 2048


class ProviderError(RuntimeError):
    pass


class LLMProvider(ABC):
    name: str
    resolved_model: str | None = None

    @abstractmethod
    async def generate(
        self,
        messages: list[dict[str, str]],
        model: str,
        *,
        temperature: float = DEFAULT_TEMPERATURE,
        max_tokens: int | None = None,
    ) -> str:
        raise NotImplementedError

    async def generate_stream(
        self,
        messages: list[dict[str, str]],
        model: str,
        *,
        temperature: float = DEFAULT_TEMPERATURE,
        max_tokens: int | None = None,
    ) -> AsyncIterator[str]:
        yield await self.generate(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )
