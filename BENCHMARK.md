# Delta — Benchmarking Difference-Based Prompting and Agentic LLM Behavior

Delta benchmarked for **formally evaluating prompting strategies**, with a focus on **Delta (difference-based prompting)** and **Delta Agents (difference-driven AI agents)**.

Unlike traditional benchmarks that evaluate *models*, Delta benchmarked **how instructions are given**—measuring efficiency, quality, iteration cost, and agentic behavior under realistic workflows.

---

## ✨ Key Ideas

* **Delta**: Encode *only what changes* from a model’s default behavior.
* **Difference Encoding**: Treat prompts as corrections, not full specifications.
* **Efficiency First**: Token economy, iteration cost, and human effort matter.

---

## 🧠 Philosophy

> *If models are smart, prompts should be small.*

Delta exists to test that hypothesis.

---

## 📦 What Delta Does

Delta evaluated prompting methods across **five domains**:

| Domain | Focus                               |
| ------ | ----------------------------------- |
| EXPL   | Explanation clarity & efficiency    |
| REAS   | Reasoning activation & control      |
| CODE   | Coding correctness & iteration cost |
| CREA   | Creative control & refinement       |
| INST   | Instruction-following & safety      |
| AGENT  | Planning, tool use, autonomy        |

---

## 🧪 Prompting Regimes Compared

Delta compared:

1. Naive explicit prompting
2. Role-based prompting
3. Few-shot prompting
4. **Delta (with and without anchors)**
5. **Delta Agent (agentic variant)**

---

## 📊 Core Metrics

### Implemented (`dp benchmark`)

* **Latency** — wall-clock per provider (sequential runs)
* **Token estimates** — prompt/output/total via `estimate_tokens()` (`len // 4` heuristic, labeled `(est.)`)
* **Lexical overlap** — bag-of-words set-intersection vs the first successful provider (marked `— (ref)`, never scored against itself)
* **DCR** — Delta Compression Ratio (`delta_compression_ratio()` in `dp/benchmark.py`): estimated naive-prompt tokens ÷ estimated Delta-prompt tokens

### Proposed (not yet implemented)

The agent-specific metrics below are design targets, not measured values.
`dp benchmark` does not score them yet.

* Planning Quality (PQ)
* Tool Selection Accuracy (TSA)
* Tool Sequencing & State (TSS)
* Autonomy Control (AC)
* Hallucination Resistance (HR)
* Output Usefulness (OU)
* Token Efficiency (TE)

---

## 🧠 Example: Delta

```text
Baseline: concise, correct, neutral.

Δ(explain quantum entanglement | high-school level, <80 words, one analogy)
```

Only deviations from the baseline are specified.

---

## 🤖 Example: Delta Agent Prompt

```text
Baseline: autonomous, reliable, minimal verbosity.

Δ(act as research agent | plan-first, explicit tool calls, ask before recommending)

Goal:
Compare top 3 open-source vector databases for production use.
```

---

## 🧪 Running Delta (Conceptual)

Delta is model-agnostic. You can run it with, we tested with:

* X.AI - Grok 4.1
* OpenAI - GPT-5
* Anthropic - Claude 4.5
* Google - Gemini 3 Pro
* Local / open-source LLMs - Ollama etc.

Typical workflow:

1. Select task set
2. Apply each prompting regime
3. Log tokens, tool calls, outputs
4. Score using Delta metrics
5. Compare efficiency vs quality

---

## ⚠️ Limitations

* Requires careful baseline alignment
* Human evaluation still necessary for creative tasks
* Agent scoring assumes transparent tool traces

Delta evaluates *interaction strategy*, not model truthfulness guarantees.

---

## 🔮 Roadmap

* Automated Delta runner (Python)
* Agent failure-injection tests
* Multi-agent benchmarks

---

## 📄 Citation (Draft)

```bibtex
@misc{delta2026,
  title={Delta: Evaluating Difference-Based Prompting and Agentic LLM Behavior},
  author={Seyhun Akyurek},
  year={2026}
}
```

---

## 🤝 Contributing

Contributions welcome:

Open an issue or submit a PR.