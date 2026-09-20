from __future__ import annotations

from dp.session import MAX_HISTORY_ENTRIES, SessionState, SessionStore


def test_save_load_roundtrip(tmp_path) -> None:
    store = SessionStore(tmp_path / "session.json")
    state = SessionState(baseline="b", deltas=["d1"], goal="g", history=[{"a": 1}])
    store.save(state)
    loaded = store.load()
    assert loaded.baseline == "b"
    assert loaded.deltas == ["d1"]
    assert loaded.goal == "g"
    assert loaded.history == [{"a": 1}]


def test_load_creates_default_when_missing(tmp_path) -> None:
    store = SessionStore(tmp_path / "sub" / "session.json")
    loaded = store.load()
    assert loaded == SessionState()
    assert store.path.exists()


def test_history_capped_on_save(tmp_path) -> None:
    store = SessionStore(tmp_path / "session.json")
    state = SessionState(history=[{"i": i} for i in range(MAX_HISTORY_ENTRIES + 20)])
    store.save(state)
    assert len(store.load().history) == MAX_HISTORY_ENTRIES
    assert store.load().history[0] == {"i": 20}


def test_reset_wipes_state(tmp_path) -> None:
    store = SessionStore(tmp_path / "session.json")
    store.save(SessionState(baseline="b", goal="g"))
    assert store.reset() == SessionState()
