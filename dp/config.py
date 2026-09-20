from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class DefaultModels:
    openai: str = "gpt-4o-mini"
    anthropic: str = "claude-3-5-haiku-latest"
    ollama: str = "llama3.1:8b"


@dataclass(frozen=True)
class Settings:
    session_path: Path
    config_path: Path
    default_provider: str | None
    models: DefaultModels
    tavily_api_key: str | None


def get_settings() -> Settings:
    session_path = Path(
        os.getenv("DP_SESSION_PATH", str(Path.home() / ".deltaprompt" / "session.json"))
    ).expanduser()
    config_path = Path(
        os.getenv("DP_CONFIG_PATH", str(Path.home() / ".deltaprompt" / "config.json"))
    ).expanduser()

    models = DefaultModels(
        openai=os.getenv("DP_MODEL_OPENAI", DefaultModels.openai),
        anthropic=os.getenv("DP_MODEL_ANTHROPIC", DefaultModels.anthropic),
        ollama=os.getenv("DP_MODEL_OLLAMA", DefaultModels.ollama),
    )

    return Settings(
        session_path=session_path,
        config_path=config_path,
        default_provider=os.getenv("DP_DEFAULT_PROVIDER"),
        models=models,
        tavily_api_key=os.getenv("TAVILY_API_KEY"),
    )


@dataclass
class UserConfig:
    default_provider: str | None = None
    models: dict[str, str] = field(default_factory=dict)
    preferences: list[str] = field(default_factory=list)
    web_search_enabled: bool = False
    web_search_max_results: int = 5


class ConfigStore:
    def __init__(self, path: Path) -> None:
        self.path = path

    def load(self) -> UserConfig:
        if not self.path.exists():
            config = UserConfig()
            self.save(config)
            return config

        raw = json.loads(self.path.read_text(encoding="utf-8"))
        return UserConfig(
            default_provider=raw.get("default_provider"),
            models=dict(raw.get("models", {})),
            preferences=list(raw.get("preferences", [])),
            web_search_enabled=bool(raw.get("web_search_enabled", False)),
            web_search_max_results=int(raw.get("web_search_max_results", 5)),
        )

    def save(self, config: UserConfig) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(asdict(config), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
