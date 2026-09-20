# Delta Baselines Reference Sheet

This document defines the **Baseline Behavior (B)** for Delta. A baseline is the set of assumptions the model operates under before any **Delta (Δ)** is applied.

By defining a clear baseline, you can minimize instruction length and focus only on deviations.

---

## 🛠 Baseline Dimensions

When defining or anchoring a baseline, you can mix and match these dimensions.

| Dimension | Options (from least to most) |
| :--- | :--- |
| **Verbosity** | `minimal` → `concise` → `moderate` → `detailed` |
| **Tone** | `neutral` → `technical` → `professional` → `casual` |
| **Reasoning** | `implicit` → `step-by-step` → `chain-of-thought` |
| **Correctness** | `default` → `idiomatic` → `rigorous` → `verified` |
| **Formatting** | `plaintext` → `markdown` → `structured (JSON/CSV)` |
| **Autonomy** | `reactive` → `reliable` → `proactive` → `autonomous` |

---

## 📋 Canonical Baseline Combinations

These are the recommended starting points for various domains.

### 1. The "Standard" Baseline (Default)
> **Baseline:** `concise, correct, neutral`
* **Best for:** General assistance, quick questions, and basic information retrieval.

### 2. The "Technical" Baseline
> **Baseline:** `technical, idiomatic, no comments, correct by default`
* **Best for:** Software engineering, systems design, and technical documentation.

### 3. The "Agentic" Baseline
> **Baseline:** `autonomous, reliable, minimal verbosity, plan-first`
* **Best for:** Multi-step tasks, tool usage, and complex research workflows.

### 4. The "Creative" Baseline
> **Baseline:** `modern, neutral prose, descriptive, high-quality`
* **Best for:** Content generation, storytelling, and copy editing.

### 5. The "Critical" Baseline
> **Baseline:** `rigorous, verified, cited, no marketing language`
* **Best for:** Data analysis, scientific research, and fact-checking.

---

## 🔄 Combination Matrix (Quick Reference)

Use this matrix to quickly pick a baseline based on your primary and secondary needs.

| Goal \ Attribute | **Speed / Efficiency** | **Precision / Accuracy** | **Creative / Explanatory** |
| :--- | :--- | :--- | :--- |
| **Single Task** | `minimal, reactive` | `concise, rigorous` | `concise, neutral` |
| **Complex Logic** | `concise, step-by-step` | `technical, chain-of-thought` | `detailed, step-by-step` |
| **Agentic Flow** | `autonomous, minimal` | `reliable, plan-first` | `proactive, descriptive` |
| **Code / Data** | `idiomatic, minimal` | `technical, verified` | `detailed, markdown` |

---

## ⚓ How to Anchor a Baseline

In a new conversation or when switching contexts, use a **one-time anchor** to set the ground rules.

**Example 1: Setting a Technical Baseline**
```text
Baseline: Technical, Pythonic, no comments, minimal verbosity.
```

**Example 2: Setting an Agentic Baseline**
```text
Baseline: Autonomous, plan-first, explicit tool use, ask before recommending.
```

Once anchored, you only need to use deltas:
```text
Δ(add error handling)
Δ(use async/await)
```

---

## 💡 Pro-Tips for Baseline Mastery

1.  **Inheritance:** Any dimension not specified in the anchor or Delta defaults to the model’s internal "helpful assistant" prior.
2.  **Context Erosion:** In very long chats, re-anchor your baseline every ~10-15 turns to prevent "instruction drift."
3.  **Specific vs. General:** Start with a **General** baseline and use **Deltas** for specific tasks. Don't try to bake every constraint into the baseline.

---

*This reference sheet is part of the [Delta](README.md)