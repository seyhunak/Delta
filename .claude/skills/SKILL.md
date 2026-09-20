# Delta Skill for Claude Code

This skill provides specialized commands and workflows for working with the Delta project - a difference-based prompting technique for LLMs.

## Overview

Delta is a prompting methodology that encodes only the difference between a model's default behavior and the user's desired behavior. Instead of restating full instructions, it treats prompts as corrections.

**Core concept:**
- B = model's baseline behavior (implied by pretraining + context)
- O = desired output
- Delta specifies: Δ = O − B

**Canonical syntax:** `Δ(goal | constraints | style | output)`

## Claude Code Installation

To use this skill with Claude Code:

1. Place `SKILL.md` in `.claude/skills/` at your project root
2. Or use the skill command to load it: `/skill Delta`
3. Or download directly:

```bash
mkdir -p .claude/skills
curl -fsSL https://raw.githubusercontent.com/seyhunak/Delta/main/SKILL.md -o .claude/skills/SKILL.md
# or
wget -q https://raw.githubusercontent.com/seyhunak/Delta/main/SKILL.md -O .claude/skills/SKILL.md
```

Once loaded, Claude Code will have access to all the commands and workflows documented in this file.

## Delta CLI Installation

```bash
python3 -m pip install -e .
```

## CLI Commands

The `dp` command provides the following subcommands:

### Session Management

- `dp setup` - Interactive configuration for providers, models, and preferences
- `dp show` - Display current session state (baseline, goal, deltas)
- `dp reset` - Clear current session

### Setting Prompt Components

- `dp baseline set "..."` - Set baseline behavior
- `dp delta add "..."` - Add a delta constraint
- `dp goal set "..."` - Set the goal/task
- `dp set "baseline" "goal" -d "delta1" -d "delta2"` - Set all at once

### Execution

- `dp run` - Execute prompt with current session
- `dp run --provider openai` - Run with specific provider
- `dp run --model gpt-4` - Override model
- `dp run --stream` - Stream output tokens live
- `dp run --temperature 0.7 --max-tokens 1024` - Override sampling params
- `dp run --web-search` - Enable Tavily web search context
- `dp run --search-query "custom query"` - Override search query

### Benchmarking

- `dp benchmark` - Compare outputs across all available providers
- `dp benchmark openai anthropic` - Benchmark specific providers
- `dp benchmark --web-search` - Include web context in benchmark

### Diagnostics

- `dp doctor` - Check provider availability and configuration

## Workflows

### Quick Prompt Execution

```bash
dp "concise, technical" "Explain async/await in Python" -d "include code example"
dp run
```

### Multi-turn Session

```bash
dp baseline set "concise, helpful, technical"
dp goal set "Design a REST API for task management"
dp delta add "include authentication"
dp run
dp delta add "add rate limiting"
dp run
```

### Provider Comparison

```bash
dp baseline set "creative writer, vivid prose"
dp goal set "Write a short story about time"
dp benchmark openai anthropic ollama
```

## Best Practices

1. **Start with baseline** - Anchor the model's default behavior once
2. **Add deltas incrementally** - Compose behavior changes step by step
3. **Use constraints sparingly** - Only specify what's different from baseline
4. **Keep deltas focused** - One constraint per delta works best
5. **Re-anchor when needed** - For long conversations, briefly restate baseline

## Example Patterns

### Explanation
```
Baseline: concise, correct, neutral.
Δ(explain quantum entanglement | high-school level, <80 words, one analogy)
```

### Reasoning
```
Baseline: no explicit reasoning unless required.
Δ(solve | multi-step math, show reasoning)
```

### Coding
```
Baseline: idiomatic Python, correct by default.
Δ(implement function | O(n), no comments, include tests)
```

### Agentic Behavior
```
Baseline: autonomous, reliable, minimal verbosity.
Δ(act as research agent | plan-first, explicit tool calls)
```

## Environment Variables

- `OPENAI_API_KEY` - For OpenAI provider
- `ANTHROPIC_API_KEY` - For Anthropic provider
- `OLLAMA_HOST` - For local Ollama (default: http://localhost:11434)
- `TAVILY_API_KEY` - For web search context

## Files

- Session: `~/.deltaprompt/session.json`
- Config: `~/.deltaprompt/config.json`
