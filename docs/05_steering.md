# Activation Steering and Representation Engineering

Tools for modifying model behavior at inference time by intervening on internal activations — adding "steering vectors," ablating directions, or applying SAE-feature edits. Closely related: **representation engineering** (RepE), **Contrastive Activation Addition** (CAA), **ActAdd**, **LAT** (Latent Adversarial Training, separate from steering but uses similar primitives), **conditioned activation steering** (Bayat et al.), **feature steering** (SAE-based).

## At a glance: which steering tool?

| If you want… | Use |
|---|---|
| Compute and apply CAA (Contrastive Activation Addition) steering vectors | **steering-vectors** library |
| Modular toolkit: contrast pair construction + steering + visualization | **Dialz** |
| Representation engineering / RepE / LAT-style direction finding | **representation-engineering** (Andy Zou) |
| Apply steering at vLLM throughput on a 70B model | **vLLM-Lens** (see [`07_serving_and_activations.md`](07_serving_and_activations.md)) |
| SAE feature steering (turn feature N up/down) | **SAELens** + custom hooks (see [`02_saes.md`](02_saes.md)) |
| Pure ablation / direction removal (refusal direction, etc.) | hand-rolled, or `repe` / `steering-vectors` |
| Refusal-direction "abliteration" specifically | `andyrdt/refusal_direction` (canonical) or active forks (`Orion-zhen/abliteration`); avoid stale `FailSpy/abliterator` |

## steering-vectors

Aliases: `steering-vectors` on PyPI (v0.12.2, Feb 2025), `steering-vectors/steering-vectors` on GitHub. Authors: **David Chanin (`chanind`) and Daniel Tan (`dtch1997`)** per PyPI metadata. The library implements the CAA method from **Panickssery et al. 2023** (which is the paper, not the library author).

**What it is.** A clean PyTorch/HuggingFace library for **Contrastive Activation Addition (CAA)** — compute the difference of mean activations between two sets of contrastive prompts, then add that vector at inference time to steer behavior. Implements the method from Panickssery et al.'s "Steering Llama 2 via Contrastive Activation Addition" (Dec 2023).

**Status (2026-04):** Stable but slow — last commit Feb 2025 (~14 months stale). Not abandoned (issues responded to) but no recent additions. Still the cleanest pure-PyTorch CAA library; works fine on Llama / Gemma / Qwen-class HF models.

**When to use it:**
- The classic CAA workflow: build pairs of (positive behavior, negative behavior) prompts, compute steering vector, apply.
- You want a small, focused library that does one thing well.
- Reproducing CAA-style results.

**When *not* to use it:**
- You want a full toolkit including dataset construction, visualizations, multiple steering methods — Dialz is more comprehensive.
- You need vLLM-scale throughput — apply the same vectors via vLLM-Lens instead.

**Pitfalls:**
- **Position selection.** CAA vectors are usually averaged over the last token of the answer prefix or specific token positions. Wrong positions = garbage vectors. Read the library's defaults and override consciously.
- **Layer choice.** Steering at layer ~half-depth is the typical sweet spot for behavioral steering; very early layers do little, very late layers don't propagate. Sweep.
- **Magnitude is dataset-dependent.** A magnitude that works on Llama-2-7B doesn't transfer to Gemma. Sweep magnitudes per (model, behavior).

```python
# pip install steering-vectors
from steering_vectors import train_steering_vector, SteeringVector
sv = train_steering_vector(model, tokenizer, training_pairs, layers=[15])
with sv.apply(model, multiplier=1.0):
    output = model.generate(...)
```

## Dialz

Aliases: `dialz` on PyPI (v1.1.4, July 2025), `cardiffnlp/dialz` on GitHub (Cardiff NLP), arXiv:2505.06262 (Dialz: A Python Toolkit for Steering Vectors). Author: Zara Siddique (`groovychoons`, Cardiff University).

**What it is.** A 2025 toolkit that bundles **contrast-pair dataset construction**, multiple steering-vector methods, application, **per-token steering indices**, and **visualizations**. Aimed at being a more complete workflow library than steering-vectors.

**Status (2026-04):** **More active than `steering-vectors`** — last commit March 2026, ongoing feature work (steering-token-index, dtype control). Post-1.0.

**When to use it:** You want batteries-included experimentation — dataset utilities + multiple steering-vector methods + visualizations + per-token control. The richer workflow story.

**When *not* to use it:** You want minimal dependencies / want to roll the steps yourself — start with `steering-vectors` for the bare-bones primitive.

## representation-engineering (RepE)

Aliases: `repe` on PyPI (v0.1.4), **`andyzoujm/representation-engineering` on GitHub** (the canonical URL — earlier docs sometimes wrote `andyzou-jiaming/...`, that's the same author but the canonical handle is `andyzoujm`), "RepE", "Andy Zou's RepE library", "the LAT library". **RepE = Representation Engineering. LAT = Linear Artificial Tomography** (the RepE direction-finding method, *not* Latent Adversarial Training, which is unrelated).

**What it is.** Implements the methods from "Representation Engineering: A Top-Down Approach to AI Transparency" (Zou et al. 2023, arXiv:2310.01405). Provides:
- **LAT scanning** for finding behavior-relevant directions.
- **Reading vectors** vs **control vectors** distinction.
- Behavior steering, honesty / harmfulness probing.

**Status (2026-04):** **Reference implementation, effectively frozen** — last commit August 2024 (~20 months stale). The methods are still cited as baselines in 2026 papers but for new steering work, prefer `steering-vectors` or `dialz`.

**When to use it:**
- Reproducing RepE-paper-style direction finding (PCA on contrastive activations, "honesty direction," etc.).
- Reading the source as a reference for LAT.

**When *not* to use it:** New projects — use `steering-vectors` (CAA primitive) or `dialz` (full workflow) instead.

**Pitfalls:**
- **PCA vs mean-difference can give very different vectors.** RepE supports both; report which.
- **Direction sign ambiguity.** PCA-based directions can flip sign across runs. Anchor to a labeled probe to fix sign.

### repeng (lighter-weight alternative)

Aliases: `repeng` on PyPI (v0.4.0), `vgel/repeng`, "Theia Vogel's RepE library".

A lighter-weight independent library inspired by RepE methods, with **`llama.cpp` GGUF export** for quantized inference. Useful when you want to apply control vectors against quantized / locally-served models. Distinct from `andyzoujm/representation-engineering`.

## Refusal-direction abliteration

Aliases: "abliteration", "Arditi et al. refusal direction", "refusal direction is a single direction".

**What it is.** A specific application: find the "refusal direction" via mean-difference of activations on harmful vs harmless prompts (Arditi et al. 2024, "Refusal in Language Models Is Mediated by a Single Direction"), then *project it out* of the model's weights or activations to prevent refusals. There are public uncensored model checkpoints created this way ("abliterated" models).

**Which repo?**
- **`andyrdt/refusal_direction`** — **the canonical paper repo** for Arditi et al. 2024. Last commit June 2025. Use this as the authoritative reference.
- **`FailSpy/abliterator`** — popular early implementation; **last commit June 2024 (stale, 17 unresolved issues)**. Educational / historical only; do not start new work from it.
- **`Orion-zhen/abliteration`** — active fork (Dec 2025), transformers-native (no TransformerLens dependency), good for actually producing abliterated checkpoints.
- **`wassname/abliterator`** — uses baukit instead of TransformerLens, active early 2026; useful when TransformerLens architecture support is the bottleneck.
- **`jwest33/abliterator`** — active March 2026, adds null-space projection and winsorization variants.

**When to use it:**
- Studying refusal mechanisms.
- Reproducing the Arditi et al. result (use `andyrdt/refusal_direction`).
- Generating a refusal-removed checkpoint for downstream research (use `Orion-zhen/abliteration` for a smooth transformers-native path).

**When *not* to use it:**
- Production / public deployment — abliterated models are openly more harmful. Treat outputs accordingly.
- General-purpose steering — the technique is narrowly focused.

**Pitfalls:**
- **Model degradation.** Aggressive ablation hurts general capability. Check standard benchmarks after.
- **Provider ToS.** Distributing abliterated derivatives of license-restricted models has legal complexity.
- **Don't start from `FailSpy/abliterator`** — it's been overtaken by both the canonical paper repo and several active forks.

## SAE feature steering

Not a separate library — implemented via SAELens (see [`02_saes.md`](02_saes.md)) plus custom hooks. Pattern:
1. Identify a feature `f` that activates on the behavior you want to control (Neuronpedia is good for browsing).
2. At inference, encode the residual stream into SAE features, modify feature `f` (clamp, scale, ablate), decode back.
3. Continue the forward pass with the modified residual.

**Pitfalls:**
- **Reconstruction error compounds.** Every time you encode→decode, you lose some of the residual. Use error terms to add the unreconstructed component back.
- **Feature splitting.** "The deception feature" in a 16k-width SAE may be 5 features in a 65k-width SAE. Steering the wrong one of the 5 may do nothing.
- **Off-target effects.** Clamping a feature on can knock out language modeling. Always check perplexity / sample text afterward.

## vLLM-Lens for production-scale steering

Aliases: `vllm-lens`, `UKGovernmentBEIS/vllm-lens` on GitHub.

For applying steering vectors during high-throughput inference (millions of samples, tensor-parallel 70B models), vLLM-Lens is the right tool. See [`07_serving_and_activations.md`](07_serving_and_activations.md) for full details. Quick summary: pass steering vectors via `GenerateConfig.extra_body` when calling the vLLM-Lens-served model from Inspect or directly via the OpenAI-compatible API.

## Cross-cutting steering pitfalls

- **Steering effects don't always generalize.** A vector that flips refusal on a held-out test set may not produce the underlying *behavior* — only the surface refusal. Always check on out-of-distribution cases.
- **"Is this steering or just noise?"** With small contrast sets, mean-difference vectors are noisy. Use ≥100 pairs per side; check via random-split control: do random "positive/negative" splits give nontrivial steering effects? If yes, your real steering effect may be artifactual.
- **Magnitude search burns budget.** Steering generally requires sweeping `multiplier` in [-5, +5]-ish; budget for it.
- **Eval-aware models.** Models that have learned to detect being evaluated may behave differently with/without obvious "evaluator" prompts. Steering may or may not interact with this — see Steering Evaluation-Aware Language Models (arXiv 2510.20487) for a recent example.
- **Layer-by-layer effects compound.** Steering at multiple layers simultaneously is non-linear; a vector that works at layer 15 alone may behave differently when combined with a layer-20 vector.
- **CAA = Contrastive Activation Addition.** Spelled out for keyword search: this is the same thing as "the steering vectors library" approach. RepE = Representation Engineering. ActAdd = Activation Addition (the GPT-2 era pre-CAA technique).

## Cross-references

- Underlying interp libraries: [`01_mech_interp.md`](01_mech_interp.md).
- SAEs (for feature steering): [`02_saes.md`](02_saes.md).
- Probes (for finding directions in the first place): [`06_probes.md`](06_probes.md).
- vLLM-Lens for scale: [`07_serving_and_activations.md`](07_serving_and_activations.md).

---

## Common questions

### How do I make a steering vector?

The Contrastive Activation Addition (CAA) recipe: (1) build pairs of contrastive prompts — positive examples of the behavior, negative examples; (2) run the model on each, capture residual-stream activations at a specific layer + token position; (3) take the mean difference of activations. That's your steering vector. Apply by adding it (scaled) to the residual stream during generation. The `steering-vectors` library implements this end-to-end.

### Why doesn't my steering vector work?

Most common causes: (1) **wrong layer** — try the middle layers (~half-depth) first; very early or very late layers usually don't propagate behaviorally. (2) **wrong magnitude** — sweep multiplier in [-5, +5]; the right value is dataset- and model-dependent. (3) **wrong token position** — average over the last token of the answer prefix or specific positions, not arbitrary positions. (4) **too few contrast pairs** — use ≥100 per side; with fewer, the vector is dominated by noise.

### What is CAA (Contrastive Activation Addition)?

CAA = **Contrastive Activation Addition** — the dominant method for activation steering in 2024–2026. Computes a steering vector by averaging the difference of residual-stream activations between matched contrastive prompt pairs (e.g. sycophantic vs non-sycophantic answers), then adds the vector during inference to dial the trait up or down. Originated: Panickssery et al. 2023, "Steering Llama 2 via Contrastive Activation Addition."

### Can I apply steering at vLLM scale (production throughput)?

Yes — use **vLLM-Lens** (UK AISI). Pass steering vectors via `GenerateConfig.extra_body` when calling the vLLM-Lens-served model from Inspect AI or directly via the OpenAI-compatible API. ~20% slower than vanilla vLLM, dramatically faster than nnsight or TransformerLens for the same task. See [`07_serving_and_activations.md`](07_serving_and_activations.md).

### Does activation steering generalize?

Often less than you'd hope. A vector that flips refusal on a held-out test set may not produce the underlying *behavior change* — only the surface refusal token. Always test on out-of-distribution prompts. With small contrast sets, mean-difference vectors are noisy — run a control: do random "positive/negative" splits give nontrivial steering effects? If yes, your real steering effect may be partly artifactual.

### Steering vs SAE feature steering — which?

**CAA-style steering vectors** are simpler, work with no SAE, and apply broadly. **SAE feature steering** (clamp / scale / ablate one SAE feature) is more targeted but only as good as the SAE — you may find a feature is "split" across multiple SAE latents. For first-pass experiments use CAA; for fine-grained intervention with mechanistic claims, SAE features. See [`02_saes.md`](02_saes.md).

### What is the refusal direction / abliteration?

**Refusal direction**: a direction in activation space found via mean-difference of activations on harmful vs harmless prompts (Arditi et al. 2024, "Refusal in Language Models Is Mediated by a Single Direction"). **Abliteration**: projecting that direction out of the model's weights, producing an uncensored "abliterated" checkpoint. Useful for refusal-mechanism research; not recommended for deployment.

**Which repo?** Use **`andyrdt/refusal_direction`** for the canonical Arditi-paper reproduction, or **`Orion-zhen/abliteration`** for a transformers-native modern implementation. **Avoid `FailSpy/abliterator`** — last commit June 2024, stale; the early popularity is no longer matched by maintenance.

---

Last verified: 2026-04-30. `steering-vectors` v0.12.2 (Feb 2025, slow but stable; authors David Chanin and Daniel Tan). `dialz` v1.1.4 (cardiffnlp/dialz, Cardiff NLP, more active than steering-vectors as of April 2026). RepE (`andyzoujm/representation-engineering`) frozen since Aug 2024 — still cited as baseline; new work should use steering-vectors or dialz. `repeng` (vgel) is a separate lighter-weight library with GGUF export. Refusal direction: `andyrdt/refusal_direction` is canonical (June 2025); `FailSpy/abliterator` is stale.
