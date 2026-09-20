from __future__ import annotations

import os
from dataclasses import dataclass

from dp.config import Settings
from dp.providers.anthropic import AnthropicProvider
from dp.providers.base import LLMProvider, ProviderError
from dp.providers.ollama import OllamaProvider, is_ollama_available
from dp.providers.openai import OpenAIProvider

SUPPORTED_PROVIDERS = ("openai", "anthropic", "ollama")
KNOWN_PROVIDERS = ("openai", "anthropic", "ollama", "groq")


@dataclass(frozen=True)
class ProviderStatus:
    available: bool
    reason: str = ""


async def detect_providers() -> dict[str, ProviderStatus]:
    statuses: dict[str, ProviderStatus] = {}

    statuses["openai"] = ProviderStatus(
        available=bool(os.getenv("OPENAI_API_KEY")),
        reason="OPENAI_API_KEY" if os.getenv("OPENAI_API_KEY") else "missing OPENAI_API_KEY",
    )
    statuses["anthropic"] = ProviderStatus(
        available=bool(os.getenv("ANTHROPIC_API_KEY")),
        reason="ANTHROPIC_API_KEY" if os.getenv("ANTHROPIC_API_KEY") else "missing ANTHROPIC_API_KEY",
    )
    ollama_host = os.getenv("OLLAMA_HOST", "localhost:11434")
    ollama_up = await is_ollama_available()
    statuses["ollama"] = ProviderStatus(
        available=ollama_up,
        reason=f"{ollama_host} reachable" if ollama_up else f"{ollama_host} unreachable",
    )
    statuses["groq"] = ProviderStatus(
        available=bool(os.getenv("GROQ_API_KEY")),
        reason="not implemented",
    )

    return statuses


def default_model_for(provider: str, settings: Settings) -> str:
    provider = provider.lower()
    if provider == "openai":
        return settings.models.openai
    if provider == "anthropic":
        return settings.models.anthropic
    if provider == "ollama":
        return settings.models.ollama
    raise ProviderError(f"No default model configured for provider: {provider}")


async def select_provider(explicit: str | None, settings: Settings, preferred: str | None = None) -> str:
    statuses = await detect_providers()

    if explicit:
        provider = explicit.lower()
        if provider not in KNOWN_PROVIDERS:
            raise ProviderError(f"Unknown provider: {provider}")
        if provider not in SUPPORTED_PROVIDERS:
            raise ProviderError(f"Provider is known but not implemented: {provider}")
        if not statuses.get(provider, ProviderStatus(False)).available:
            reason = statuses.get(provider, ProviderStatus(False, "unavailable")).reason
            raise ProviderError(f"Provider '{provider}' is unavailable ({reason})")
        return provider

    configured_provider = preferred or settings.default_provider
    if configured_provider:
        configured = configured_provider.lower()
        if configured in SUPPORTED_PROVIDERS and statuses.get(configured, ProviderStatus(False)).available:
            return configured

    for provider in ("openai", "anthropic", "ollama"):
        if statuses.get(provider, ProviderStatus(False)).available:
            return provider

    return "ollama"


def provider_factory(provider: str) -> LLMProvider:
    provider = provider.lower()
    if provider == "openai":
        return OpenAIProvider()
    if provider == "anthropic":
        return AnthropicProvider()
    if provider == "ollama":
        return OllamaProvider()
    raise ProviderError(f"Unknown provider: {provider}")
