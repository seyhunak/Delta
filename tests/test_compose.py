from __future__ import annotations

import pytest
import typer

from dp.cli import (
    add_web_context_to_messages,
    compose_messages,
    compose_user_prompt,
    ensure_prompt_inputs,
)


def test_compose_user_prompt_wire_format() -> None:
    assert compose_user_prompt("concise.", ["shorter", "formal"], "Explain X.") == (
        "Baseline: concise.\nΔ(shorter)\nΔ(formal)\nGoal:\nExplain X."
    )


def test_compose_user_prompt_no_deltas() -> None:
    assert compose_user_prompt("concise.", [], "Explain X.") == (
        "Baseline: concise.\nGoal:\nExplain X."
    )


def test_compose_messages_system_literal_and_preferences() -> None:
    messages = compose_messages("b", ["d"], "g", preferences=["be brief"])
    assert messages[0] == {
        "role": "system",
        "content": "You are a capable AI.\n\nUser preferences:\n- be brief",
    }
    assert "Δ(d)" in messages[1]["content"]
    assert "Δ(" not in messages[0]["content"]


def test_add_web_context_first_user_message_only() -> None:
    messages = [
        {"role": "system", "content": "sys"},
        {"role": "user", "content": "prompt"},
    ]
    updated = add_web_context_to_messages(messages, "Web Context (Tavily):\n[1] x")
    assert updated[0]["content"] == "sys"
    assert updated[1]["content"] == "prompt\n\nWeb Context (Tavily):\n[1] x"
    assert messages[1]["content"] == "prompt"


def test_add_web_context_empty_is_noop() -> None:
    messages = [{"role": "user", "content": "prompt"}]
    assert add_web_context_to_messages(messages, "") == messages


def test_ensure_prompt_inputs_rejects_empty() -> None:
    with pytest.raises(typer.BadParameter):
        ensure_prompt_inputs("", "goal")
    with pytest.raises(typer.BadParameter):
        ensure_prompt_inputs("baseline", "   ")
    ensure_prompt_inputs("baseline", "goal")
