from __future__ import annotations

import json
import os
from collections.abc import AsyncIterator

import httpx

from dp.providers.base import DEFAULT_TEMPERATURE, LLMProvider, ProviderError

DEFAULT_BASE_URL = "http://localhost:11434"


def resolve_base_url(base_url: str | None = None) -> str:
    return (base_url or os.getenv("OLLAMA_HOST", DEFAULT_BASE_URL)).rstrip("/")


class OllamaProvider(LLMProvider):
    name = "ollama"

    def __init__(self, base_url: str | None = None, timeout_s: float = 120.0) -> None:
        self.base_url = resolve_base_url(base_url)
        self.timeout_s = timeout_s
        self.resolved_model: str | None = None

    @staticmethod
    def _build_prompt(messages: list[dict[str, str]]) -> str:
        prompt_parts: list[str] = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            prompt_parts.append(f"{role.upper()}: {content}")
        return "\n\n".join(prompt_parts)

    def _payload(
        self,
        model: str,
        prompt: str,
        temperature: float,
        max_tokens: int | None,
        stream: bool,
    ) -> dict:
        options: dict = {"temperature": temperature}
        if max_tokens is not None:
            options["num_predict"] = max_tokens
        return {"model": model, "prompt": prompt, "stream": stream, "options": options}

    async def _list_models(self, client: httpx.AsyncClient) -> list[str]:
        response = await client.get(f"{self.base_url}/api/tags")
        response.raise_for_status()
        data = response.json()
        models = data.get("models", [])
        names = [m.get("name", "") for m in models if isinstance(m, dict)]
        return [name for name in names if isinstance(name, str) and name.strip()]

    async def _resolve_model(self, client: httpx.AsyncClient, model: str) -> str:
        self.resolved_model = model
        try:
            available = await self._list_models(client)
        except httpx.HTTPError:
            return model
        if model in available:
            return model
        short = model.split(":", 1)[0]
        for name in available:
            if name == model or name.split(":", 1)[0] == short:
                self.resolved_model = name
                return name
        if available:
            self.resolved_model = available[0]
            return available[0]
        raise ProviderError(
            "Ollama is running but no local models are installed. "
            "Run: ollama pull llama3.1:8b (or any model), then retry."
        )

    async def generate(
        self,
        messages: list[dict[str, str]],
        model: str,
        *,
        temperature: float = DEFAULT_TEMPERATURE,
        max_tokens: int | None = None,
    ) -> str:
        prompt = self._build_prompt(messages)
        try:
            async with httpx.AsyncClient(timeout=self.timeout_s) as client:
                active_model = await self._resolve_model(client, model)
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json=self._payload(active_model, prompt, temperature, max_tokens, stream=False),
                )
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPError as exc:
            if isinstance(exc, ProviderError):
                raise
            raise ProviderError(f"Ollama request failed: {exc}") from exc

        text = data.get("response")
        if not isinstance(text, str):
            raise ProviderError("Ollama response format was invalid")
        return text.strip()

    async def generate_stream(
        self,
        messages: list[dict[str, str]],
        model: str,
        *,
        temperature: float = DEFAULT_TEMPERATURE,
        max_tokens: int | None = None,
    ) -> AsyncIterator[str]:
        prompt = self._build_prompt(messages)
        try:
            async with httpx.AsyncClient(timeout=self.timeout_s) as client:
                active_model = await self._resolve_model(client, model)
                async with client.stream(
                    "POST",
                    f"{self.base_url}/api/generate",
                    json=self._payload(active_model, prompt, temperature, max_tokens, stream=True),
                ) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            event = json.loads(line)
                        except ValueError:
                            continue
                        chunk = event.get("response", "")
                        if chunk:
                            yield str(chunk)
                        if event.get("done"):
                            break
        except httpx.HTTPError as exc:
            if isinstance(exc, ProviderError):
                raise
            raise ProviderError(f"Ollama stream failed: {exc}") from exc


async def is_ollama_available(base_url: str | None = None) -> bool:
    url = resolve_base_url(base_url)
    try:
        async with httpx.AsyncClient(timeout=1.0) as client:
            response = await client.get(f"{url}/api/tags")
            return response.status_code == 200
    except httpx.HTTPError:
        return False
