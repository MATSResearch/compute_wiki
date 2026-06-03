---
tags:
  - interpretability
---

# Probes and Linear Classifiers

Tools for training classifiers on model internals — the workhorse technique for "does the model represent X?" Common uses: lie detection, refusal detection, sentiment, deceptive intent, model-state-of-knowledge.

## At a glance: which probe approach?

| If you want… | Use |
|---|---|
| The 90% case: linear probe on activations | `sklearn.linear_model.LogisticRegression` |
| Contrast Consistent Search (CCS, an unsupervised probe method) | Hand-rolled or `collin-burns/discovering_latent_knowledge` reference repo |
| Larger probing pipeline with caching, multi-layer sweeps | **probity** |
| Probe a 70B+ model | Extract activations once via vLLM-Lens or nnsight remote, then sklearn |

## Linear probes via sklearn (the default)

There is no "library" for this. The pattern is:

```python
import torch
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score

# 1. Extract activations at a chosen layer + position for each example
acts = []  # list of (hidden_size,) tensors
labels = []  # list of 0/1
# ... use TransformerLens / nnsight / baukit to fill these ...

X = torch.stack(acts).float().cpu().numpy()
y = torch.tensor(labels).numpy()

# 2. Train probe with regularization
clf = LogisticRegression(C=0.1, max_iter=1000).fit(X_train, y_train)
print("acc:", accuracy_score(y_test, clf.predict(X_test)))
```

**Why this is the default.** Linear probes are interpretable, fast to fit, and the linear-representation hypothesis predicts that meaningful concepts are linearly readable from residual stream activations. Adding more capacity (MLP probes) usually means you're learning the concept *in the probe*, not finding it in the model.

**When to use it:** Almost always, as a first pass.

**When *not* to use it:** When the question is causal ("does the model *use* this representation?"), not predictive. Use intervention experiments (steering, ablation) for causal claims.

## CCS (Contrast Consistent Search)

Aliases: CCS = Contrast-Consistent Search, "Burns et al. probe", "discovering latent knowledge", `collin-burns/discovering_latent_knowledge` on GitHub, "the unsupervised lie detector" (informally — and contested).

**What it is.** An unsupervised probe method: given contrast pairs (statement + true/false framing), find a direction such that the projections of the two framings sum to ~1 and one is high / one is low. The original 2022 paper claimed this finds "truth" without labels.

**Status (2026-04):** **Both reference repos are abandoned.** `collin-burns/discovering_latent_knowledge` last meaningful commit 2022; `EleutherAI/elk` (the scaled-up CCS reference) last commit Nov 2023. **No actively maintained CCS library exists.** Treat both as archive-quality — install may require pinning old `transformers` versions; reading the code as reference and reimplementing minimally is often the easier path.

**When to use it:** Reproducing CCS as a baseline. Reading the source as a reference.

**When *not* to use it:**
- **Read the followup work first.** CCS has been shown to be sensitive to prompt template, often discovers prominent surface features rather than truth, and frequently underperforms supervised probes (Farquhar et al., "Challenges with Unsupervised LLM Knowledge Discovery").
- **Doing unsupervised probing fresh in 2026:** consider **SAE feature-based approaches** via SAELens / Neuronpedia instead — that's where most 2025–2026 unsupervised concept-discovery work has gone.

**Pitfalls:**
- **CCS results don't replicate consistently across templates / models** — sweep both.
- **Sign ambiguity.** CCS produces a direction; its sign is determined by the loss tiebreaker. Anchor sign to a few labeled examples.
- **"It works on TruthfulQA" doesn't mean it works for novel deception detection.** Held-out distribution shift matters.

## probity

Aliases: `curt-tigges/probity` on GitHub. **Not on PyPI** — install via `uv pip install git+https://github.com/curt-tigges/probity` (or pip equivalent). Last commit April 2025.

**What it is.** A library for systematic linear probing across many layers / positions / models, with caching of activations, paired-prompt dataset construction, token-position handling, and a sklearn-like API.

**Status (2026-04):** Personal research tooling, low-velocity (~12 months since last commit). Maintainer Curt Tigges has shifted toward SAE work; probity is not actively developed but works.

**When to use it:** You want probity's dataset-construction conventions (paired prompts, careful token-position handling) and don't want to roll them yourself. You're doing a non-trivial probing sweep.

**When *not* to use it:** A single experiment — sklearn on cached activations is enough (~30 lines). You expect upstream fixes.

## Hand-rolled probing on extracted activations

For research-scale (≤70B), the typical pipeline:

1. **Decide what to probe.** A specific behavior, concept, or hidden state. Define a labeled dataset (or contrast pairs).
2. **Extract activations once.** Use TransformerLens / nnsight / vLLM-Lens to dump activations for all examples at all layers you might care about. Save to disk (e.g. `.pt` files or zarr) — re-extracting is expensive.
3. **Train probes per layer / position.** Sweep regularization. Plot accuracy vs layer to find the "where" of the representation.
4. **Validate causally.** A high-accuracy probe direction may or may not be *used* by the model. Test by ablating along the direction and seeing if behavior changes.

## Pitfalls (cross-cutting)

- **Probe accuracy ≠ "the model represents X causally."** A probe can pick up correlated features, prompt-format artifacts, or the answer leaking into late layers. Causal validation matters.
- **Class imbalance.** A 90/10 split + 90% accuracy probe means nothing. Always report balanced accuracy or AUROC.
- **Train/test contamination.** Activations from the same prompt in train and test (different formattings, paraphrases) leak. Split at the *concept* level (different topics, different days, different sources), not the prompt level.
- **Position selection bias.** Probing at "the last token" works because most info accumulates there — but that doesn't mean the model "knows" at the last token; it might know earlier and just propagate. Try multiple positions.
- **Layer choice.** Late-layer probes can pick up the model's planned output, which is downstream of the question you actually want to ask ("does the model know X early?"). Probe early layers too.
- **"My probe works on Pythia / GPT-2" — does it on a real model?** Old base models behave differently from RLHF'd 2025 frontier models. Always replicate on your target.
- **Held-out distribution.** A probe trained on AI-generated contrast pairs may not generalize to natural prompts. Test on the actual distribution you care about.
- **Probe regularization.** With activations of dim 4096+ and small datasets, an unregularized linear probe overfits. Use L2 regularization (sklearn's `C` parameter) and tune via CV.
- **Tokenizer / chat-template mismatch.** Activations are position-indexed; if you tokenized with a different template than at inference, your "last token" is the wrong one.

## Probing methods worth knowing (no library, reference)

- **Logistic regression / linear probe.** The default.
- **Mean difference / difference-of-means.** Often as good as logistic regression, simpler, less overfitting.
- **Mass-mean shift.** Direction of class means, normalized. Used in Belrose et al.'s LEACE work.
- **LEACE / Least-squares Concept Erasure.** A probe-based *erasure* method — surgically removes a concept from a representation. `EleutherAI/concept-erasure` on GitHub, `concept-erasure` on PyPI (v0.2.4, Jan 2024). Belrose et al. 2023 (arXiv:2306.03819). Algorithm is closed-form so the slow release cadence is fine — last functional commit Oct 2024; works as-is.
- **Iterative nullspace projection (INLP).** Older erasure method.
- **Probing logit lens / tuned lens.** Reading from intermediate layers via the unembedding (or a learned linear map). `AlignmentResearch/tuned-lens` on GitHub (the canonical maintained location).

## tuned-lens

Aliases: `tuned-lens` on PyPI, **`AlignmentResearch/tuned-lens` on GitHub** (the canonical maintained location — `EleutherAI/tuned-lens` is a stale fork, project moved to FAR AI / AlignmentResearch under Nora Belrose). "the tuned lens".

**What it is.** A learned linear projection from intermediate residual streams to vocab logits — a calibrated version of "logit lens." Useful for visualizing what the model "thinks" at each layer.

**Status (2026-04):** Limping. **PyPI release 0.2.0 is from July 2023** and missing modern model support. `main` branch added Mistral (Aug 2025) and Gemma (June 2024) but **Llama-3, Gemma-2/3, and Qwen-3 are not supported** as of this writing. Install from git, not PyPI, and expect to patch model loading.

**When to use it:** Visualizing layerwise predictions on supported models (GPT-2 family, Pythia, Llama-1/2, Mistral, Gemma-1).

**When *not* to use it:** Llama-3 / Gemma-2/3 / Qwen-3 — tuned lens doesn't support them. Either train your own translator layers (the repo supports this; takes hours on a single GPU) or use **logit lens** as a coarser substitute (just `model.unembed @ residual` — works for any architecture, ~10 lines).

## Cross-references

- Activation extraction (the prerequisite for probing): [`mech-interp.md`](mech-interp.md), [`serving-and-activations.md`](serving-and-activations.md).
- Steering using probe directions: [`steering.md`](steering.md).
- SAE features as a probing target: [`saes.md`](saes.md).
- Probes used as **monitors** inside AI Control protocols: [`ai-control.md`](../oversight-and-control/ai-control.md).
- Probes for valence / mood / introspection states: [`welfare-introspection.md`](../alignment-science/welfare-introspection.md).
- Probes to detect sleeper-agent / alignment-faking model organisms: [`model-organisms.md`](../alignment-science/model-organisms.md).
- Activation-based probe monitors as alternative to CoT-based monitoring: [`cot-faithfulness.md`](../alignment-science/cot-faithfulness.md).

---

## Common questions

### What's the simplest way to train a probe on activations?

Extract activations once, then `sklearn.linear_model.LogisticRegression`:
```python
from sklearn.linear_model import LogisticRegression
clf = LogisticRegression(C=0.1, max_iter=1000).fit(X_train, y_train)
print("acc:", clf.score(X_test, y_test))
```
This is the 90% case. Don't reach for fancier probes unless you have a reason — adding capacity to the probe usually means you're learning the concept *in the probe*, not finding it in the model.

### Why is my probe accuracy suspiciously high?

Probable leakage. Common causes: (1) **train/test split at the prompt level** instead of concept level — different paraphrases of the same idea split across both. Split at the *concept / topic / source* level. (2) **Class imbalance** — a 90/10 split + 90% accuracy probe means nothing; report **balanced accuracy** or **AUROC**. (3) **Late-layer probes** pick up the model's planned output, not its understanding — try earlier layers. (4) **Last-token bias** — most info accumulates there; try multiple positions.

### Linear probe vs MLP probe — which?

**Linear probe** for almost everything. The linear-representation hypothesis predicts meaningful concepts are linearly readable from residual stream activations. An MLP probe with hidden capacity often learns the concept *itself* rather than reading it from the model — which means high accuracy that doesn't reflect the model's representation.

### What is CCS (Contrast Consistent Search)?

CCS = **Contrast Consistent Search** — an unsupervised probe method (Burns et al. 2022) that finds a direction such that the projections of true/false framings of a statement sum to ~1 and one is high / one is low, without requiring labels. **Caveat:** subsequent work (Farquhar et al., "Challenges with Unsupervised LLM Knowledge Discovery") showed CCS is sensitive to prompt template, often discovers prominent surface features rather than truth, and frequently underperforms supervised probes. Validate against supervised baselines.

### What is the tuned lens?

`tuned-lens` (`AlignmentResearch/tuned-lens` on GitHub, formerly EleutherAI) — a learned linear projection from intermediate residual streams to vocab logits. Calibrated version of "logit lens" (which uses the unembedding matrix directly). Useful for visualizing what the model "thinks" at each layer. **Caveat:** PyPI 0.2.0 is from July 2023; install from git for Mistral/Gemma support. **Llama-3, Gemma-2/3, Qwen-3 are not supported** — for those models, use raw logit lens (`model.unembed @ residual`).

### Probes vs steering — what's the difference?

**Probing** is *reading*: train a classifier on activations to detect a property. Predictive — does not establish causation. **Steering** is *writing*: add or modify activations to change behavior. Causal — establishes the direction *can* affect behavior. A probe direction may or may not be one the model actually *uses*; ablation / steering experiments test that. See [`steering.md`](steering.md).

### Does my probe work on the deployed model?

Probes don't always generalize. Common failures: (1) trained on AI-generated contrast pairs, doesn't transfer to natural prompts. (2) trained on Pythia / GPT-2, doesn't transfer to RLHF'd 2025 frontier models. (3) trained on one task domain, doesn't transfer to another. Always test on the actual distribution you care about.

---

Last verified: 2026-04-30. probity not on PyPI (install from git, last commit April 2025). CCS reference (`collin-burns/discovering_latent_knowledge`) and EleutherAI's `elk` both abandoned. tuned-lens moved to `AlignmentResearch/tuned-lens` (FAR AI); PyPI 0.2.0 is from 2023, install from git for Mistral/Gemma; Llama-3/Gemma-2/Qwen-3 not supported. concept-erasure (LEACE) v0.2.4, works as-is.
