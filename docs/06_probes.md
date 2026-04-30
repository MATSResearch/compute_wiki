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

Aliases: CCS = Contrast Consistent Search, "Burns et al. probe", "discovering latent knowledge", `collin-burns/discovering_latent_knowledge` on GitHub, "the unsupervised lie detector" (informally — and contested).

**What it is.** An unsupervised probe method: given contrast pairs (statement + true/false framing), find a direction such that the projections of the two framings sum to ~1 and one is high / one is low. The original 2022 paper claimed this finds "truth" without labels.

**When to use it:** Probing for binary properties when you have natural contrast pairs but not labels.

**When *not* to use it:** **Read the followup work first.** CCS has been shown to be sensitive to prompt template, often discovers prominent surface features rather than truth, and frequently underperforms supervised probes (Farquhar et al., "Challenges with Unsupervised LLM Knowledge Discovery"). Treat CCS results with skepticism and validate against supervised baselines.

**Pitfalls:**
- **CCS results don't replicate consistently across templates / models** — sweep both.
- **Sign ambiguity.** CCS produces a direction; its sign is determined by the loss tiebreaker. Anchor sign to a few labeled examples.
- **"It works on TruthfulQA" doesn't mean it works for novel deception detection.** Held-out distribution shift matters.

## probity

Aliases: `probity` on PyPI (verify availability), `curt-tigges/probity` on GitHub.

**What it is.** A library for systematic linear probing across many layers / positions / models, with caching of activations and standard sklearn-like API.

**When to use it:** You're doing probing as a major project component (sweeping layers × positions × probe types) and want infrastructure rather than a one-off script.

**When *not* to use it:** A single experiment — sklearn is enough.

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
- **LEACE / LEAst-squares Concept Erasure.** A probe-based *erasure* method — surgically removes a concept from a representation. `EleutherAI/concept-erasure` on GitHub.
- **Iterative nullspace projection (INLP).** Older erasure method.
- **Probing logit lens / tuned lens.** Reading from intermediate layers via the unembedding (or a learned linear map). `EleutherAI/tuned-lens` on GitHub.

## tuned-lens

Aliases: `tuned-lens` on PyPI, `EleutherAI/tuned-lens`, "the tuned lens".

**What it is.** A learned linear projection from intermediate residual streams to vocab logits — a calibrated version of "logit lens." Useful for visualizing what the model "thinks" at each layer.

**When to use it:** Visualizing layerwise predictions, layer-by-layer prompt analysis.

**When *not* to use it:** The model isn't supported, or you want raw logit lens (just `model.unembed @ residual`).

## Cross-references

- Activation extraction (the prerequisite for probing): [`01_mech_interp.md`](01_mech_interp.md), [`07_serving_and_activations.md`](07_serving_and_activations.md).
- Steering using probe directions: [`05_steering.md`](05_steering.md).
- SAE features as a probing target: [`02_saes.md`](02_saes.md).
- Probes used as **monitors** inside AI Control protocols: [`13_ai_control.md`](13_ai_control.md).
- Probes for valence / mood / introspection states: [`15_welfare_introspection.md`](15_welfare_introspection.md).
- Probes to detect sleeper-agent / alignment-faking model organisms: [`16_model_organisms.md`](16_model_organisms.md).
- Activation-based probe monitors as alternative to CoT-based monitoring: [`17_cot_faithfulness.md`](17_cot_faithfulness.md).

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

`tuned-lens` (EleutherAI) — a learned linear projection from intermediate residual streams to vocab logits. Calibrated version of "logit lens" (which uses the unembedding matrix directly). Useful for visualizing what the model "thinks" at each layer. `pip install tuned-lens`.

### Probes vs steering — what's the difference?

**Probing** is *reading*: train a classifier on activations to detect a property. Predictive — does not establish causation. **Steering** is *writing*: add or modify activations to change behavior. Causal — establishes the direction *can* affect behavior. A probe direction may or may not be one the model actually *uses*; ablation / steering experiments test that. See [`05_steering.md`](05_steering.md).

### Does my probe work on the deployed model?

Probes don't always generalize. Common failures: (1) trained on AI-generated contrast pairs, doesn't transfer to natural prompts. (2) trained on Pythia / GPT-2, doesn't transfer to RLHF'd 2025 frontier models. (3) trained on one task domain, doesn't transfer to another. Always test on the actual distribution you care about.

---

Last verified: 2026-04. CCS reference impl unchanged since 2022; probity active. tuned-lens maintained by EleutherAI.
