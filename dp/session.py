from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


MAX_HISTORY_ENTRIES = 50


@dataclass
class SessionState:
    baseline: str = ""
    deltas: list[str] = field(default_factory=list)
    goal: str = ""
    history: list[dict[str, Any]] = field(default_factory=list)


class SessionStore:
    def __init__(self, path: Path) -> None:
        self.path = path

    def load(self) -> SessionState:
        if not self.path.exists():
            state = SessionState()
            self.save(state)
            return state

        raw = json.loads(self.path.read_text(encoding="utf-8"))
        return SessionState(
            baseline=raw.get("baseline", ""),
            deltas=list(raw.get("deltas", [])),
            goal=raw.get("goal", ""),
            history=list(raw.get("history", [])),
        )

    def save(self, state: SessionState) -> None:
        state.history = state.history[-MAX_HISTORY_ENTRIES:]
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(asdict(state), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def reset(self) -> SessionState:
        state = SessionState()
        self.save(state)
        return state


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
