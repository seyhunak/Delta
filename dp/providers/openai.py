from __future__ import annotations

import json
import os
from collections.abc import AsyncIterator

import httpx

from dp.providers.base import DEFAULT_TEMPERATURE, LLMProvider, ProviderError


class OpenAIProvider(LLMProvider):
    name = "openai"

    def __init__(self, api_key: str | None = None, timeout_s: float = 60.0) -> None:
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.timeout_s = timeout_s
        if not self.api_key:
            raise ProviderError("OPENAI_API_KEY is not set")

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _payload(
        self,
        messages: list[dict[str, str]],
        model: str,
        temperature: float,
        max_tokens: int | None,
        stream: bool,
    ) -> dict:
        payload: dict = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "stream": stream,
        }
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        return payload

    async def generate(
        self,
        messages: list[dict[str, str]],
        model: str,
        *,
        temperature: float = DEFAULT_TEMPERATURE,
        max_tokens: int | None = None,
    ) -> str:
        self.resolved_model = model
        try:
            async with httpx.AsyncClient(timeout=self.timeout_s) as client:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers=self._headers(),
                    json=self._payload(messages, model, temperature, max_tokens, stream=False),
                )
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPError as exc:
            raise ProviderError(f"OpenAI request failed: {exc}") from exc

        try:
            content = data["choices"][0]["message"]["content"]
            return str(content).strip()
        except (KeyError, IndexError, TypeError, AttributeError) as exc:
            raise ProviderError("OpenAI response format was invalid") from exc

    async def generate_stream(
        self,
        messages: list[dict[str, str]],
        model: str,
        *,
        temperature: float = DEFAULT_TEMPERATURE,
        max_tokens: int | None = None,
    ) -> AsyncIterator[str]:
        self.resolved_model = model
        try:
            async with httpx.AsyncClient(timeout=self.timeout_s) as client:
                async with client.stream(
                    "POST",
                    "https://api.openai.com/v1/chat/completions",
                    headers=self._headers(),
                    json=self._payload(messages, model, temperature, max_tokens, stream=True),
                ) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        line = line.strip()
                        if not line.startswith("data:"):
                            continue
                        data_text = line[len("data:"):].strip()
                        if data_text == "[DONE]":
                            break
                        try:
                            event = json.loads(data_text)
                        except ValueError:
                            continue
                        try:
                            delta = event["choices"][0]["delta"].get("content")
                        except (KeyError, IndexError, TypeError, AttributeError):
                            continue
                        if delta:
                            yield str(delta)
        except httpx.HTTPError as exc:
            raise ProviderError(f"OpenAI stream failed: {exc}") from exc
