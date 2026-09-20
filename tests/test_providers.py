from __future__ import annotations

import pytest

from dp.providers.base import DEFAULT_TEMPERATURE, LLMProvider
from dp.providers.ollama import OllamaProvider, resolve_base_url


def test_resolve_base_url_default_and_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OLLAMA_HOST", raising=False)
    assert resolve_base_url() == "http://localhost:11434"
    assert resolve_base_url("http://x:1234/") == "http://x:1234"
    monkeypatch.setenv("OLLAMA_HOST", "http://remote:11434/")
    assert resolve_base_url() == "http://remote:11434"
    assert OllamaProvider().base_url == "http://remote:11434"


def test_build_prompt_flattens_roles() -> None:
    prompt = OllamaProvider._build_prompt(
        [
            {"role": "system", "content": "sys"},
            {"role": "user", "content": "hi"},
        ]
    )
    assert prompt == "SYSTEM: sys\n\nUSER: hi"


def test_stream_fallback_yields_full_output() -> None:
    class EchoProvider(LLMProvider):
        name = "echo"

        async def generate(self, messages, model, *, temperature=DEFAULT_TEMPERATURE, max_tokens=None) -> str:
            return "full output"

    async def collect() -> list[str]:
        return [chunk async for chunk in EchoProvider().generate_stream([], "m")]

    import asyncio

    assert asyncio.run(collect()) == ["full output"]
