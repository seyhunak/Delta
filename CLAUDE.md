# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

Two coupled deliverables:

1. **The Delta methodology** — a prompting technique documented in the root-level markdown files. `README.md` is the entry point and its *Navigation* section links every other doc: `BASELINE.md` (baseline vocabulary), `EXAMPLES.md`, `COMPARE.md`, `DELTA_VS_NAIVE.md`, `BENCHMARK.md`, `CLI.md`, `SKILL.md`, `FAILURES.md` (failure case studies).
2. **The `dp` CLI** (`dp/` package, distribution `deltaprompt-cli`, version `0.1.0` in both `pyproject.toml` and `dp/__init__.py`) — the reference implementation. A persisted session holds `baseline` + an ordered list of `deltas` + `goal`; `dp run` composes those into a single prompt and executes it against a provider.

The docs are a first-class artifact here, not an afterthought — the repo exists to publish the technique. Treat doc/code drift as a bug (see *Doc–code coupling* below).

### The methodology, compressed

`Δ = O − B`, where **B** is the model's baseline behavior and **O** the desired output. Write only the deviation. Canonical syntax: `Δ(goal | constraints | style | output)`, all fields optional; unspecified dimensions inherit the baseline. Deltas are *incrementally composable* — each added delta modifies behavior without resetting context, which is exactly why `SessionState.deltas` is an ordered list you append to rather than a dict you overwrite. `BASELINE.md` defines the standard baseline dimensions (verbosity, tone, reasoning, correctness, formatting, autonomy) and five canonical baseline combinations; use its vocabulary when writing examples so docs stay internally consistent.

## Commands

```bash
python3 -m pip install -e .        # install; exposes the `dp` console script
dp --install-completion            # shell completion (typer built-in)

dp doctor                          # which providers are reachable + which would be selected
dp setup                           # interactive wizard -> ~/.deltaprompt/config.json

dp set "<baseline>" "<goal>" -d "<delta>" -d "<delta>" [-a|--append-deltas]
dp baseline set "<text>"           # granular equivalents
dp delta add "<text>"
dp goal set "<text>"
dp show                            # session + config summary
dp reset                           # wipe session (baseline, deltas, goal, history)

dp run [--provider openai|anthropic|ollama] [--model M]
       [--temperature T] [--max-tokens N] [--stream/--no-stream]
       [--web-search/--no-web-search] [--search-query Q] [--search-results N]
dp benchmark [--providers openai --providers anthropic | openai anthropic ollama]
             [--model M] [--temperature T] [--max-tokens N] [--web-search] ...
```

`dp set` **replaces** deltas by default; `-a` appends. `dp benchmark` accepts providers as either repeated `--providers` flags or bare positional args (both lists are concatenated).

### Verification

Tests live in `tests/` (pytest, `pip install -e ".[test]"`). Conventions: one
file per module area (`test_compose.py`, `test_benchmark.py`, `test_session.py`,
`test_providers.py`); network-free — providers are tested via pure helpers
(`_build_prompt`, `resolve_base_url`) and a fake `LLMProvider`, never live APIs.
Run `pytest -q` before committing. No linter, formatter, or type checker yet.

```bash
DP_SESSION_PATH=/tmp/dp-session.json DP_CONFIG_PATH=/tmp/dp-config.json dp show
```

Always point `DP_SESSION_PATH`/`DP_CONFIG_PATH` at throwaway files when testing — otherwise you clobber the user's real `~/.deltaprompt/` state, and both stores silently create-and-overwrite. Ollama is the only provider needing no API key (local daemon on `localhost:11434`); if none is available, `select_provider` still returns `"ollama"` and the run fails at request time with a `ProviderError`.

If you add tests, follow the existing convention (one file per module area under `tests/`, network-free).

## Architecture

### Prompt composition — the heart of the project

Lives in `dp/cli.py:47-80`. Everything else is plumbing around it.

- `compose_user_prompt(baseline, deltas, goal)` renders the canonical wire format:
  ```text
  Baseline: <baseline>
  Δ(<delta1>)
  Δ(<delta2>)
  Goal:
  <goal>
  ```
  This exact string *is* the methodology. Changing its shape changes what the project means — don't "clean it up" without a deliberate decision, and mirror any change into `README.md`, `CLI.md`, and `SKILL.md`.
- `compose_messages()` produces a two-message chat: a system message that is the fixed literal `"You are a capable AI."` (plus a `User preferences:` bullet block when `config.preferences` is non-empty), and one user message containing the composed prompt. **Deltas deliberately never go in the system message** — the technique is about in-band correction, not system-prompt engineering.
- `add_web_context_to_messages()` appends the Tavily block to the *first* user message only, non-destructively (it deep-copies the message dicts).

### Layers

| Path | Responsibility |
| --- | --- |
| `dp/cli.py` | All Typer commands, prompt composition, Rich rendering. ~625 lines; the only module with UI. |
| `dp/providers/__init__.py` | Provider *policy*: detection, selection, defaults, factory. |
| `dp/providers/{openai,anthropic,ollama}.py` | One `LLMProvider` implementation each, raw `httpx` against the vendor HTTP API. |
| `dp/providers/base.py` | `LLMProvider` ABC (single async `generate(messages, model) -> str`) and `ProviderError`. |
| `dp/config.py` | `Settings` (env, frozen) + `UserConfig`/`ConfigStore` (JSON file). |
| `dp/session.py` | `SessionState` + `SessionStore` (JSON file, history capped at 50), `now_iso()`. |
| `dp/benchmark.py` | `BenchmarkResult`, token estimation, `LexicalOverlapScorer`, `delta_compression_ratio`, `run_single_benchmark`. |
| `dp/tools/tavily.py` | Optional web-context enrichment. |

### Async pattern

Every async command is a thin sync Typer wrapper around a private coroutine driven by `asyncio.run`: `run`→`_run`, `benchmark`→`_benchmark`, `doctor`→`_doctor`. `setup` resolves detection + suggestion in a single `asyncio.run` via `_detect_and_suggest()`. Follow this shape for new commands — Typer sees only sync functions.

### Providers

`dp/providers/__init__.py` owns all policy; the concrete modules only know how to speak one HTTP API.

- **`SUPPORTED_PROVIDERS = ("openai", "anthropic", "ollama")` vs `KNOWN_PROVIDERS = (..., "groq")`** is deliberate, not leftover. `groq` is *known* so `dp doctor` lists it and `--provider groq` produces a precise "known but not implemented" error instead of "unknown provider". Keep that distinction when adding providers.
- **`detect_providers()`** is cheap and side-effect-free: env-var presence for hosted providers, a 1-second `GET /api/tags` probe for Ollama. It does not validate keys — a present-but-invalid key reads as "available" and fails later at request time.
- **`select_provider()` precedence:** explicit `--provider` → `UserConfig.default_provider` → `Settings.default_provider` (`DP_DEFAULT_PROVIDER`) → first available of openai/anthropic/ollama → hard fallback `"ollama"`. Explicit selection of an unavailable provider raises; implicit selection never raises.
- **Constructors can raise.** `OpenAIProvider()`/`AnthropicProvider()` raise `ProviderError` from `__init__` when the key is missing, so `provider_factory()` itself is a throwing call site.
- **Adding a provider touches five places:** a new module implementing `LLMProvider`; a branch in `provider_factory()`; an entry in `detect_providers()`; a branch in `default_model_for()`; a field on `DefaultModels` (and its `DP_MODEL_*` env override in `get_settings()`). Then add it to `SUPPORTED_PROVIDERS` and document it in `CLI.md` + `SKILL.md`.

Provider-specific quirks worth knowing:

- **Anthropic** flattens the system message out of `messages` into the top-level `system` field, defaults `max_tokens: 2048` (overridable via `--max-tokens`) and `temperature: 0.2` (overridable via `--temperature`), pins `anthropic-version: 2023-06-01`, and concatenates all `type == "text"` content blocks. Streaming parses `content_block_delta` SSE events.
- **OpenAI** posts `messages` through unchanged to `/v1/chat/completions` with `temperature: 0.2` default; `max_tokens` is sent only when set. Streaming parses `choices[0].delta.content` SSE chunks until `[DONE]`.
- **Ollama** does *not* use the chat endpoint. `_build_prompt()` flattens messages into `"ROLE: content"` blocks joined by blank lines and posts to `/api/generate` with `stream: False`. Before generating it resolves the model against `/api/tags` (exact match, then base-name match, then first installed model) and records the outcome in `resolved_model` — the CLI warns and reports the actually-used model when it differs. If no models are installed it raises a `ProviderError` telling the user to `ollama pull`. Base URL comes from `OLLAMA_HOST` (default `http://localhost:11434`). Timeout is 120s (vs 60s for hosted providers).

### Config vs session — two different concepts

- **`Settings`** (`dp/config.py`) is frozen, env-derived, and re-read on every `get_settings()` call — there's no caching, so env changes take effect immediately. Env vars: `DP_SESSION_PATH`, `DP_CONFIG_PATH`, `DP_DEFAULT_PROVIDER`, `DP_MODEL_OPENAI`, `DP_MODEL_ANTHROPIC`, `DP_MODEL_OLLAMA`, `TAVILY_API_KEY` (plus `OPENAI_API_KEY`/`ANTHROPIC_API_KEY` read directly by the provider modules and `detect_providers`).
- **`UserConfig`** is the mutable JSON at `~/.deltaprompt/config.json`, written by `dp setup`: `default_provider`, per-provider `models`, `preferences` (injected into the system message), `web_search_enabled`, `web_search_max_results`.
- **`SessionState`** is the JSON at `~/.deltaprompt/session.json`: `baseline`, `deltas`, `goal`, and an ever-growing `history`.

Both stores auto-create their file with defaults on the first `load()` and write with `indent=2, ensure_ascii=False`. **`history` is capped at the 50 most recent entries** on every `save()` (`MAX_HISTORY_ENTRIES` in `dp/session.py`).

### Model resolution

Per run: `--model` flag → `UserConfig.models[provider]` → `default_model_for(provider, settings)` (i.e. `DP_MODEL_*` env or the `DefaultModels` literals: `gpt-4o-mini`, `claude-3-5-haiku-latest`, `llama3.1:8b`).

### Benchmark

`run_single_benchmark` runs providers **sequentially, not concurrently** (a `for` loop with `await`), so latency numbers are not contended but wall-clock is the sum. Unavailable or unsupported providers are skipped with a warning; a provider that errors mid-run is reported and dropped. Zero results → exit code 1.

`LexicalOverlapScorer` is a bag-of-words set-intersection ratio scored against `results[0]` — **the first *successful* provider, which depends on ordering**, so the reference is whatever survived first, and it always scores 1.000 against itself. The comparison table marks the reference `— (ref)` instead of printing that trivial score. `estimate_tokens()` is `max(1, len(text) // 4)` — a crude heuristic, not a tokenizer, which is why every count in the UI is labeled `(est.)`. Don't present these numbers as measurements.

### Web context (Tavily)

Active only when a Tavily key is present **and** web search is on (`config.web_search_enabled`, overridable per-run by `--web-search/--no-web-search`). The query defaults to the goal text, overridable with `--search-query`; results are clamped to 1–10 in three separate places. `build_web_context_block()` renders a numbered `Web Context (Tavily):` block of title/URL/snippet. Failures are **non-fatal** — the run prints a yellow warning and continues without context. A missing key when search is requested is likewise a warning, not an error. `TavilyClient` sends the key as a Bearer header.

### Error handling convention

Everything that can fail across the network raises `ProviderError` (from `dp/providers/base.py`) — including Tavily, which imports it rather than defining its own. Commands catch `ProviderError` and `typer.BadParameter`, print in red, and `raise typer.Exit(code=1)`. A failed `dp run` still appends a `{timestamp, provider, model, error}` entry to session history and saves **before** re-raising, so history is a complete record of attempts, not just successes. `ensure_prompt_inputs()` gates `run`/`benchmark` on non-empty baseline and goal, raising `typer.BadParameter` with the exact fixing command.

### Rendering

All terminal output goes through a module-level `rich.Console` in `dp/cli.py`. Long operations are wrapped in `console.status(...)` spinners. `render_pretty_response()` prints a "Run Summary" key/value panel (provider, model, latency, est. token counts, web sources, chars) followed by a Markdown-rendered output panel. `_normalize_markdown()` prefixes a `## Response` heading when the output doesn't already start with `#`, and substitutes a placeholder for empty output.

## Doc–code coupling

- **`SKILL.md` and `.claude/skills/SKILL.md` are byte-identical duplicates.** The root copy is what users `curl` from GitHub (the install snippet inside it points at `raw.githubusercontent.com/seyhunak/Delta/main/SKILL.md`); the `.claude/` copy is what Claude Code loads locally. **Edit both or they drift.**
- Changing CLI flags or behavior means updating `CLI.md` (full command reference, provider-selection order, troubleshooting) and the command list in `SKILL.md`.
- Adding a root-level doc means adding it to the *Navigation* list in `README.md`; `README.md` also carries an inline CLI capabilities summary and a "Last Updated" date at the bottom.

## Repo conventions

- Python ≥3.10; every module starts with `from __future__ import annotations` and uses PEP 604 (`str | None`) types throughout. CLI options use `Annotated[T, typer.Option(...)]`.
- Dataclasses everywhere for state; frozen for anything immutable (`Settings`, `DefaultModels`, `ProviderStatus`, `BenchmarkResult` is mutable).
- No vendor SDKs — `httpx.AsyncClient` per request, constructed inside the call and closed by `async with`.
- Comments are essentially absent; the code is written to read without them. Match that.
- Don't `git add -A` blindly — check `git status` first (`.venv/`, `__pycache__/`, and `*.egg-info/` are gitignored but scratch files may not be).
- Test conventions: one file per module area under `tests/` (`test_compose.py`, `test_benchmark.py`, `test_session.py`, `test_providers.py`); network-free; run `pytest -q` before committing.
