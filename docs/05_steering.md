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
| Refusal-direction "abliteration" specifically | `FailSpy/abliterator` and forks |

## steering-vectors

Aliases: `steering-vectors` on PyPI, `steering-vectors/steering-vectors` on GitHub, "Nina Panickssery's CAA library", "the CAA library".

**What it is.** A clean PyTorch/HuggingFace library for **Contrastive Activation Addition (CAA)** — compute the difference of mean activations between two sets of contrastive prompts, then add that vector at inference time to steer behavior. Originated from Panickssery et al.'s "Steering Llama 2 via Contrastive Activation Addition" (Dec 2023, updated 2026).

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

Aliases: `dialz` on PyPI (verify availability), arXiv:2505.06262 (Dialz: A Python Toolkit for Steering Vectors).

**What it is.** A 2025 toolkit that bundles contrast-pair dataset construction, multiple steering-vector methods, application, and visualizations. Aimed at being a more complete workflow library than steering-vectors.

**When to use it:** You want one library covering the full CAA workflow with visualizations.

**When *not* to use it:** You want minimal dependencies / understand each step yourself — start with steering-vectors.

**Pitfall:** Newer library, smaller user base than steering-vectors. Check active issues before depending on it for a major project.

## representation-engineering (RepE)

Aliases: `representation-engineering` on PyPI, `andyzou-jiaming/representation-engineering` on GitHub, "RepE", "Andy Zou's RepE library", "the LAT library" (note: LAT in this context = Linear Artificial Tomography, the RepE method, not Latent Adversarial Training).

**What it is.** Implements the methods from "Representation Engineering: A Top-Down Approach to AI Transparency" (Zou et al. 2023). Provides:
- **LAT scanning** for finding behavior-relevant directions.
- **Reading vectors** vs **control vectors** distinction.
- Behavior steering, honesty / harmfulness probing.

**When to use it:**
- RepE-paper-style direction finding: PCA on contrastive activations, "honesty direction," etc.
- You want both probing (read) and steering (write) in one library.

**When *not* to use it:** You only want CAA-flavored mean-difference steering — steering-vectors is simpler.

**Pitfalls:**
- **PCA vs mean-difference can give very different vectors.** RepE supports both; report which.
- **Direction sign ambiguity.** PCA-based directions can flip sign across runs. Anchor to a labeled probe to fix sign.

## Refusal-direction abliteration

Aliases: "abliteration", `FailSpy/abliterator`, "Arditi et al. refusal direction".

**What it is.** A specific application: find the "refusal direction" via mean-difference of activations on harmful vs harmless prompts (Arditi et al. 2024), then *project it out* of the model's weights or activations to prevent refusals. There are public uncensored model checkpoints created this way ("abliterated" models).

**When to use it:**
- Studying refusal mechanisms.
- Reproducing the Arditi et al. result.
- Generating a refusal-removed checkpoint for downstream research.

**When *not* to use it:**
- Production / public deployment — abliterated models are openly more harmful. Treat outputs accordingly.
- General-purpose steering — the technique is narrowly focused.

**Pitfalls:**
- **Model degradation.** Aggressive ablation hurts general capability. Check standard benchmarks after.
- **Provider ToS.** Distributing abliterated derivatives of license-restricted models has legal complexity.

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

Last verified: 2026-04. CAA library `steering-vectors` 0.12.x. Dialz published May 2025. RepE library still maintained by Andy Zou.
