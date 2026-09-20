# Naive vs Delta — Side-by-Side Examples

This file demonstrates how **Delta** compresses instructions by encoding *only differences* from a model’s baseline behavior, compared to traditional naive prompting.

Each section shows the **same task** prompted in two ways.

---

## Creative Task

### Naive Prompt

```text
Write a short science fiction story of about 300 words.
The tone should be bleak and philosophical.
Use a minimalist writing style.
The ending should be ambiguous and open to interpretation.
The story should be about a future where memories can be deleted,
but one memory refuses to disappear.
```

### Delta

```text
Baseline: modern, coherent prose, neutral tone.

Δ(write short story | ~300 words, bleak, minimalist, ambiguous ending)

Theme:
A future where memories can be deleted, but one memory refuses to disappear.
```

---

## Reasoning Task

### Naive Prompt

```text
Solve the following problem step by step.
Explain your reasoning clearly before giving the final answer.

A train travels 60 km at 30 km/h and then 60 km at 60 km/h.
What is the average speed for the entire trip?
```

### Delta

```text
Baseline: concise, correct, no explicit reasoning unless required.

Δ(solve | multi-step math, show reasoning, final answer boxed)

Problem:
A train travels 60 km at 30 km/h and then 60 km at 60 km/h.
```

---

## Coding Task

### Naive Prompt

```text
Write a Python function that takes a string as input and returns the index
of the first non-repeating character in the string.
The function should run in O(n) time.
Do not use external libraries.
Include simple test cases.
Do not include unnecessary comments or explanations.
```

### Delta

```text
Baseline: idiomatic, readable Python, correct by default.

Δ(implement function | O(n), no external libraries, no comments, include tests)

Task:
Return the index of the first non-repeating character in a string.
```

---

## Multi-Step Tool-Using Agent

### Naive Prompt

```text
You are an AI research assistant.
Research the top 3 open-source vector databases.
Use web search to find information.
Read documentation if necessary.
Compare them based on maturity, scalability, and ecosystem.
Create a comparison table.
Make sure the information is accurate and cite sources.
Finally, recommend the best option.
```

### Delta

```text
Baseline: autonomous, reliable, minimal verbosity, no tool use unless helpful.

Δ(act as research agent | plan-first, explicit tool calls, verify before summarizing, ask before recommending)

Goal:
Identify the top 3 open-source vector databases suitable for production.

Constraints:
- Focus on maturity, scalability, ecosystem
- Cite sources
- No marketing language
```

---

## AI Agent Task

### Naive Prompt

```text
You are an AI agent helping with research.
Your task is to research and prepare a comparison of the top 3 task-management
tools for small engineering teams.
Focus on pricing, integrations, and learning curve.
Organize the information clearly and provide a recommendation.
```

### Delta

```text
Baseline: autonomous, goal-oriented, safe, minimal verbosity.

Δ(act as task agent | plan-first, ask before irreversible actions, output checklist + next action)

Goal:
Prepare a comparison of the top 3 task-management tools for small engineering teams,
focusing on pricing, integrations, and learning curve.
```

---

## Summary Comparison

| Aspect         | Naive Prompting | Delta |
| -------------- | --------------- | ---------- |
| Prompt length  | Long            | Short      |
| Redundancy     | High            | Minimal    |
| Iteration cost | High            | Low        |
| Baseline use   | Ignored         | Leveraged  |
| Human effort   | Higher          | Lower      |

---

## Key Insight

> **Naive prompts describe everything.
> Delta prompts describe only what changed.**

As models become more capable, **difference-based prompting scales better than instruction accumulation**.
