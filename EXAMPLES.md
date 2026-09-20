# Delta — Sample Prompts

This file contains **canonical examples** of Delta across common task categories.
Each prompt encodes **only deviations from baseline behavior**, leveraging the model's existing capabilities to minimize instruction bloat.

---

## 📑 Table of Contents

- [🎨 Creative Task](#-creative-task)
- [🧮 Reasoning Task](#-reasoning-task)
- [💻 Coding Task](#-coding-task)
- [📊 Data Analysis](#-data-analysis)
- [📝 Content Summarization](#-content-summarization)
- [🤖 AI Agent Task](#-ai-agent-task)
- [🤝 Multi Step - Coordination Agent](#-multi-step---coordination-agent)
- [🔁 Chaining Deltas](#-chaining-deltas)
- [⚓ Anchoring the Baseline](#-anchoring-the-baseline)

---

## 🎨 Creative Task

**Goal:** Generate a short story with specific stylistic constraints.

```text
Baseline: coherent, engaging, modern prose, neutral tone.

Δ(write short story | ~300 words, bleak tone, minimalist style, ambiguous ending)

Theme:
A future where memories can be deleted, but one memory refuses to disappear.
```

---

## 🧮 Reasoning Task

**Goal:** Solve a mathematical problem with explicit reasoning.

```text
Baseline: concise, correct, no explicit reasoning unless required.

Δ(solve | multi-step math, show reasoning, final answer boxed)

Problem:
A train travels 60 km at 30 km/h and then 60 km at 60 km/h.
What is the average speed for the entire trip?
```

---

## 💻 Coding Task

**Goal:** Implement a specific function with performance and style constraints.

```text
Baseline: idiomatic, readable Python, correct by default.

Δ(implement function | O(n) time, no external libraries, no comments, include simple tests)

Task:
Write a function `first_unique_char(s: str) -> int` that returns the index of the
first non-repeating character in a string, or -1 if none exists.
```

---

## 📊 Data Analysis

**Goal:** Analyze a dataset and provide verified insights.

```text
Baseline: rigorous, verified, cited, no marketing language.

Δ(analyze csv | use pandas, identify outliers, plot distribution, summarize key trends)

Task:
Analyze the provided `sales_data.csv` to find seasonal trends and any anomalies in regional performance.
```

---

## 📝 Content Summarization

**Goal:** Summarize complex information with a specific focus.

```text
Baseline: concise, neutral, factual.

Δ(summarize | bullet points, focus on economic impact, <150 words)

Input:
[Full text of a report on renewable energy adoption in developing nations]
```

---

## 🤖 AI Agent Task

**Goal:** Instruct an autonomous agent for a research mission.

```text
Baseline: autonomous, goal-oriented, safe, minimal verbosity, explain decisions briefly.

Δ(act as task agent | plan-first, ask before irreversible actions, output checklist + next action)

Goal:
Research and prepare a short comparison of the top 3 task-management tools
for small engineering teams, focusing on pricing, integrations, and learning curve.
```

---

## 🤝 Multi Step - Coordination Agent

**Scenario:**
A product team evaluates a new "Metrics" feature for an Ads Platform. Three agents collaborate using Delta to maintain focus and efficiency.

### Shared Baseline (Declared Once)

```text
Baseline: cooperative, concise, factual, respect other agents’ outputs,
do not repeat information already provided unless correcting it.
```

### Agent 1 — Research Agent
```text
Δ(act as research agent | gather evidence, cite sources, no recommendations)
Task: Summarize industry practices and user demand for ad metrics.
```

### Agent 2 — Engineering Agent
```text
Δ(act as engineering agent | feasibility-focused, surface risks, estimate effort)
Task: Evaluate technical feasibility based on the research findings.
```

### Agent 3 — Product Agent
```text
Δ(act as product agent | synthesize inputs, decision-oriented, no new research)
Task: Recommend whether to proceed, noting tradeoffs and uncertainties.
```

---

## 🔁 Chaining Deltas

Deltas are **incrementally composable**. You can refine behavior over multiple turns without restating the entire baseline or previous deltas.

**Example Conversation Flow:**

1.  **User:** `Δ(write report | technical, markdown)`
2.  **Model:** [Generates technical report]
3.  **User:** `Δ(make it shorter | use bullet points for the summary)`
4.  **Model:** [Refines the report]
5.  **User:** `Δ(add a "Risks" section | focus on security)`
6.  **Model:** [Adds the requested section]

---

## ⚓ Anchoring the Baseline

When starting a new session or switching contexts, use a **one-time anchor** to set the expected behavior. Once anchored, use simple Deltas for specific tasks.

**Example:**

**User (Anchor):**
```text
Baseline: Technical, Pythonic, no comments, minimal verbosity.
```

**User (Delta 1):**
```text
Δ(implement quicksort)
```

**User (Delta 2):**
```text
Δ(add type hints | O(n log n) verification)
```

---

## 💡 Best Practices

*   **Be Specific:** Only include what deviates from the baseline.
*   **Use Pipes:** Use the `|` symbol to separate constraints for readability.
*   **Re-Anchor:** If the model's behavior drifts in long conversations, re-anchor the baseline briefly.
*   **Leverage Priors:** Assume the model knows "best practices" (e.g., O(n) for searching a hash map) unless you need to override them.

---

*For more details on defining baselines, see [BASELINE.md](BASELINE.md).*
