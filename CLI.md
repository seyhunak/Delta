# Delta CLI (`dp`)

This document covers the CLI workflow, commands, and examples for the Delta tool.

Back to main docs: [README.md](README.md)

---

## Install

```bash
python3 -m pip install -e .
```

Command entrypoint:

```bash
dp
```

Install shell completion (zsh):

```bash
dp --install-completion
exec zsh
```

---

## What `dp` Does

`dp` manages a prompt session with:

* `baseline`
* incremental `deltas`
* `goal`
* `history`

It composes and runs:

```text
Baseline: <baseline>
Δ(<delta1>)
Δ(<delta2>)
Goal:
<goal>
```

System message:

```text
You are a capable AI.
```

If you set preferences via `dp setup`, they are appended to the system message.

---

## Persistence

Session state:

* `~/.deltaprompt/session.json`

Config state:

* `~/.deltaprompt/config.json`

You can override paths with:

* `DP_SESSION_PATH`
* `DP_CONFIG_PATH`

---

## Provider Selection

Priority order:

1. `--provider` flag
2. Saved config default provider (`dp setup`)
3. `DP_DEFAULT_PROVIDER`
4. First detected available provider
5. Ollama fallback

Supported providers:

* `openai` (requires `OPENAI_API_KEY`)
* `anthropic` (requires `ANTHROPIC_API_KEY`)
* `ollama` (requires local Ollama at `localhost:11434` or `OLLAMA_HOST`)
* Session history is capped at the 50 most recent entries.

Web search provider:

* `tavily` (requires `TAVILY_API_KEY`)

---

## Commands

### `dp setup`

Interactive setup for:

* default provider
* default model
* preferences (comma-separated)
* Tavily web-search toggle and max results

```bash
dp setup
```

### `dp set`

Set baseline + goal + delta(s) in one command.

```bash
dp set "<baseline>" "<goal>" -d "<delta>"
```

Multiple deltas:

```bash
dp set "<baseline>" "<goal>" -d "<d1>" -d "<d2>"
```

Append deltas instead of replacing:

```bash
dp set "<baseline>" "<goal>" -d "<delta>" -a
```

### Legacy subcommands

```bash
dp baseline set "<text>"
dp delta add "<text>"
dp goal set "<text>"
```

### `dp run`

Execute the current session with selected provider/model.

```bash
dp run
dp run --provider ollama --model llama3.2:3b
dp run --stream
dp run --temperature 0.7 --max-tokens 1024
dp run --web-search --search-query "latest python retry best practices" --search-results 5
```

Sampling defaults are `temperature 0.2` and the provider default for max tokens
(Anthropic: 2048). If Ollama falls back to a different installed model, the run
warns and reports the model actually used.

Output features:

* live progress spinner (provider + model)
* markdown-rendered AI response
* optional Tavily web context injection into the prompt
* structured run stats:
  * provider
  * model
  * latency
  * prompt token estimate
  * output token estimate
  * total token estimate
  * web source count

### `dp benchmark`

Compare providers on the same prompt.

```bash
dp benchmark --providers ollama
dp benchmark --providers openai --providers anthropic --providers ollama
dp benchmark --providers ollama --web-search --search-query "python http retry strategy"
```

Benchmark output includes:

* per-provider latency
* prompt/output/total token estimates
* output comparison score table (the reference provider is marked `— (ref)`, not scored)
* rendered output for each provider

`dp benchmark` also accepts `--temperature` and `--max-tokens`, applied to every provider.

### `dp doctor`

Show provider availability and selected default provider.

```bash
dp doctor
```

### `dp show`

Show current session + config summary.

```bash
dp show
```

### `dp reset`

Reset session state.

```bash
dp reset
```

---

## Example: Article Generation Test

```bash
dp reset

dp set \
"Write with clear structure, practical examples, and concise paragraphs." \
"Generate a 700-word article: 'Async Retry Strategies for API Clients in Python'" \
-d "Use H2/H3 markdown headings." \
-d "Include one comparison table." \
-d "Include a short code snippet with exponential backoff + jitter." \
-d "End with a 5-bullet key takeaways section."

dp run
```

---

## Troubleshooting

### `dp run` appears stuck

`dp run` is non-streaming by default, so output appears when complete. Progress spinner indicates active execution. Use `dp run --stream` to print tokens live.

### Ollama 404 / model not found

Check local models:

```bash
ollama list
```

Run with an installed model:

```bash
dp run --provider ollama --model <installed-model>
```

If no models are installed:

```bash
ollama pull llama3.2:3b
```

### No provider detected

Run:

```bash
dp doctor
```

Then configure with:

```bash
dp setup
```
