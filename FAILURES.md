# Delta — Failure Case Studies

Short, illustrative case studies for the failure modes in [README.md](README.md).
Each follows the same shape: **symptom → cause → fix**. They are teaching
examples, not empirical measurements.

---

## 1. Ambiguous output (baseline mismatch)

**Symptom:** `Δ(summarize | brief)` returns a 500-word summary with an
introduction and conclusion. The user expected three bullet points.

**Cause:** "Brief" was never anchored. The model's default summarizer prior
(long-form, structured article) filled the gap — there was no shared baseline,
so the delta had nothing to deviate *from*.

**Fix:** anchor once, then delta:

```text
Baseline: concise, neutral, factual.
Δ(summarize report | bullet points, <150 words)
```

**Rule:** if the output shape surprises you, the baseline was implicit. Make it explicit.

---

## 2. Missing constraint (over-compression)

**Symptom:** `Δ(implement search | fast)` returns a correct but
quadratic implementation with a paragraph of explanation the caller didn't want.

**Cause:** "Fast" compresses two independent constraints (time complexity and
output verbosity) into one vague word. Over-compression shifts interpretation
work onto the model.

**Fix:** one constraint per delta, stated measurably:

```text
Baseline: idiomatic Python, correct by default.
Δ(implement search | O(log n), no comments, include tests)
```

**Rule:** compress the *obvious*, never the *load-bearing*. Anything that
changes correctness or cost gets its own explicit delta.

---

## 3. Drift and contradiction (context erosion)

**Symptom:** a long session starts with `Δ(formal tone)`, and twenty turns
later adds `Δ(sound casual and friendly)`. Output oscillates — stiff openings
with slang closings.

**Cause:** deltas append; they never expire. Two contradictory deltas are both
"active", and recency decides each token. In long chats the original anchor
also erodes from the context window.

**Fix:** prefer replace over append for direction changes, and re-anchor
every ~10–15 turns:

```bash
dp set "concise, casual, technical" "Rewrite the onboarding email."
dp run
```

**Rule:** deltas are a stack, not a set — `dp set` (replace) for pivots,
`-a` (append) only for refinements. When in doubt, re-anchor.

---

*Contribute yours: real-world failure reports are the most valuable addition
to this file. Open an issue or PR.*
