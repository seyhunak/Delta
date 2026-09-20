from __future__ import annotations

import json
import os
from collections.abc import AsyncIterator

import httpx

from dp.providers.base import DEFAULT_MAX_TOKENS, DEFAULT_TEMPERATURE, LLMProvider, ProviderError


class AnthropicProvider(LLMProvider):
    name = "anthropic"

    def __init__(self, api_key: str | None = None, timeout_s: float = 60.0) -> None:
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.timeout_s = timeout_s
        if not self.api_key:
            raise ProviderError("ANTHROPIC_API_KEY is not set")

    def _headers(self) -> dict[str, str]:
        return {
            "x-api-key": self.api_key or "",
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }

    def _split_messages(self, messages: list[dict[str, str]]) -> tuple[str, list[dict[str, str]]]:
        system = ""
        anthropic_messages: list[dict[str, str]] = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "system":
                system = content
            elif role in {"user", "assistant"}:
                anthropic_messages.append({"role": role, "content": content})
        return system, anthropic_messages

    def _payload(
        self,
        messages: list[dict[str, str]],
        model: str,
        temperature: float,
        max_tokens: int | None,
        stream: bool,
    ) -> dict:
        system, anthropic_messages = self._split_messages(messages)
        return {
            "model": model,
            "max_tokens": max_tokens or DEFAULT_MAX_TOKENS,
            "temperature": temperature,
            "system": system,
            "messages": anthropic_messages,
            "stream": stream,
        }

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
                    "https://api.anthropic.com/v1/messages",
                    headers=self._headers(),
                    json=self._payload(messages, model, temperature, max_tokens, stream=False),
                )
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPError as exc:
            raise ProviderError(f"Anthropic request failed: {exc}") from exc

        try:
            blocks = data["content"]
            text = "".join(block.get("text", "") for block in blocks if block.get("type") == "text")
            return text.strip()
        except (KeyError, TypeError, AttributeError) as exc:
            raise ProviderError("Anthropic response format was invalid") from exc

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
                    "https://api.anthropic.com/v1/messages",
                    headers=self._headers(),
                    json=self._payload(messages, model, temperature, max_tokens, stream=True),
                ) as response:
                    response.raise_for_status()
                    current_event = ""
                    async for line in response.aiter_lines():
                        line = line.strip()
                        if line.startswith("event:"):
                            current_event = line[len("event:"):].strip()
                        elif line.startswith("data:") and current_event == "content_block_delta":
                            try:
                                event = json.loads(line[len("data:"):].strip())
                            except ValueError:
                                continue
                            text = event.get("delta", {}).get("text") if isinstance(event.get("delta"), dict) else None
                            if text:
                                yield str(text)
        except httpx.HTTPError as exc:
            raise ProviderError(f"Anthropic stream failed: {exc}") from exc
